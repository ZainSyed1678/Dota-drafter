"""Tests for incremental count updates and full-recompute tolerance verification."""

import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml_pipeline.incremental import DraftCountAccumulator


def generate_synthetic_matches(n_matches: int = 1000, seed: int = 42):
    rng = np.random.RandomState(seed)
    heroes = list(range(1, 128))
    matches = []
    for i in range(n_matches):
        team1 = rng.choice(heroes, size=5, replace=False).tolist()
        team2 = rng.choice([h for h in heroes if h not in team1], size=5, replace=False).tolist()
        rw = bool(rng.rand() > 0.48)
        matches.append({
            "match_id": 9000000000 + i,
            "radiant_team": team1,
            "dire_team": team2,
            "radiant_win": rw
        })
    return matches


def test_incremental_matches_full_recompute_exact_tolerance():
    """Verify incremental accumulator equals full batch recompute to <1e-6 tolerance."""
    all_matches = generate_synthetic_matches(n_matches=3000, seed=42)

    # Full batch accumulation
    full_acc = DraftCountAccumulator()
    full_acc.add_batch(all_matches)
    full_m = full_acc.compute_matrices()

    # Incremental accumulation across 3 batches of 1,000
    inc_acc = DraftCountAccumulator()
    batch_size = 1000
    for start in range(0, len(all_matches), batch_size):
        chunk = all_matches[start:start + batch_size]
        inc_acc.add_batch(chunk)

    inc_m = inc_acc.compute_matrices()

    assert inc_acc.total_matches == len(all_matches)

    # Assert exact match on hero winrates
    for h, wr_full in full_m["hero_winrate"].items():
        wr_inc = inc_m["hero_winrate"][h]
        assert abs(wr_full - wr_inc) < 1e-6, f"Hero {h} mismatch: {wr_full} vs {wr_inc}"

    # Assert exact match on matchup matrix
    for pair, m_full in full_m["matchup"].items():
        m_inc = inc_m["matchup"][pair]
        assert abs(m_full - m_inc) < 1e-6, f"Matchup {pair} mismatch: {m_full} vs {m_inc}"

    # Assert exact match on synergy matrix
    for pair, s_full in full_m["synergy"].items():
        s_inc = inc_m["synergy"][pair]
        assert abs(s_full - s_inc) < 1e-6, f"Synergy {pair} mismatch: {s_full} vs {s_inc}"

    # Verification helper
    is_valid, max_diff = inc_acc.verify_against_full_recompute(all_matches, tolerance=1e-6)
    assert is_valid is True
    assert max_diff < 1e-6
