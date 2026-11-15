"""
Unit tests for shrinkage tuning functions.
"""

import sys
from pathlib import Path
import numpy as np
import pytest

root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from ml_pipeline.tune_shrinkage import build_shrunk_matrices


def test_build_shrunk_matrices_bounds():
    sorted_heroes = [1, 2, 3]
    hero_wins = {1: 60.0, 2: 40.0, 3: 50.0}
    hero_games = {1: 100.0, 2: 100.0, 3: 100.0}
    matchup_wins = {(1, 2): 60.0, (2, 1): 40.0}
    matchup_games = {(1, 2): 100.0, (2, 1): 100.0}
    synergy_wins = {(1, 2): 55.0}
    synergy_games = {(1, 2): 100.0}

    h_wr, g_prior, s_matchup, s_syn = build_shrunk_matrices(
        sorted_heroes, hero_wins, hero_games, matchup_wins, matchup_games, synergy_wins, synergy_games,
        k_hero=5.0, k_matchup=10.0, k_synergy=15.0
    )

    assert 0.0 <= g_prior <= 1.0
    for h in sorted_heroes:
        assert 0.3 <= h_wr[h] <= 0.7
    assert 0.4 <= s_matchup[(1, 2)] <= 0.7
    assert 0.4 <= s_syn[(1, 2)] <= 0.6
