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

@app.on_event("startup")
def startup():

    print("=" * 60)
    print("Dota Drafter API Started")
    print(f"Heroes Loaded: {len(hero_map)}")
    print("Version: 1.0.0")
    print("=" * 60)

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

    matchup_score: float
    synergy_score: float

    role_bonus: float
    draft_bonus: float

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
    "heroes": len(hero_map),
    "version": "1.0.0"
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
        f"v1:"
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

@app.get("/debug/counters/{hero_name}")
def debug_counters(hero_name: str):

    return {
        "hero": hero_name,
        "top_counters":
            hero_repository.get_top_counters(
                hero_name
            )
    }

@app.post("/debug/recommendation")
def debug_recommendation(
    req: DraftRequest
):

    return {
        "enemy": req.enemy,
        "team": req.team,
        "candidates": engine.audit(
            req.enemy,
            req.team
        )
    }

@app.post("/debug/missing-roles")
def debug_missing_roles(
    req: DraftRequest
):

    ally_ids = (
        engine.resolve_names(
            req.team
        )
    )

    return {
        "team": req.team,
        "missing_roles":
            engine.get_missing_roles(
                ally_ids
            )
    }

@app.get(
    "/debug/matchup/{hero}/{enemy}"
)
def debug_matchup(
    hero: str,
    enemy: str
):

    result = (
        hero_repository
        .get_matchup_details(
            hero,
            enemy
        )
    )

    if not result:

        return {
            "error":
            "matchup not found"
        }

    return result

@app.get("/debug/roles/{hero_name}")
def debug_roles(
    hero_name: str
):

    hero_id = (
        engine.name_to_id.get(
            hero_name.lower()
        )
    )

    return {
        "hero": hero_name,
        "roles":
            hero_repository.get_roles(
                hero_id
            )
    }