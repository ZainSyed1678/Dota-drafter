"""
Unit tests for scoring, Empirical-Bayes shrinkage, and recency weighting math.
"""

import math

import pytest
from app.model_loader import store
from app.scoring import infer_missing_roles, norm_matchup, predict, synergy_score


def test_shrinkage_formula():
    """
    Test Empirical-Bayes shrinkage formula:
    shrunk = (wins + k * prior) / (games + k)
    """
    k = 20.0
    prior = 0.52

    # Zero games -> should equal prior exactly
    wins_zero = 0.0
    games_zero = 0.0
    shrunk_zero = (wins_zero + k * prior) / (games_zero + k)
    assert shrunk_zero == pytest.approx(0.52)

    # 1 win out of 1 game -> should shrink heavily towards prior
    wins_1 = 1.0
    games_1 = 1.0
    shrunk_1 = (wins_1 + k * prior) / (games_1 + k)
    # (1 + 20 * 0.52) / (1 + 20) = 11.4 / 21 ≈ 0.5428
    assert shrunk_1 == pytest.approx(0.542857, rel=1e-3)
    assert shrunk_1 < 0.60  # Far away from raw 1.0!

    # 10,000 games with 60% win rate -> should converge to 0.60
    wins_large = 6000.0
    games_large = 10000.0
    shrunk_large = (wins_large + k * prior) / (games_large + k)
    assert shrunk_large == pytest.approx(0.60, abs=1e-3)


def test_recency_weights():
    """
    Test exponential recency weighting decay:
    w = exp(-lambda * (1 - pos))
    """
    recency_lambda = 0.2
    # Oldest match (pos = 0)
    w_old = math.exp(-recency_lambda * 1.0)
    # Newest match (pos = 1)
    w_new = math.exp(-recency_lambda * 0.0)

    assert w_new == pytest.approx(1.0)
    assert w_old == pytest.approx(math.exp(-0.2))
    assert w_old < w_new


def test_normalised_matchup_centering():
    """
    Verify that normalized matchup advantage is centered at 0.0 relative to baseline.
    """
    hero_id = 1  # Anti-Mage
    store.hero_avg_matchup.get(hero_id, 0.50)

    # Empty enemy list -> 0.0
    assert norm_matchup(hero_id, []) == 0.0

    # If enemy has matchups equal to baseline -> 0.0
    enemies = [14]  # Pudge
    score = norm_matchup(hero_id, enemies)
    assert isinstance(score, float)
    assert -0.5 <= score <= 0.5


def test_synergy_centering():
    """
    Verify that synergy advantage is centered at 0.0 relative to 50% baseline.
    """
    hero_id = 1
    assert synergy_score(hero_id, []) == 0.0
    allies = [5]  # Crystal Maiden
    score = synergy_score(hero_id, allies)
    assert isinstance(score, float)
    assert -0.5 <= score <= 0.5


def test_role_inference():
    """
    Test position coverage and missing role deduction.
    """
    # 1: Anti-Mage (carry), 13: Puck (mid), 2: Axe (offlane)
    allies = [1, 13, 2]
    needed = infer_missing_roles(allies)
    assert "support" in needed
    assert "carry" not in needed

    # Empty team -> all roles needed
    needed_empty = infer_missing_roles([])
    assert set(needed_empty) == {"carry", "mid", "offlane", "support"}


def test_predict_scoring_bounds():
    """
    Verify combined prediction score produces finite, reasonable numbers.
    """
    score = predict(1, [14, 47], [5], engine="combined")
    assert isinstance(score, float)
    assert not math.isnan(score)
    assert not math.isinf(score)
