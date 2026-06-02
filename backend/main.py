from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.model_loader import model_store
from services.recommendation_engine import engine


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

hero_map = model_store.hero_map
matchup_matrix = model_store.matchup_matrix
synergy_matrix = model_store.synergy_matrix
hero_avg_matchup = model_store.hero_avg_matchup


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
    return {
        "hero_map_sample": {
            k: hero_map[k]
            for k in list(hero_map)[:20]
        },
        "avg_matchup_sample": {
            hero_map.get(k, k): round(v, 4)
            for k, v in list(hero_avg_matchup.items())[:10]
        },
        "total_heroes": len(hero_map),
        "total_matchup_pairs": len(matchup_matrix),
        "total_synergy_pairs": len(synergy_matrix),
    }


@app.get("/heroes")
def heroes():
    return hero_map


@app.post(
    "/suggest",
    response_model=SuggestResponse
)
def suggest(req: DraftRequest):

    picks = engine.suggest(
        enemy_names=req.enemy,
        ally_names=req.team
    )

    return SuggestResponse(
        picks=[
            HeroSuggestion(**pick)
            for pick in picks
        ]
    )