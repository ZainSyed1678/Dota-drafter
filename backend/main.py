from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.cache_service import (
    cache_service
)

from repositories.hero_repository import hero_repository
from services.recommendation_engine import engine
from time import perf_counter

from prometheus_client import generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from fastapi import Response

from services.metrics import (
    REQUEST_COUNT,
    CACHE_HITS,
    CACHE_MISSES,
    SUGGEST_LATENCY
)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# ─────────────────────────────────────────────────────────────
# Shared references
# ─────────────────────────────────────────────────────────────

hero_map = hero_repository.get_hero_map()


# ─────────────────────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────────────────────

class DraftRequest(BaseModel):
    enemy: list[str]
    team: list[str]


class HeroSuggestion(BaseModel):
    id: int
    name: str
    score: float
    reasons: list[str]
    roles: list[str]


class SuggestResponse(BaseModel):
    picks: list[HeroSuggestion]


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "heroes": len(hero_map)
    }


@app.get("/debug")
def debug():

    stats = hero_repository.stats()

    return {
        "hero_map_sample": {
            k: hero_map[k]
            for k in list(hero_map)[:20]
        },
        **stats
    }


@app.post(
    "/suggest",
    response_model=SuggestResponse
)
def suggest(req: DraftRequest):

    REQUEST_COUNT.inc()

    start = perf_counter()

    cache_key = (
        f"enemy:{','.join(sorted(req.enemy))}"
        f"|team:{','.join(sorted(req.team))}"
    )

    cached = cache_service.get(
        cache_key
    )

    # ─────────────────────────────
    # Cache Hit
    # ─────────────────────────────
    if cached:

        CACHE_HITS.inc()

        print(
            f"REDIS HIT: {cache_key}"
        )

        SUGGEST_LATENCY.observe(
            perf_counter() - start
        )

        return SuggestResponse(
            picks=[
                HeroSuggestion(**pick)
                for pick in cached
            ]
        )

    # ─────────────────────────────
    # Cache Miss
    # ─────────────────────────────
    CACHE_MISSES.inc()

    print(
        f"REDIS MISS: {cache_key}"
    )

    picks = engine.suggest(
        enemy_names=req.enemy,
        ally_names=req.team
    )

    cache_service.set(
        cache_key,
        picks,
        ttl=3600
    )

    SUGGEST_LATENCY.observe(
        perf_counter() - start
    )

    return SuggestResponse(
        picks=[
            HeroSuggestion(**pick)
            for pick in picks
        ]
    )
@app.get("/metrics")
def metrics():

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )