"""
Unit tests for adaptive shrinkage calculations.
"""

import sys
from pathlib import Path
import pytest

root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from ml_pipeline.adaptive_shrinkage import (
    compute_adaptive_matchup_shrinkage,
    compute_adaptive_synergy_shrinkage
)


def test_adaptive_shrinkage_behavior():
    matchup_games = {
        (1, 2): 10.0,     # Sparse pair
        (1, 3): 5000.0,   # Very dense pair
    }
    matchup_wins = {
        (1, 2): 8.0,      # 80% empirical in 10 games
        (1, 3): 2750.0,   # 55% empirical in 5000 games
    }
    hero_winrate = {1: 0.50, 2: 0.50, 3: 0.50}

    shrunk, k_mat = compute_adaptive_matchup_shrinkage(
        matchup_wins, matchup_games, hero_winrate, global_prior=0.50, base_k=20.0
    )

    # Sparse pair should have higher effective k (heavier shrinkage toward 0.50)
    assert k_mat[(1, 2)] > k_mat[(1, 3)]
    # Dense pair should be very close to empirical 55% (2750/5000 = 0.55)
    assert abs(shrunk[(1, 3)] - 0.55) < 0.005
    # Sparse pair should be shrunk noticeably toward prior 0.50 away from 0.80
    assert shrunk[(1, 2)] < 0.70
