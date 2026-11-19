from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.config import settings
from app.hero_knowledge import (
    CARRY_HEROES,
    HARD_SUPPORTS,
    MID_HEROES,
    OFFLANE_HEROES,
    SOFT_SUPPORTS,
    SPECIFIC_COUNTERS,
    SPECIFIC_SYNERGIES,
    explain_counter,
    explain_role_fit,
    explain_synergy,
    get_hero_overview,
)
from app.logger import get_logger
from app.model_loader import store

log = get_logger("dota-api.scoring")


def get_role_probability(hero_id: int, role: str) -> float:
    """Return data-driven P(role | hero), falling back to static taxonomy."""
    r_clean = role.lower()
    if r_clean in ("soft_support", "hard_support"):
        r_clean = "support"

    if hasattr(store, "hero_role_distributions") and store.hero_role_distributions:
        dist = store.hero_role_distributions.get(hero_id)
        if dist:
            return float(dist.get(r_clean, 0.0))

    # Static taxonomy fallback
    raw = store.hero_roles.get(hero_id, ["offlane"])
    static_roles = [x.lower() for x in (raw if isinstance(raw, list) else [raw])]
    if r_clean in static_roles:
        return 1.0 / max(1, len(static_roles))
    return 0.05


def get_roles(hero_id: int, threshold: float = 0.15) -> List[str]:
    """Return active roles for hero where P(role | hero) >= threshold, with taxonomy fallback."""
    roles = []
    # 1. Data-driven role distributions if loaded
    if hasattr(store, "hero_role_distributions") and store.hero_role_distributions:
        dist = store.hero_role_distributions.get(hero_id)
        if dist:
            for r, p in dist.items():
                if p >= threshold:
                    roles.append(r)
                    if r == "support":
                        roles.extend(["soft_support", "hard_support"])
            if roles:
                return sorted(list(set(roles)))

    # 2. Canonical sets fallback
    hero_name = store.id_to_name.get(hero_id, "")
    if hero_name in CARRY_HEROES:
        roles.append("carry")
    if hero_name in MID_HEROES:
        roles.append("mid")
    if hero_name in OFFLANE_HEROES:
        roles.append("offlane")
    if hero_name in SOFT_SUPPORTS:
        roles.append("soft_support")
        if "support" not in roles:
            roles.append("support")
    if hero_name in HARD_SUPPORTS:
        roles.append("hard_support")
        if "support" not in roles:
            roles.append("support")

    # 3. Static taxonomy dictionary fallback
    if not roles:
        raw = store.hero_roles.get(hero_id, ["offlane"])
        roles = [x.lower() for x in (raw if isinstance(raw, list) else [raw])]
        if "support" in roles:
            roles.extend(["soft_support", "hard_support"])
    return sorted(list(set(roles)))


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


def compute_posterior_confidence(
    games: int,
    raw_rate: float = 0.50,
    prior: float = 0.50,
    k: float = 15.0,
    max_width_high: float = 0.08,
    max_width_medium: float = 0.15
) -> Tuple[str, float]:
    """
    Computes confidence tier ('high', 'medium', 'low') and 95% posterior interval width
    from Beta posterior variance instead of hardcoded small-sample constants.
    """
    if games <= 0:
        return "low", 1.0

    wins = raw_rate * games
    alpha = wins + k * prior
    beta = (games - wins) + k * (1.0 - prior)
    total = alpha + beta

    var = (alpha * beta) / ((total ** 2) * (total + 1.0))
    interval_width = float(3.92 * np.sqrt(max(0.0, var)))

    if interval_width <= max_width_high or games >= 200:
        tier = "high"
    elif interval_width <= max_width_medium or games >= 50:
        tier = "medium"
    else:
        tier = "low"

    return tier, interval_width


