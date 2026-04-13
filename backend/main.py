from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pickle, os, numpy as np
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("dota-api")

app = FastAPI(title="Dota 2 Drafter API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load pkl files ────────────────────────────────────────────────────────────
BASE = os.getenv("MODEL_DIR", os.path.join(os.path.dirname(__file__), "model"))

def _load(name):
    path = os.path.join(BASE, name)
    if not os.path.exists(path):
        raise RuntimeError(f"Model file not found: {path}\n"
                           f"Run the notebook to generate pkl files first.")
    with open(path, "rb") as f:
        return pickle.load(f)

try:
    hero_map         = _load("hero_map.pkl")
    matchup_matrix   = _load("matchup.pkl")
    synergy_matrix   = _load("synergy.pkl")
    hero_roles       = _load("roles.pkl")
    hero_avg_matchup = _load("hero_avg_matchup.pkl")
    hero_winrate     = _load("hero_winrate.pkl")
    log.info(f"Loaded models — {len(hero_map)} heroes, "
             f"{len(matchup_matrix)} matchup pairs, "
             f"{len(synergy_matrix)} synergy pairs")
except RuntimeError as e:
    log.error(str(e))
    # Don't crash on startup — health check will fail until model is ready
    hero_map = matchup_matrix = synergy_matrix = {}
    hero_roles = hero_avg_matchup = hero_winrate = {}

id_to_name: dict = hero_map
name_to_id: dict = {v.lower(): k for k, v in hero_map.items()}


# ── Models ────────────────────────────────────────────────────────────────────
class DraftRequest(BaseModel):
    enemy: list[str]
    team:  list[str]

class HeroSuggestion(BaseModel):
    id:      int
    name:    str
    score:   float
    reasons: list[str]
    roles:   list[str]

class SuggestResponse(BaseModel):
    picks: list[HeroSuggestion]


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_roles(hero_id: int) -> list[str]:
    r = hero_roles.get(hero_id, ["offlane"])
    return [x.lower() for x in (r if isinstance(r, list) else [r])]

def resolve(names: list[str]) -> list[int]:
    out, missing = [], []
    for n in names:
        rid = name_to_id.get(n.lower())
        if rid is not None:
            out.append(rid)
        else:
            missing.append(n)
    if missing:
        log.warning(f"Unresolved hero names: {missing} — check /debug")
    return out

def norm_matchup(hero_id: int, enemy_ids: list[int]) -> float:
    if not enemy_ids: return 0.0
    bl    = hero_avg_matchup.get(hero_id, 0.5)
    total = 0.0
    for e in enemy_ids:
        raw = matchup_matrix.get((hero_id, e)) or matchup_matrix.get((e, hero_id)) or bl
        total += raw - bl
    return total / len(enemy_ids)

def synergy_score(hero_id: int, ally_ids: list[int]) -> float:
    if not ally_ids: return 0.0
    total = 0.0
    for a in ally_ids:
        v = synergy_matrix.get((hero_id, a)) or synergy_matrix.get((a, hero_id)) or 0.5
        total += v - 0.5
    return total / len(ally_ids)

def build_reasons(hero_id, enemy_ids, enemy_names, ally_ids, ally_names):
    reasons = []
    bl      = hero_avg_matchup.get(hero_id, 0.5)

    counters, neutral = [], []
    for eid, ename in zip(enemy_ids, enemy_names):
        raw = matchup_matrix.get((hero_id, eid)) or matchup_matrix.get((eid, hero_id)) or bl
        adj = raw - bl
        if adj >= 0.01:
            counters.append((ename, adj))
        elif adj >= -0.005:
            neutral.append((ename, adj))

    counters.sort(key=lambda x: x[1], reverse=True)
    neutral.sort( key=lambda x: x[1], reverse=True)

    if counters:
        for name, adj in counters:
            reasons.append(f"Counters {name} ({adj:+.3f} WR)")
    elif neutral:
        for name, adj in neutral[:2]:
            reasons.append(f"Even vs {name} ({adj:+.3f} WR)")
    else:
        reasons.append("Picked for synergy / meta")

    syn = []
    for aid, aname in zip(ally_ids, ally_names):
        v   = synergy_matrix.get((hero_id, aid)) or synergy_matrix.get((aid, hero_id)) or 0.5
        adj = v - 0.5
        if adj >= 0.01:
            syn.append((aname, adj))
    syn.sort(key=lambda x: x[1], reverse=True)
    for name, adj in syn[:2]:
        reasons.append(f"Synergy: {name} ({adj:+.3f} WR)")

    wr = hero_winrate.get(hero_id, 0.5)
    if wr > 0.53:
        reasons.append(f"Meta strong ({wr:.1%} WR)")

    return reasons


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    ready = len(hero_map) > 0
    return {"status": "ok" if ready else "model_not_loaded", "heroes": len(hero_map)}

@app.get("/debug")
def debug():
    return {
        "hero_map_sample":     {k: hero_map[k] for k in list(hero_map)[:20]},
        "avg_matchup_sample":  {hero_map.get(k,k): round(v,4)
                                for k,v in list(hero_avg_matchup.items())[:10]},
        "total_heroes":        len(hero_map),
        "total_matchup_pairs": len(matchup_matrix),
        "total_synergy_pairs": len(synergy_matrix),
    }

@app.get("/heroes")
def heroes():
    return hero_map

@app.post("/suggest", response_model=SuggestResponse)
def suggest(req: DraftRequest):
    if not hero_map:
        raise HTTPException(503, "Model not loaded yet — pkl files missing")

    enemy_ids = resolve(req.enemy)
    ally_ids  = resolve(req.team)
    selected  = set(enemy_ids + ally_ids)

    scored = []
    for hero_id in hero_map:
        if hero_id in selected or hero_id not in hero_avg_matchup:
            continue
        m   = norm_matchup(hero_id, enemy_ids)
        s   = synergy_score(hero_id, ally_ids)
        wr  = hero_winrate.get(hero_id, 0.5)
        score = 1.50 * m + 0.35 * s + 0.06 * (wr - 0.5)
        if abs(m) < 0.005:
            score -= 0.02
        scored.append((hero_id, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    picks = []
    for hero_id, score in scored[:9]:
        picks.append(HeroSuggestion(
            id      = hero_id,
            name    = id_to_name[hero_id],
            score   = round(score, 4),
            reasons = build_reasons(hero_id, enemy_ids, req.enemy, ally_ids, req.team),
            roles   = get_roles(hero_id),
        ))

    return SuggestResponse(picks=picks)
