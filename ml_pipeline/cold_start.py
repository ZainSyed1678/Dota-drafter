"""Patch cold-start prior blending, patch-age-aware weighting, and retrain cadence.

1. Prior Blending:
   Blends new-patch empirical matrix with previous patch posterior:
   w_prior = exp(-N_games / tau)
   M_blended = (1 - w_prior) * M_new + w_prior * M_prev

2. Patch-Age-Aware Weighting:
   Discounts or resets recency weight across patch boundaries to prevent old-patch meta
   from contaminating a fresh patch.

3. Post-Patch Retrain Cadence:
   Configurable burst schedule (e.g. daily for first 3 days after patch drop, then every 3 days).
"""

import sys
import math
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def compute_cold_start_prior_blend(
    new_patch_wins: float,
    new_patch_games: float,
    prev_patch_winrate: float,
    global_prior: float = 0.50,
    k_shrink: float = 10.0,
    tau_games: float = 50.0
) -> Tuple[float, float]:
    """
    Compute blended matchup/synergy winrate for a hero pair during cold-start.

    Args:
        new_patch_wins: Observed wins in current patch.
        new_patch_games: Observed games in current patch.
        prev_patch_winrate: Posterior winrate from previous patch.
        global_prior: Global meta prior (default 0.50).
        k_shrink: Shrinkage pseudo-count.
        tau_games: Decay scale for prior blending.

    Returns:
        blended_winrate: Float in [0, 1].
        prior_weight: Float in [0, 1] indicating weight placed on previous patch.
    """
    if new_patch_games <= 0.0:
        return prev_patch_winrate, 1.0

    # Empirical Bayes estimate in current patch
    raw_new = (new_patch_wins + k_shrink * global_prior) / (new_patch_games + k_shrink)

    # Weight on previous patch decays exponentially with sample size
    w_prior = float(math.exp(-new_patch_games / max(1.0, tau_games)))
    blended = float((1.0 - w_prior) * raw_new + w_prior * prev_patch_winrate)

    return blended, w_prior


def compute_patch_aware_weight(
    match_patch: str,
    active_patch: str,
    days_since_match: float,
    lambda_decay: float = 0.20,
    patch_boundary_penalty: float = 0.25
) -> float:
    """
    Compute sample weight with patch boundary discount.

    If match is from an earlier patch than active_patch, applies a boundary penalty
    discounting older meta.
    """
    base_weight = math.exp(-lambda_decay * max(0.0, days_since_match))
    if match_patch != active_patch:
        # Penalize old patch data
        base_weight *= patch_boundary_penalty
    return float(base_weight)


def get_recommended_retrain_cadence(
    patch_release_date: datetime.date,
    current_date: datetime.date,
    normal_interval_days: int = 3,
    post_patch_burst_days: int = 3,
    post_patch_interval_days: int = 1
) -> Dict[str, Any]:
    """
    Determine retrain schedule based on elapsed time since latest patch drop.

    - Days 0..post_patch_burst_days: High-frequency retraining (e.g. daily)
    - Days > post_patch_burst_days: Standard cadence (e.g. every 3 days)
    """
    days_since_patch = (current_date - patch_release_date).days
    is_burst_period = 0 <= days_since_patch <= post_patch_burst_days
    interval = post_patch_interval_days if is_burst_period else normal_interval_days

    return {
        "current_date": current_date.isoformat(),
        "patch_release_date": patch_release_date.isoformat(),
        "days_since_patch": days_since_patch,
        "is_burst_period": is_burst_period,
        "cadence_days": interval,
        "schedule_mode": "burst_daily" if is_burst_period else "normal_3day"
    }
