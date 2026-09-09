import os
import pickle
from typing import Dict, Tuple, List, Any
from logger import get_logger
from config import settings

log = get_logger("dota-api.scoring")

def _load(name: str) -> Any:
    path = os.path.join(settings.MODEL_DIR, name)
    if not os.path.exists(path):
        raise RuntimeError(f"Model file not found: {path}")
    with open(path, "rb") as f:
        return pickle.load(f)

# Global states
hero_map: Dict[int, str] = {}
matchup_matrix: Dict[Tuple[int, int], float] = {}
synergy_matrix: Dict[Tuple[int, int], float] = {}
hero_roles: Dict[int, List[str]] = {}
hero_avg_matchup: Dict[int, float] = {}
hero_winrate: Dict[int, float] = {}
id_to_name: Dict[int, str] = {}
name_to_id: Dict[str, int] = {}

def load_models():
    global hero_map, matchup_matrix, synergy_matrix, hero_roles
    global hero_avg_matchup, hero_winrate, id_to_name, name_to_id
    
    try:
        hero_map = _load("hero_map.pkl")
        matchup_matrix = _load("matchup.pkl")
        synergy_matrix = _load("synergy.pkl")
        hero_roles = _load("roles.pkl")
        
        # Optional models
        try:
            hero_avg_matchup = _load("hero_avg_matchup.pkl")
        except RuntimeError:
            log.warning("hero_avg_matchup.pkl missing, using defaults.")
            hero_avg_matchup = {}
            
        try:
            hero_winrate = _load("hero_winrate.pkl")
        except RuntimeError:
            log.warning("hero_winrate.pkl missing, using defaults.")
            hero_winrate = {}
            
        log.info(f"Loaded models - {len(hero_map)} heroes, {len(matchup_matrix)} matchups")
        
        id_to_name = hero_map
        name_to_id = {v.lower(): k for k, v in hero_map.items()}
        
    except RuntimeError as e:
        log.error(str(e))
        hero_map = matchup_matrix = synergy_matrix = {}
        hero_roles = hero_avg_matchup = hero_winrate = {}

# Load once on import
load_models()

def get_roles(hero_id: int) -> List[str]:
    r = hero_roles.get(hero_id, ["offlane"])
    return [x.lower() for x in (r if isinstance(r, list) else [r])]

def resolve(names: List[str]) -> List[int]:
    out, missing = [], []
    for n in names:
        rid = name_to_id.get(n.lower())
        if rid is not None:
            out.append(rid)
        else:
            missing.append(n)
    if missing:
        log.warning(f"Unresolved hero names: {missing}")
    return out

def norm_matchup(hero_id: int, enemy_ids: List[int]) -> float:
    if not enemy_ids: return 0.0
    bl = hero_avg_matchup.get(hero_id, 0.5)
    total = 0.0
    for e in enemy_ids:
        raw = matchup_matrix.get((hero_id, e)) or matchup_matrix.get((e, hero_id)) or bl
        total += raw - bl
    return total / len(enemy_ids)

def synergy_score(hero_id: int, ally_ids: List[int]) -> float:
    if not ally_ids: return 0.0
    total = 0.0
    for a in ally_ids:
        v = synergy_matrix.get((hero_id, a)) or synergy_matrix.get((a, hero_id)) or 0.5
        total += v - 0.5
    return total / len(ally_ids)

def build_reasons(hero_id: int, enemy_ids: List[int], enemy_names: List[str], ally_ids: List[int], ally_names: List[str]) -> List[str]:
    reasons = []
    bl = hero_avg_matchup.get(hero_id, 0.5)

    counters, neutral = [], []
    for eid, ename in zip(enemy_ids, enemy_names):
        raw = matchup_matrix.get((hero_id, eid)) or matchup_matrix.get((eid, hero_id)) or bl
        adj = raw - bl
        if adj >= 0.01:
            counters.append((ename, adj))
        elif adj >= -0.005:
            neutral.append((ename, adj))

    counters.sort(key=lambda x: x[1], reverse=True)
    neutral.sort(key=lambda x: x[1], reverse=True)

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
        v = synergy_matrix.get((hero_id, aid)) or synergy_matrix.get((aid, hero_id)) or 0.5
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
