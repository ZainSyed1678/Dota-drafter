import os
import json
import pickle
from typing import Dict, Tuple, List, Any, Optional
import numpy as np

from logger import get_logger
from config import settings
from hero_knowledge import (
    get_hero_difficulty,
    get_hero_overview,
    explain_counter,
    explain_synergy,
)

log = get_logger("dota-api.scoring")

# Global states
hero_map: Dict[int, str] = {}
heroes_list: List[Dict[str, Any]] = []
matchup_matrix: Dict[Tuple[int, int], float] = {}
matchup_samples: Dict[Tuple[int, int], int] = {}
synergy_matrix: Dict[Tuple[int, int], float] = {}
synergy_samples: Dict[Tuple[int, int], int] = {}
hero_roles: Dict[int, List[str]] = {}
hero_avg_matchup: Dict[int, float] = {}
hero_winrate: Dict[int, float] = {}
combiner_weights: Dict[str, float] = {
    'matchup': 1.5604,
    'synergy': 1.5120,
    'winrate': 0.9607,
    'model': 2.2110,
    'intercept': 0.1035,
}
ml_model: Any = None
id_to_name: Dict[int, str] = {}
name_to_id: Dict[str, int] = {}
sorted_hero_ids: List[int] = []
hero_to_idx: Dict[int, int] = {}

model_metadata: Dict[str, Any] = {
    "version": "v2.2.0",
    "loaded_at": None,
    "status": "missing_core_files",
    "files": {},
    "combiner_weights": combiner_weights,
    "data_freshness": {},
}


def load_models(version: Optional[str] = None) -> bool:
    global hero_map, heroes_list, matchup_matrix, matchup_samples, synergy_matrix, synergy_samples, hero_roles
    global hero_avg_matchup, hero_winrate, id_to_name, name_to_id, ml_model, combiner_weights
    global sorted_hero_ids, hero_to_idx, model_metadata

    import datetime

    base_model_dir = settings.MODEL_DIR
    target_dir = base_model_dir

    # Support model/<version>/ directories
    if version:
        cand = os.path.join(base_model_dir, version)
        if os.path.isdir(cand):
            target_dir = cand
    elif os.path.isdir(base_model_dir):
        # Scan for version subdirectories (e.g. v2.2.0, v2.1.0)
        subdirs = [
            d for d in os.listdir(base_model_dir)
            if os.path.isdir(os.path.join(base_model_dir, d)) and not d.startswith(".")
            and os.path.exists(os.path.join(base_model_dir, d, "matchup.pkl"))
        ]
        if subdirs:
            subdirs.sort(reverse=True)
            target_dir = os.path.join(base_model_dir, subdirs[0])

    log.info(f"Loading model artifacts from {target_dir}...")
    temp_metadata = {"files": {}}

    def _safe_load(name: str, required: bool = True):
        path = os.path.join(target_dir, name)
        if not os.path.exists(path):
            # Fall back to base_model_dir if not found in version subfolder
            path = os.path.join(base_model_dir, name)
            if not os.path.exists(path):
                if required:
                    raise RuntimeError(f"Required model file missing: {path}")
                return None

        stat = os.stat(path)
        temp_metadata["files"][name] = {
            "size_bytes": stat.st_size,
            "modified_at": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }

        with open(path, "rb") as f:
            return pickle.load(f)

    try:
        new_hero_map = _safe_load("hero_map.pkl")
        new_matchup = _safe_load("matchup.pkl")
        new_synergy = _safe_load("synergy.pkl")
        new_roles = _safe_load("roles.pkl")

        new_ml_model = _safe_load("model.pkl", required=False)
        new_matchup_samples = _safe_load("matchup_samples.pkl", required=False) or {}
        new_synergy_samples = _safe_load("synergy_samples.pkl", required=False) or {}
        new_weights = _safe_load("combiner_weights.pkl", required=False) or {}
        new_avg = _safe_load("hero_avg_matchup.pkl", required=False) or {}
        new_winrate = _safe_load("hero_winrate.pkl", required=False) or {}

        # Load metadata.json if present
        meta_path = os.path.join(target_dir, "metadata.json")
        if not os.path.exists(meta_path):
            meta_path = os.path.join(base_model_dir, "metadata.json")
        disk_meta = {}
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    disk_meta = json.load(f)
            except Exception as e:
                log.warning(f"Failed to read metadata.json: {e}")

        # Load heroes_metadata.json if present
        heroes_meta_path = os.path.join(target_dir, "heroes_metadata.json")
        if not os.path.exists(heroes_meta_path):
            heroes_meta_path = os.path.join(base_model_dir, "heroes_metadata.json")
        loaded_heroes_list = []
        if os.path.exists(heroes_meta_path):
            try:
                with open(heroes_meta_path, "r", encoding="utf-8") as f:
                    loaded_heroes_list = json.load(f)
            except Exception as e:
                log.warning(f"Failed to read heroes_metadata.json: {e}")

        # Atomic state swap
        hero_map = new_hero_map
        matchup_matrix = new_matchup
        matchup_samples = new_matchup_samples
        synergy_matrix = new_synergy
        synergy_samples = new_synergy_samples
        hero_roles = new_roles
        ml_model = new_ml_model
        hero_avg_matchup = new_avg
        hero_winrate = new_winrate
        if new_weights:
            combiner_weights = new_weights

        id_to_name = hero_map
        name_to_id = {v.lower(): k for k, v in hero_map.items()}
        sorted_hero_ids = sorted(list(hero_map.keys()))
        hero_to_idx = {h: i for i, h in enumerate(sorted_hero_ids)}

        # Build fallback heroes_list if not loaded from file
        if loaded_heroes_list:
            heroes_list = loaded_heroes_list
        else:
            heroes_list = [
                {
                    "id": hid,
                    "name": hname,
                    "roles": get_roles(hid),
                    "attribute": "all",
                    "image_url": f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{hname.lower().replace(' ', '_').replace('-', '')}.png",
                    "icon_url": f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/icons/{hname.lower().replace(' ', '_').replace('-', '')}.png"
                }
                for hid, hname in sorted(hero_map.items(), key=lambda x: x[1])
            ]

        model_metadata["status"] = "ready"
        model_metadata["loaded_at"] = datetime.datetime.now().isoformat()
        model_metadata["model_path"] = target_dir
        model_metadata["files"] = temp_metadata["files"]
        model_metadata["combiner_weights"] = combiner_weights
        if disk_meta:
            model_metadata.update(disk_meta)

        log.info(f"Loaded model version {model_metadata.get('version', 'unknown')} ({len(hero_map)} heroes, {len(matchup_matrix)} matchups)")
        return True

    except Exception as e:
        log.error(f"Error loading models: {e}", exc_info=True)
        model_metadata["status"] = "missing_core_files"
        model_metadata["error"] = str(e)
        return False


