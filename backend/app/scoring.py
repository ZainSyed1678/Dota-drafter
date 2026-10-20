from typing import List, Tuple, Any
import numpy as np

from app.config import settings
from app.logger import get_logger
from app.model_loader import store
from app.hero_knowledge import (
    get_hero_difficulty,
    get_hero_overview,
    explain_counter,
    explain_synergy,
)

log = get_logger("dota-api.scoring")


def get_roles(hero_id: int) -> List[str]:
    r = store.hero_roles.get(hero_id, ["offlane"])
    return [x.lower() for x in (r if isinstance(r, list) else [r])]


def resolve_hero_id(identifier: Any) -> Any:
    if identifier is None:
        return None
    try:
        nid = int(identifier)
        if nid in store.hero_map:
            return nid
    except (ValueError, TypeError):
        pass
    s = str(identifier).strip().lower()
    return store.name_to_id.get(s)


def resolve_or_raise(identifiers: List[Any], field_name: str) -> List[int]:
    out = []
    for item in identifiers:
        hid = resolve_hero_id(item)
        if hid is None:
            raise ValueError(f"Unknown hero '{item}' in {field_name}. Please provide a valid Dota 2 hero name or ID.")
        out.append(hid)
    return out


def infer_missing_roles(ally_ids: List[int]) -> List[str]:
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

    return needed if needed else ["carry", "mid", "offlane", "support"]


def norm_matchup(hero_id: int, enemy_ids: List[int]) -> float:
    if not enemy_ids:
        return 0.0
    bl = store.hero_avg_matchup.get(hero_id, 0.50)
    total = 0.0
    for e in enemy_ids:
        raw = store.matchup_matrix.get((hero_id, e))
        if raw is None:
            rev = store.matchup_matrix.get((e, hero_id))
            raw = (1.0 - rev) if rev is not None else bl
        total += (raw - bl)
    return total / len(enemy_ids)


def synergy_score(hero_id: int, ally_ids: List[int]) -> float:
    if not ally_ids:
        return 0.0
    total = 0.0
    for a in ally_ids:
        pair = (min(hero_id, a), max(hero_id, a))
        v = store.synergy_matrix.get(pair, 0.50)
        total += (v - 0.50)
    return total / len(ally_ids)


def compute_model_win_prob(candidate_id: int, enemy_ids: List[int], ally_ids: List[int]) -> float:
    if store.ml_model is None or not store.hero_to_idx:
        return 0.50
    try:
        num_heroes = len(store.sorted_hero_ids)
        vec = np.zeros(num_heroes, dtype=np.float32)
        team = ally_ids + [candidate_id]
        for h in team:
            if h in store.hero_to_idx:
                vec[store.hero_to_idx[h]] = 1.0
        for h in enemy_ids:
            if h in store.hero_to_idx:
                vec[store.hero_to_idx[h]] = -1.0
        r_wr = float(np.mean([store.hero_winrate.get(h, 0.50) for h in team]))
        d_wr = float(np.mean([store.hero_winrate.get(h, 0.50) for h in enemy_ids])) if enemy_ids else 0.50
        extra = [r_wr, d_wr, r_wr - d_wr]
        feat = np.concatenate([vec, extra]).reshape(1, -1)

        if hasattr(store.ml_model, "predict_proba"):
            return float(store.ml_model.predict_proba(feat)[0][1])
        elif hasattr(store.ml_model, "predict"):
            pred = store.ml_model.predict(feat)
            if isinstance(pred, np.ndarray) and pred.ndim > 0:
                return float(pred[0])
            return float(pred)
        return 0.50
    except Exception as e:
        log.warning(f"Error computing model probability: {e}")
        return 0.50


def predict(hero_id: int, enemy_ids: List[int], ally_ids: List[int], engine: str = None) -> float:
    if engine is None:
        engine = settings.PREDICTION_ENGINE

    m = norm_matchup(hero_id, enemy_ids)
    s = synergy_score(hero_id, ally_ids)
    wr = store.hero_winrate.get(hero_id, 0.50)
    w_diff = wr - 0.50

    w_m = store.combiner_weights.get('matchup', 1.5604)
    w_s = store.combiner_weights.get('synergy', 1.5120)
    w_w = store.combiner_weights.get('winrate', 0.9607)
    w_p = store.combiner_weights.get('model', 2.2110)

    if engine == "ml":
        return compute_model_win_prob(hero_id, enemy_ids, ally_ids)

    if engine == "heuristic" or store.ml_model is None:
        score = w_m * m + w_s * s + w_w * w_diff
        if abs(m) < 0.005:
            score -= 0.02
        return score

    p_model = compute_model_win_prob(hero_id, enemy_ids, ally_ids)
    score = (w_m * m) + (w_s * s) + (w_w * w_diff) + (w_p * (p_model - 0.50))
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
    hero_name = store.id_to_name.get(hero_id, "This hero")
    bl = store.hero_avg_matchup.get(hero_id, 0.50)

    counters = []
    neutral = []
    for eid, ename in zip(enemy_ids, enemy_names):
        raw = store.matchup_matrix.get((hero_id, eid))
        if raw is None:
            rev = store.matchup_matrix.get((eid, hero_id))
            raw = (1.0 - rev) if rev is not None else bl
        adj = raw - bl
        sample_size = store.matchup_samples.get((hero_id, eid), store.matchup_samples.get((eid, hero_id), 0))
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
        v = store.synergy_matrix.get(pair, 0.50)
        adj = v - 0.50
        sample_size = store.synergy_samples.get(pair, 0)
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

    wr = store.hero_winrate.get(hero_id, 0.50)
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
