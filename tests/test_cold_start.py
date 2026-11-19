"""Tests for patch cold start prior blending, patch boundary weighting, and retrain cadence."""

import datetime
import math
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml_pipeline.cold_start import (
    compute_cold_start_prior_blend,
    compute_patch_aware_weight,
    get_recommended_retrain_cadence
)


def test_cold_start_prior_blending_transitions():
    """Verify smooth exponential decay of prior weight from 1.0 to 0.0 as samples accumulate."""
    prev_posterior = 0.62
    global_prior = 0.50
    tau = 50.0

    # 1. Zero games: completely relies on previous patch posterior
    blended_0, w_0 = compute_cold_start_prior_blend(
        new_patch_wins=0,
        new_patch_games=0,
        prev_patch_winrate=prev_posterior,
        global_prior=global_prior,
        tau_games=tau
    )
    assert blended_0 == prev_posterior
    assert w_0 == 1.0

    # 2. At tau = 50 games: prior weight is exp(-1) ~ 0.36788
    # Suppose new patch is 15 wins out of 50 games (winrate 30%)
    blended_50, w_50 = compute_cold_start_prior_blend(
        new_patch_wins=15,
        new_patch_games=50,
        prev_patch_winrate=prev_posterior,
        global_prior=global_prior,
        k_shrink=10.0,
        tau_games=tau
    )
    assert abs(w_50 - math.exp(-1.0)) < 1e-4
    # Blended winrate must be between new patch estimate and previous patch
    raw_new_50 = (15 + 10.0 * 0.5) / 60.0  # 20/60 = 0.3333
    expected_50 = (1.0 - w_50) * raw_new_50 + w_50 * prev_posterior
    assert abs(blended_50 - expected_50) < 1e-4

    # 3. High sample size (500 games): prior weight approaches 0
    blended_500, w_500 = compute_cold_start_prior_blend(
        new_patch_wins=150,
        new_patch_games=500,
        prev_patch_winrate=prev_posterior,
        global_prior=global_prior,
        tau_games=tau
    )
    assert w_500 < 1e-4
    assert abs(blended_500 - (150 + 5.0) / 510.0) < 0.01


def test_patch_boundary_penalty():
    """Verify that matches from old patches receive steep boundary discounting."""
    active_patch = "7.36"
    old_patch = "7.35"
    days = 2.0
    lambda_decay = 0.20
    penalty = 0.25

    w_active = compute_patch_aware_weight(active_patch, active_patch, days, lambda_decay, penalty)
    w_old = compute_patch_aware_weight(old_patch, active_patch, days, lambda_decay, penalty)

    expected_active = math.exp(-0.20 * 2.0)
    expected_old = expected_active * 0.25

    assert abs(w_active - expected_active) < 1e-5
    assert abs(w_old - expected_old) < 1e-5
    assert w_old == pytest.approx(w_active * penalty)


def test_post_patch_burst_cadence():
    """Verify retrain schedule adjusts to daily burst during the first 3 days after a patch."""
    patch_date = datetime.date(2026, 11, 15)

    # Day 1: within burst period
    c1 = get_recommended_retrain_cadence(
        patch_release_date=patch_date,
        current_date=datetime.date(2026, 11, 16),
        normal_interval_days=3,
        post_patch_burst_days=3,
        post_patch_interval_days=1
    )
    assert c1["is_burst_period"] is True
    assert c1["cadence_days"] == 1
    assert c1["schedule_mode"] == "burst_daily"

    # Day 5: after burst period
    c5 = get_recommended_retrain_cadence(
        patch_release_date=patch_date,
        current_date=datetime.date(2026, 11, 20),
        normal_interval_days=3,
        post_patch_burst_days=3,
        post_patch_interval_days=1
    )
    assert c5["is_burst_period"] is False
    assert c5["cadence_days"] == 3
    assert c5["schedule_mode"] == "normal_3day"