# Load on import
load_models()


def get_roles(hero_id: int) -> List[str]:
    r = hero_roles.get(hero_id, ["offlane"])
    return [x.lower() for x in (r if isinstance(r, list) else [r])]


def resolve_hero_id(identifier: Any) -> Optional[int]:
    """Resolve hero name or numeric ID to valid integer hero ID."""
    if identifier is None:
        return None
    try:
        nid = int(identifier)
        if nid in hero_map:
            return nid
    except (ValueError, TypeError):
        pass

    s = str(identifier).strip().lower()
    if s in name_to_id:
        return name_to_id[s]
    return None


def resolve_or_raise(identifiers: List[Any], field_name: str) -> List[int]:
    """Resolve list of identifiers or raise ValueError for unknown heroes."""
    if not hero_map:
        load_models()

    out = []
    for item in identifiers:
        hid = resolve_hero_id(item)
        if hid is None:
            raise ValueError(f"Unknown hero '{item}' in {field_name}. Please provide a valid Dota 2 hero name or ID.")
        out.append(hid)
    return out


def infer_missing_roles(ally_ids: List[int]) -> List[str]:
    """
    Infer missing roles from current allies.
    Standard Dota composition: 1 carry, 1 mid, 1 offlane, 2 supports.
    """
    role_counts = {"carry": 0, "mid": 0, "offlane": 0, "support": 0}
    for aid in ally_ids:
        roles = get_roles(aid)
        for r in roles:
            if r in role_counts:
                role_counts[r] += 1

    needed = []
    if role_counts["carry"] == 0:
        needed.append("carry")
    if role_counts["mid"] == 0:
        needed.append("mid")
    if role_counts["offlane"] == 0:
        needed.append("offlane")
    if role_counts["support"] < 2:
        needed.append("support")

    if not needed:
        needed = ["carry", "mid", "offlane", "support"]
    return needed


def resolve(names: List[str]) -> List[int]:
    out, missing = [], []
    for n in names:
        hid = resolve_hero_id(n)
        if hid is not None:
            out.append(hid)
        else:
            missing.append(n)
    if missing:
        log.warning(f"Unresolved hero names: {missing}")
    return out


