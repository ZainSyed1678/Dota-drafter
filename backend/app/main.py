import time
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address
    has_limiter = True
except ImportError:
    class DummyLimiter:
        def limit(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator
    Limiter = DummyLimiter
    _rate_limit_exceeded_handler = None
    RateLimitExceeded = Exception
    def get_remote_address(req):
        return "127.0.0.1"
    has_limiter = False

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from app.config import settings
from app.logger import get_logger
from app.model_loader import store
from app.routes.draft import router as draft_router
from app.routes.health import router as health_router
from app.routes.heroes import router as heroes_router

log = get_logger("dota-api.main")

if has_limiter:
    limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])
else:
    limiter = DummyLimiter()

app = FastAPI(
    title="Dota 2 Drafter API",
    version=store.metadata.get("version", "2.2.0"),
    docs_url="/docs",
    redoc_url=None
)

app.state.limiter = limiter
if has_limiter:
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Prometheus Telemetry Metrics
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
ACTIVE_ENGINE = Gauge("dota_active_prediction_engine", "Prediction engine: 1 for ML/combined, 0 for heuristic")
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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join([str(part) for part in err.get("loc", []) if part != "body"])
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
    HERO_COUNT.set(len(store.hero_map))
    ACTIVE_ENGINE.set(1 if settings.PREDICTION_ENGINE in ["combined", "ml"] else 0)
    if store.metadata.get("loaded_at"):
        try:
            dt = datetime.fromisoformat(store.metadata["loaded_at"])
            MODEL_LOAD_TIME.set(dt.timestamp())
        except Exception:
            pass
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.on_event("startup")
def startup_event():
    token = settings.TELEGRAM_TOKEN
    if token:
        try:
            from bot_service import start_bot_thread
            start_bot_thread(token)
            log.info("Telegram supervisor bot started in background")
        except Exception as e:
            log.warning(f"Could not start Telegram bot: {e}")


# Include Routers
app.include_router(health_router)
app.include_router(heroes_router)
app.include_router(draft_router)