def norm_matchup(hero_id: int, enemy_ids: List[int], hero_role: Optional[str] = None) -> float:
    if not enemy_ids:
        return 0.0
    bl = store.hero_avg_matchup.get(hero_id, 0.50)
    total = 0.0
    for e in enemy_ids:
        raw = None
        # Role-conditioned matchup with global fallback
        if hero_role and hasattr(store, "role_matchup_matrix") and store.role_matchup_matrix:
            e_roles = get_roles(e)
            e_primary = e_roles[0] if e_roles else "offlane"
            raw = store.role_matchup_matrix.get((hero_id, e, hero_role, e_primary))

        if raw is None:
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

        n_r = len(team)
        n_d = len(enemy_ids)
        total_rev = n_r + n_d

        # Check if active model expects masked partial-draft features (num_heroes + 7)
        is_masked = (
            store.combiner_weights.get("is_masked", False)
            or (hasattr(store.ml_model, "num_feature") and store.ml_model.num_feature() == num_heroes + 7)
        )

        if is_masked:
            state_indicators = np.array([
                n_r / 5.0,
                n_d / 5.0,
                (n_r - n_d) / 5.0,
                total_rev / 10.0,
                r_wr,
                d_wr,
                r_wr - d_wr
            ], dtype=np.float32)
            feat = np.concatenate([vec, state_indicators]).reshape(1, -1)
        else:
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


def compute_embedding_win_prob(candidate_id: int, enemy_ids: List[int], ally_ids: List[int]) -> float:
    """Compute win probability using the HeroEmbeddingDeepSet neural network."""
    if store.embedding_model is None:
        return 0.50
    try:
        import torch
        team = list(ally_ids) + [candidate_id]
        hero_to_idx = store.hero_to_idx
        num_heroes = len(hero_to_idx)

        rad_slots = [0] * 5
        for i, hid in enumerate(team[:5]):
            if hid in hero_to_idx:
                rad_slots[i] = hero_to_idx[hid] + 1

        dire_slots = [0] * 5
        for i, hid in enumerate(enemy_ids[:5]):
            if hid in hero_to_idx:
                dire_slots[i] = hero_to_idx[hid] + 1

        n_r = len(team)
        n_d = len(enemy_ids)
        tot = n_r + n_d
        r_wr = float(np.mean([store.hero_winrate.get(h, 0.50) for h in team])) if team else 0.50
        d_wr = float(np.mean([store.hero_winrate.get(h, 0.50) for h in enemy_ids])) if enemy_ids else 0.50

        state_feat = [
            n_r / 5.0,
            n_d / 5.0,
            (n_r - n_d) / 5.0,
            tot / 10.0,
            r_wr,
            d_wr,
            r_wr - d_wr
        ]

        rad_t = torch.tensor([rad_slots], dtype=torch.long)
        dire_t = torch.tensor([dire_slots], dtype=torch.long)
        state_t = torch.tensor([state_feat], dtype=torch.float32)

        with torch.no_grad():
            if hasattr(store.embedding_model, "predict_proba"):
                prob = store.embedding_model.predict_proba(rad_t, dire_t, state_t).item()
            else:
                out = store.embedding_model(rad_t, dire_t, state_t)
                prob = torch.sigmoid(out).item()
        return float(prob)
    except Exception as e:
        log.warning(f"Error computing embedding model probability: {e}")
        return 0.50


def predict(
    hero_id: int,
    enemy_ids: List[int],
    ally_ids: List[int],
    engine: str = None,
    target_role: Optional[str] = None
) -> float:
    if engine is None:
        engine = settings.PREDICTION_ENGINE

    m = norm_matchup(hero_id, enemy_ids, hero_role=target_role)
    s = synergy_score(hero_id, ally_ids)
    wr = store.hero_winrate.get(hero_id, 0.50)
    w_diff = wr - 0.50

    w_m = store.combiner_weights.get('matchup', 1.5604)
    w_s = store.combiner_weights.get('synergy', 1.5120)
    w_w = store.combiner_weights.get('winrate', 0.9607)
    w_p = store.combiner_weights.get('model', 2.2110)
    w_emb = store.combiner_weights.get('embedding', 0.0)
    has_emb = store.combiner_weights.get('has_embedding', False)

    if engine == "ml":
        return compute_model_win_prob(hero_id, enemy_ids, ally_ids)

    if engine == "heuristic" or store.ml_model is None:
        score = w_m * m + w_s * s + w_w * w_diff
        if abs(m) < 0.005:
            score -= 0.02
        return score

    p_model = compute_model_win_prob(hero_id, enemy_ids, ally_ids)
    score = (w_m * m) + (w_s * s) + (w_w * w_diff) + (w_p * (p_model - 0.50))
    if has_emb and store.embedding_model is not None and w_emb != 0.0:
        p_emb = compute_embedding_win_prob(hero_id, enemy_ids, ally_ids)
        score += w_emb * (p_emb - 0.50)
    return score


