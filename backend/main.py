import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

from logger import get_logger
from models import DraftRequest, SuggestResponse, HeroSuggestion
import scoring

log = get_logger("dota-api.main")

# Rate Limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

app = FastAPI(
    title="Dota 2 Drafter API",
    version="2.0",
    docs_url="/docs",
    redoc_url=None
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Security Headers & Prometheus Telemetry Middleware
REQUEST_COUNT = Counter(
    "dota_api_requests_total",
    "Total HTTP request count",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "dota_request_latency_seconds",
    "Request latency in seconds",
    ["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)

HERO_COUNT = Gauge("dota_loaded_heroes_total", "Number of loaded heroes in model")
ACTIVE_ENGINE = Gauge("dota_active_prediction_engine", "Prediction engine: 1 for ML, 0 for heuristic")
MODEL_LOAD_TIME = Gauge("dota_model_load_timestamp_seconds", "Timestamp when models were last loaded")

@app.middleware("http")
async def security_and_telemetry_middleware(request: Request, call_next):
    endpoint = request.url.path
    if endpoint == "/metrics":
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    start_time = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response
    finally:
        latency = time.perf_counter() - start_time
        REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status=status_code).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency)

# Standard JSON Error Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join([str(l) for l in err.get("loc", []) if l != "body"])
        msg = err.get("msg", "Validation error")
        errors.append(f"{loc}: {msg}" if loc else msg)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error_type": "ValidationError",
            "message": "Invalid draft parameters provided.",
            "details": errors
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error_type": "HTTPException",
            "message": str(exc.detail),
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    log.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error_type": "InternalServerError",
            "message": "An unexpected server error occurred. Please contact system administrator."
        }
    )

@app.get("/metrics")
def metrics():
    HERO_COUNT.set(len(scoring.hero_map))
    ACTIVE_ENGINE.set(1 if scoring.settings.PREDICTION_ENGINE == "ml" else 0)
    if scoring.model_metadata.get("loaded_at"):
        try:
            dt = datetime.fromisoformat(scoring.model_metadata["loaded_at"])
            MODEL_LOAD_TIME.set(dt.timestamp())
        except Exception:
            pass
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.on_event("startup")
def startup_event():
    import os
    token = os.environ.get("TELEGRAM_TOKEN")
    if token:
        try:
            from bot_service import start_bot_thread
            start_bot_thread(token)
            log.info("Telegram supervisor bot started in background!")
        except Exception as e:
            log.warning(f"Could not start Telegram bot: {e}")

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Dota 2 Drafter API",
        "version": "2.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health():
    ready = scoring.model_metadata["status"] == "ready"
    return {"status": "ok" if ready else scoring.model_metadata["status"], "heroes": len(scoring.hero_map)}

@app.get("/model/status")
def model_status():
    return scoring.model_metadata

@app.post("/model/reload")
def model_reload():
    success = scoring.load_models()
    if success:
        return {"status": "success", "metadata": scoring.model_metadata}
    else:
        raise HTTPException(500, detail="Failed to reload model files from disk.")

@app.get("/debug")
def debug():
    return {
        "hero_map_sample":     {k: scoring.hero_map[k] for k in list(scoring.hero_map)[:20]},
        "avg_matchup_sample":  {scoring.hero_map.get(k, k): round(v, 4)
                                for k, v in list(scoring.hero_avg_matchup.items())[:10]},
        "total_heroes":        len(scoring.hero_map),
        "total_matchup_pairs": len(scoring.matchup_matrix),
        "total_synergy_pairs": len(scoring.synergy_matrix),
    }

@app.get("/heroes")
def heroes():
    return scoring.hero_map

@app.post("/suggest", response_model=SuggestResponse)
@limiter.limit("60/minute")
def suggest(request: Request, req: DraftRequest):
    if not scoring.hero_map:
        raise HTTPException(503, "Model not loaded yet — pkl files missing")

    enemy_ids = scoring.resolve(req.enemy)
    ally_ids  = scoring.resolve(req.team)
    selected  = set(enemy_ids + ally_ids)

    scored = []
    engine = scoring.settings.PREDICTION_ENGINE
    
    for hero_id in scoring.hero_map:
        if hero_id in selected:
            continue
            
        score = scoring.predict(hero_id, enemy_ids, ally_ids, engine=engine)
        scored.append((hero_id, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    picks = []
    for hero_id, score in scored[:9]:
        picks.append(HeroSuggestion(
            id      = hero_id,
            name    = scoring.id_to_name[hero_id],
            score   = round(score, 4),
            reasons = scoring.build_reasons(hero_id, enemy_ids, req.enemy, ally_ids, req.team),
            roles   = scoring.get_roles(hero_id),
        ))

    return SuggestResponse(picks=picks)