def norm_matchup(hero_id: int, enemy_ids: List[int]) -> float:
    if not enemy_ids:
        return 0.0
    bl = hero_avg_matchup.get(hero_id, 0.50)
    total = 0.0
    for e in enemy_ids:
        raw = matchup_matrix.get((hero_id, e))
        if raw is None:
            rev = matchup_matrix.get((e, hero_id))
            raw = (1.0 - rev) if rev is not None else bl
        total += (raw - bl)
    return total / len(enemy_ids)


def synergy_score(hero_id: int, ally_ids: List[int]) -> float:
    if not ally_ids:
        return 0.0
    total = 0.0
    for a in ally_ids:
        pair = (min(hero_id, a), max(hero_id, a))
        v = synergy_matrix.get(pair, 0.50)
        total += (v - 0.50)
    return total / len(ally_ids)


def compute_model_win_prob(candidate_id: int, enemy_ids: List[int], ally_ids: List[int]) -> float:
    """Predict draft win probability using LightGBM model."""
    if ml_model is None or not hero_to_idx:
        return 0.50
    try:
        num_heroes = len(sorted_hero_ids)
        vec = np.zeros(num_heroes, dtype=np.float32)
        team = ally_ids + [candidate_id]
        for h in team:
            if h in hero_to_idx:
                vec[hero_to_idx[h]] = 1.0
        for h in enemy_ids:
            if h in hero_to_idx:
                vec[hero_to_idx[h]] = -1.0
        r_wr = float(np.mean([hero_winrate.get(h, 0.50) for h in team]))
        d_wr = float(np.mean([hero_winrate.get(h, 0.50) for h in enemy_ids])) if enemy_ids else 0.50
        extra = [r_wr, d_wr, r_wr - d_wr]
        feat = np.concatenate([vec, extra]).reshape(1, -1)

        if hasattr(ml_model, "predict_proba"):
            return float(ml_model.predict_proba(feat)[0][1])
        elif hasattr(ml_model, "predict"):
            pred = ml_model.predict(feat)
            if isinstance(pred, np.ndarray) and pred.ndim > 0:
                return float(pred[0])
            return float(pred)
        return 0.50
    except Exception as e:
        log.warning(f"Error computing model win probability: {e}")
        return 0.50


def predict(hero_id: int, enemy_ids: List[int], ally_ids: List[int], engine: str = None) -> float:
    """
    Score candidate hero using empirical combination:
    Score = w_matchup * M + w_synergy * S + w_winrate * W + w_model * (P_model - 0.5)
    """
    if engine is None:
        engine = settings.PREDICTION_ENGINE

    m = norm_matchup(hero_id, enemy_ids)
    s = synergy_score(hero_id, ally_ids)
    wr = hero_winrate.get(hero_id, 0.50)
    w_diff = wr - 0.50

    w_m = combiner_weights.get('matchup', 1.5604)
    w_s = combiner_weights.get('synergy', 1.5120)
    w_w = combiner_weights.get('winrate', 0.9607)
    w_p = combiner_weights.get('model', 2.2110)

    if engine == "ml":
        return compute_model_win_prob(hero_id, enemy_ids, ally_ids)

    if engine == "heuristic" or ml_model is None:
        score = w_m * m + w_s * s + w_w * w_diff
        if abs(m) < 0.005:
            score -= 0.02
        return score

    # Default 'combined' engine
    p_model = compute_model_win_prob(hero_id, enemy_ids, ally_ids)
    p_model_centered = p_model - 0.50
    score = (w_m * m) + (w_s * s) + (w_w * w_diff) + (w_p * p_model_centered)
    return score