def build_reasons_and_details(
    hero_id: int,
    enemy_ids: List[int],
    enemy_names: List[str],
    ally_ids: List[int],
    ally_names: List[str],
    target_role: str = None
) -> Tuple[List[str], List[dict], str, int, str]:
    reasons: List[str] = []
    details: List[dict] = []
    hero_name = store.id_to_name.get(hero_id, "This hero")
    bl = store.hero_avg_matchup.get(hero_id, 0.50)

    # Determine role context for this hero
    h_roles = get_roles(hero_id)
    if target_role:
        hero_role = target_role
    elif ally_ids:
        missing = infer_missing_roles(ally_ids)
        overlap = [r for r in missing if r in h_roles]
        hero_role = overlap[0] if overlap else (missing[0] if missing else (h_roles[0] if h_roles else "support"))
    else:
        hero_role = h_roles[0] if h_roles else "support"

    role_fit = explain_role_fit(hero_name, hero_role, ally_names)

    counters = []
    neutral = []
    for eid, ename in zip(enemy_ids, enemy_names):
        raw = store.matchup_matrix.get((hero_id, eid))
        if raw is None:
            rev = store.matchup_matrix.get((eid, hero_id))
            raw = (1.0 - rev) if rev is not None else bl
        adj = raw - bl
        sample_size = store.matchup_samples.get((hero_id, eid), store.matchup_samples.get((eid, hero_id), 0))
        confidence, _ = compute_posterior_confidence(games=sample_size, raw_rate=raw, prior=bl)

        is_known_counter = (hero_name, ename) in SPECIFIC_COUNTERS
        if adj >= 0.01 or is_known_counter:
            counters.append((ename, adj, sample_size, confidence))
        else:
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
    elif neutral and enemy_ids:
        primary_confidence = neutral[0][3]
        primary_sample_size = neutral[0][2]
        for name, adj, sample_size, conf in neutral[:2]:
            if adj >= 0.0:
                summary_str = f"Counters {name} ({adj:+.1%} WR, {sample_size} games)" if sample_size > 0 else f"Counters {name} ({adj:+.1%} WR)"
            else:
                summary_str = f"Matchup vs {name} ({adj:+.1%} WR, {sample_size} games)" if sample_size > 0 else f"Matchup vs {name} ({adj:+.1%} WR)"
            reasons.append(summary_str)
            explanation = explain_counter(hero_name, name, adj)
            explanation["summary"] = summary_str
            explanation["sample_size"] = sample_size
            explanation["confidence"] = conf
            details.append(explanation)
    else:
        # No enemies provided: primary reason is role fit & disables/mobility
        reasons.append(role_fit["summary"])
        details.append(role_fit)
        primary_confidence = "high"

    # Evaluate synergies with allies
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
        is_known_syn = (hero_name, aname) in SPECIFIC_SYNERGIES or (aname, hero_name) in SPECIFIC_SYNERGIES
        if adj >= 0.01 or is_known_syn:
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

    # Ensure role_fit is included in details when enemies were present so tactical breakdown is always complete
    if enemy_ids and role_fit not in details:
        details.append(role_fit)

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
            "sample_size": int(round(primary_sample_size)) if primary_sample_size else 0,
            "confidence": "high"
        })

    # Determine punchy tactical one-liner explanation
    # If 4 allies are given (filling final missing role) or explicit target_role is requested (like Mid tab),
    # prioritize the role-fit one-liner explaining their role, stuns/disables, and movement.
    if len(ally_ids) == 4 or (target_role and target_role != "all"):
        one_liner = role_fit["one_liner"]
    else:
        counter_details = [d for d in details if d.get("reason_type") == "counter" and d.get("one_liner")]
        if counter_details:
            one_liner = counter_details[0]["one_liner"]
        elif role_fit.get("one_liner"):
            one_liner = role_fit["one_liner"]
        elif details:
            one_liner = details[0].get("one_liner") or details[0].get("how_and_why", "").split(". ")[0].strip() + "."
        else:
            overview = get_hero_overview(hero_name)
            one_liner = f"{hero_name}: {overview.split('.')[0].strip()}."

    if not one_liner:
        overview = get_hero_overview(hero_name)
        one_liner = f"{hero_name}: {overview.split('.')[0].strip()}."

    return reasons, details, primary_confidence, primary_sample_size, one_liner
