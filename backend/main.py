from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from logger import get_logger
from models import DraftRequest, SuggestResponse, HeroSuggestion
import scoring

log = get_logger("dota-api.main")

app = FastAPI(title="Dota 2 Drafter API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    ready = len(scoring.hero_map) > 0
    return {"status": "ok" if ready else "model_not_loaded", "heroes": len(scoring.hero_map)}

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
def suggest(req: DraftRequest):
    if not scoring.hero_map:
        raise HTTPException(503, "Model not loaded yet — pkl files missing")

    enemy_ids = scoring.resolve(req.enemy)
    ally_ids  = scoring.resolve(req.team)
    selected  = set(enemy_ids + ally_ids)

    scored = []
    for hero_id in scoring.hero_map:
        if hero_id in selected:
            continue
        m   = scoring.norm_matchup(hero_id, enemy_ids)
        s   = scoring.synergy_score(hero_id, ally_ids)
        wr  = scoring.hero_winrate.get(hero_id, 0.5)
        score = 1.50 * m + 0.35 * s + 0.06 * (wr - 0.5)
        if abs(m) < 0.005:
            score -= 0.02
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
