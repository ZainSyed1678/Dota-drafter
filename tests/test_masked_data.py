"""
Unit tests for masked draft generator and feature construction.
"""

import sys
from pathlib import Path
import numpy as np
import pytest

root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from ml_pipeline.masked_data import (
    build_masked_feature_vector,
    generate_masked_draft_sample
)


def test_masked_draft_sample_bounds():
    rng = np.random.RandomState(42)
    r_team = [1, 2, 3, 4, 5]
    d_team = [6, 7, 8, 9, 10]

    for _ in range(50):
        sample = generate_masked_draft_sample(r_team, d_team, 1, rng)
        assert 0 <= sample["n_radiant"] <= 5
        assert 0 <= sample["n_dire"] <= 5
        assert 0 <= sample["total_revealed"] <= 10
        assert len(sample["revealed_radiant"]) == sample["n_radiant"]
        assert len(sample["revealed_dire"]) == sample["n_dire"]


def test_build_masked_feature_vector():
    hero_to_idx = {h: i for i, h in enumerate([1, 2, 3, 6, 7, 8])}
    hero_winrate = {h: 0.52 for h in hero_to_idx}

    feat = build_masked_feature_vector(
        revealed_radiant=[1, 2],
        revealed_dire=[6],
        hero_to_idx=hero_to_idx,
        hero_winrate=hero_winrate,
        global_prior=0.50
    )

    # 6 heroes + 7 state indicators = 13 features
    assert len(feat) == 13
    assert feat[hero_to_idx[1]] == 1.0
    assert feat[hero_to_idx[2]] == 1.0
    assert feat[hero_to_idx[6]] == -1.0
    assert feat[hero_to_idx[3]] == 0.0
    # State indicators: n_r=2, n_d=1
    assert abs(feat[6] - 2.0 / 5.0) < 1e-5
    assert abs(feat[7] - 1.0 / 5.0) < 1e-5