def build_reasons_and_details(
    hero_id: int,
    enemy_ids: List[int],
    enemy_names: List[str],
    ally_ids: List[int],
    ally_names: List[str]
) -> Tuple[List[str], List[dict], str, int]:
    reasons: List[str] = []
    details: List[dict] = []
    hero_name = id_to_name.get(hero_id, "This hero")
    bl = hero_avg_matchup.get(hero_id, 0.50)

    counters = []
    neutral = []
    for eid, ename in zip(enemy_ids, enemy_names):
        raw = matchup_matrix.get((hero_id, eid))
        if raw is None:
            rev = matchup_matrix.get((eid, hero_id))
            raw = (1.0 - rev) if rev is not None else bl
        adj = raw - bl
        sample_size = matchup_samples.get((hero_id, eid), matchup_samples.get((eid, hero_id), 0))
        if sample_size >= 50:
            confidence = "high"
        elif sample_size >= 15:
            confidence = "medium"
        else:
            confidence = "low"

        if adj >= 0.01:
            counters.append((ename, adj, sample_size, confidence))
        elif adj >= -0.005:
            neutral.append((ename, adj, sample_size, confidence))

    def counter_sort_key(item):
        ename, adj, n_games, conf = item
        conf_rank = 2 if conf == "high" else (1 if conf == "medium" else 0)
        return (conf_rank, adj)

    counters.sort(key=counter_sort_key, reverse=True)
    neutral.sort(key=counter_sort_key, reverse=True)

    primary_confidence = "medium"
    primary_sample_size = 0

    if counters:
        primary_confidence = counters[0][3]
        primary_sample_size = counters[0][2]
        for name, adj, sample_size, conf in counters:
            if conf == "low":
                summary_str = f"Counters {name} ({adj:+.1%} WR, {sample_size} games - low sample)"
            else:
                summary_str = f"Counters {name} ({adj:+.1%} WR, {sample_size} games)"
            reasons.append(summary_str)
            explanation = explain_counter(hero_name, name, adj)
            explanation["sample_size"] = sample_size
            explanation["confidence"] = conf
            details.append(explanation)
    elif neutral:
        primary_confidence = neutral[0][3]
        primary_sample_size = neutral[0][2]
        for name, adj, sample_size, conf in neutral[:2]:
            summary_str = f"Even vs {name} ({adj:+.1%} WR, {sample_size} games)"
            reasons.append(summary_str)
            details.append({
                "summary": summary_str,
                "target_hero": name,
                "reason_type": "meta",
                "how_and_why": f"{hero_name} trades evenly into {name} without significant lane or game disadvantage.",
                "key_abilities": [],
                "beginner_tip": f"Play around your team's power spikes and stick close to allies when fighting {name}.",
                "sample_size": sample_size,
                "confidence": conf
            })
    else:
        reasons.append("Picked for synergy / meta")
        details.append({
            "summary": "Picked for synergy / meta",
            "target_hero": "",
            "reason_type": "meta",
            "how_and_why": f"{hero_name} provides stable teamfight control and general utility that fits the current draft balance.",
            "key_abilities": [],
            "beginner_tip": "Focus on hitting core item timings and group up for team objectives.",
            "sample_size": 0,
            "confidence": "medium"
        })

    syn = []
    for aid, aname in zip(ally_ids, ally_names):
        pair = (min(hero_id, aid), max(hero_id, aid))
        v = synergy_matrix.get(pair, 0.50)
        adj = v - 0.50
        sample_size = synergy_samples.get(pair, 0)
        if sample_size >= 50:
            syn_conf = "high"
        elif sample_size >= 15:
            syn_conf = "medium"
        else:
            syn_conf = "low"
        if adj >= 0.01:
            syn.append((aname, adj, sample_size, syn_conf))

    syn.sort(key=lambda x: (2 if x[3] == "high" else (1 if x[3] == "medium" else 0), x[1]), reverse=True)
    if syn and primary_sample_size == 0:
        primary_confidence = syn[0][3]
        primary_sample_size = syn[0][2]

    for name, adj, sample_size, syn_conf in syn[:2]:
        if syn_conf == "low":
            summary_str = f"Synergy: {name} ({adj:+.1%} WR, {sample_size} games - low sample)"
        else:
            summary_str = f"Synergy: {name} ({adj:+.1%} WR, {sample_size} games)"
        reasons.append(summary_str)
        explanation = explain_synergy(hero_name, name, adj)
        explanation["sample_size"] = sample_size
        explanation["confidence"] = syn_conf
        details.append(explanation)

    wr = hero_winrate.get(hero_id, 0.50)
    if wr > 0.53:
        summary_str = f"Meta strong ({wr:.1%} WR)"
        reasons.append(summary_str)
        details.append({
            "summary": summary_str,
            "target_hero": "",
            "reason_type": "meta",
            "how_and_why": f"{hero_name} maintains a strong {wr:.1%} overall winrate, making them an inherently high-value pick in the current meta.",
            "key_abilities": [],
            "beginner_tip": "A very forgiving pick with strong fundamental stats and reliable execution.",
            "sample_size": int(round(sample_size)) if sample_size else 0,
            "confidence": "high"
        })

    return reasons, details, primary_confidence, primary_sample_size


def build_reasons(
    hero_id: int,
    enemy_ids: List[int],
    enemy_names: List[str],
    ally_ids: List[int],
    ally_names: List[str]
) -> List[str]:
    reasons, _, _, _ = build_reasons_and_details(hero_id, enemy_ids, enemy_names, ally_ids, ally_names)
    return reasons
