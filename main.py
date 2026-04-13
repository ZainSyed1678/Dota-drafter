from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pickle, os, numpy as np

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ── Load pkl files ────────────────────────────────────────────────────────────
BASE = os.path.join(os.path.dirname(__file__), "model")

hero_map         = pickle.load(open(os.path.join(BASE, "hero_map.pkl"),         "rb"))
matchup_matrix   = pickle.load(open(os.path.join(BASE, "matchup.pkl"),          "rb"))
synergy_matrix   = pickle.load(open(os.path.join(BASE, "synergy.pkl"),          "rb"))
hero_roles       = pickle.load(open(os.path.join(BASE, "roles.pkl"),            "rb"))
hero_avg_matchup = pickle.load(open(os.path.join(BASE, "hero_avg_matchup.pkl"), "rb"))
hero_winrate     = pickle.load(open(os.path.join(BASE, "hero_winrate.pkl"),     "rb"))

id_to_name: dict = hero_map
name_to_id: dict = {v.lower(): k for k, v in hero_map.items()}


# ── Pydantic models ───────────────────────────────────────────────────────────
class DraftRequest(BaseModel):
    enemy: list[str]
    team:  list[str]

class HeroSuggestion(BaseModel):
    id:      int
    name:    str
    score:   float
    reasons: list[str]
    roles:   list[str]   # all roles, shown as badges on card

class SuggestResponse(BaseModel):
    picks: list[HeroSuggestion]   # flat top-9, no role buckets


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_roles(hero_id: int) -> list[str]:
    r = hero_roles.get(hero_id, ["offlane"])
    if isinstance(r, str):
        r = [r]
    return [x.lower() for x in r]

def resolve_names(names: list[str]) -> list[int]:
    out = []
    for n in names:
        rid = name_to_id.get(n.lower())
        if rid is not None:
            out.append(rid)
    return out

def norm_matchup(hero_id: int, enemy_ids: list[int]) -> float:
    """Normalised matchup: advantage ABOVE this hero's global average."""
    if not enemy_ids:
        return 0.0
    bl = hero_avg_matchup.get(hero_id, 0.5)
    total = 0.0
    for e in enemy_ids:
        raw = matchup_matrix.get((hero_id, e))
        if raw is None:
            raw = matchup_matrix.get((e, hero_id))
        if raw is None:
            raw = bl
        total += raw - bl
    return total / len(enemy_ids)

def synergy_score(hero_id: int, ally_ids: list[int]) -> float:
    if not ally_ids:
        return 0.0
    total = 0.0
    for a in ally_ids:
        v = synergy_matrix.get((hero_id, a))
        if v is None:
            v = synergy_matrix.get((a, hero_id))
        if v is None:
            v = 0.5
        total += v - 0.5
    return total / len(ally_ids)

def build_reasons(hero_id, enemy_ids, enemy_names, ally_ids, ally_names):
    reasons  = []
    bl       = hero_avg_matchup.get(hero_id, 0.5)

    # Counter reasons — one per enemy (normalised)
    counters, neutral = [], []
    for eid, ename in zip(enemy_ids, enemy_names):
        raw = matchup_matrix.get((hero_id, eid)) or matchup_matrix.get((eid, hero_id)) or bl
        adj = raw - bl
        if adj >= 0.01:
            counters.append((ename, adj))
        elif adj >= -0.005:
            neutral.append((ename, adj))

    counters.sort(key=lambda x: x[1], reverse=True)
    neutral.sort(key=lambda x:  x[1], reverse=True)

    if counters:
        for name, adj in counters:
            reasons.append(f"Counters {name} ({adj:+.3f} WR)")
    elif neutral:
        for name, adj in neutral[:2]:
            reasons.append(f"Even vs {name} ({adj:+.3f} WR)")
    else:
        reasons.append("Picked for synergy / meta")

    # Synergy reasons
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
@app.get("/debug")
def debug():
    return {
        "hero_map_sample":        {k: hero_map[k] for k in list(hero_map)[:20]},
        "avg_matchup_sample":     {hero_map.get(k,k): round(v,4)
                                   for k,v in list(hero_avg_matchup.items())[:10]},
        "total_heroes":           len(hero_map),
        "total_matchup_pairs":    len(matchup_matrix),
        "total_synergy_pairs":    len(synergy_matrix),
    }

@app.get("/heroes")
def heroes():
    return hero_map

@app.post("/suggest", response_model=SuggestResponse)
def suggest(req: DraftRequest):
    enemy_ids = resolve_names(req.enemy)
    ally_ids  = resolve_names(req.team)
    selected  = set(enemy_ids + ally_ids)

    unresolved = [n for n in req.enemy + req.team if name_to_id.get(n.lower()) is None]
    if unresolved:
        print(f"WARNING unresolved names: {unresolved}")

    scored = []
    for hero_id in hero_map:
        if hero_id in selected or hero_id not in hero_avg_matchup:
            continue

        m   = norm_matchup(hero_id, enemy_ids)
        s   = synergy_score(hero_id, ally_ids)
        wr  = hero_winrate.get(hero_id, 0.5)

        score = (
            1.50 * m
            + 0.35 * s
            + 0.06 * (wr - 0.5)
        )
        if abs(m) < 0.005:
            score -= 0.02

        scored.append((hero_id, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    picks = []
    for hero_id, score in scored[:9]:
        reasons = build_reasons(hero_id, enemy_ids, req.enemy, ally_ids, req.team)
        picks.append(HeroSuggestion(
            id      = hero_id,
            name    = id_to_name[hero_id],
            score   = round(score, 4),
            reasons = reasons,
            roles   = get_roles(hero_id),
        ))

    return SuggestResponse(picks=picks)
