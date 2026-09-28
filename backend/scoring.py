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

model_metadata: Dict[str, Any] = {
    "loaded_at": None,
    "status": "missing_core_files",
    "files": {}
}

def load_models():
    global hero_map, matchup_matrix, synergy_matrix, hero_roles
    global hero_avg_matchup, hero_winrate, id_to_name, name_to_id
    global model_metadata
    
    import datetime
    
    temp_metadata = {"files": {}}
    
    def _safe_load(name: str, required: bool = True):
        path = os.path.join(settings.MODEL_DIR, name)
        if not os.path.exists(path):
            if required:
                raise RuntimeError(f"Required model file missing: {path}")
            return None
        
        # Track file metadata
        stat = os.stat(path)
        temp_metadata["files"][name] = {
            "size_bytes": stat.st_size,
            "modified_at": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
        
        with open(path, "rb") as f:
            return pickle.load(f)

    try:
        new_hero_map = _safe_load("hero_map.pkl")
        new_matchup = _safe_load("matchup.pkl")
        new_synergy = _safe_load("synergy.pkl")
        new_roles = _safe_load("roles.pkl")
        new_ml_model = _safe_load("model.pkl", required=False)
        
        # Optional models
        new_avg = _safe_load("hero_avg_matchup.pkl", required=False) or {}
        new_winrate = _safe_load("hero_winrate.pkl", required=False) or {}
            
        log.info(f"Loaded models - {len(new_hero_map)} heroes, {len(new_matchup)} matchups")
        
        # Atomic swap
        global ml_model
        hero_map = new_hero_map
        matchup_matrix = new_matchup
        synergy_matrix = new_synergy
        hero_roles = new_roles
        ml_model = new_ml_model
        hero_avg_matchup = new_avg
        hero_winrate = new_winrate
        
        id_to_name = hero_map
        name_to_id = {v.lower(): k for k, v in hero_map.items()}
        
        model_metadata["status"] = "ready"
        model_metadata["loaded_at"] = datetime.datetime.now().isoformat()
        model_metadata["files"] = temp_metadata["files"]
        return True
        
    except RuntimeError as e:
        log.error(str(e))
        model_metadata["status"] = "missing_core_files"
        model_metadata["error"] = str(e)
        return False

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

def predict(hero_id: int, enemy_ids: List[int], ally_ids: List[int], engine: str = 'heuristic') -> float:
    if engine == 'ml' and ml_model is not None:
        import numpy as np
        NUM_HEROES = len(hero_map)
        heroes_list = sorted(list(hero_map.keys()))
        hero_to_idx = {h: i for i, h in enumerate(heroes_list)}
        vec = []
        hero_vec = np.zeros(NUM_HEROES)
        team = ally_ids + [hero_id]
        for h in team:
            if h in hero_to_idx: hero_vec[hero_to_idx[h]] = 1
        for h in enemy_ids:
            if h in hero_to_idx: hero_vec[hero_to_idx[h]] = -1
        vec.extend(hero_vec)
        radiant_wr = np.mean([hero_winrate.get(h, 0.5) for h in team])
        dire_wr = np.mean([hero_winrate.get(h, 0.5) for h in enemy_ids])
        vec.append(2 * radiant_wr)
        vec.append(2 * dire_wr)
        vec.append(3 * (radiant_wr - dire_wr))
        matchup_score = 0
        for r in team:
            for d in enemy_ids:
                matchup_score += matchup_matrix.get((r, d), 0.5) - 0.5
        vec.append(4 * matchup_score)
        syn_score = 0
        for i in range(len(team)):
            for j in range(i+1, len(team)):
                pair = (team[i], team[j])
                rev_pair = (team[j], team[i])
                syn_score += synergy_matrix.get(pair, synergy_matrix.get(rev_pair, 0.5)) - 0.5
        vec.append(2 * syn_score)
        try:
            if hasattr(ml_model, 'predict_proba'):
                return float(ml_model.predict_proba([vec])[0][1])
            return 0.5
        except:
            return 0.5
    else:
        m = norm_matchup(hero_id, enemy_ids)
        s = synergy_score(hero_id, ally_ids)
        wr = hero_winrate.get(hero_id, 0.5)
        score = 1.50 * m + 0.35 * s + 0.06 * (wr - 0.5)
        if abs(m) < 0.005:
            score -= 0.02
        return score
