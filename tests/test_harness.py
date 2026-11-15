"""
Unit tests for walk-forward evaluation harness.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from ml_pipeline.harness import WalkForwardHarness


def test_walk_forward_temporal_invariance(tmp_path):
    # Create synthetic parquet dataset with strict chronological match_ids
    data = []
    for i in range(1000):
        data.append({
            "match_id": 100000 + i,
            "radiant_win": bool(i % 2 == 0),
            "radiant_team": [1, 2, 3, 4, 5],
            "dire_team": [6, 7, 8, 9, 10],
            "patch_version": "7.35d" if i < 400 else "7.35f"
        })
    df = pd.DataFrame(data)
    test_pq = tmp_path / "test_matches.parquet"
    df.to_parquet(test_pq, index=False)

    harness = WalkForwardHarness(parquet_path=str(test_pq), n_folds=2, holdout_ratio=0.15)
    folds = harness.get_folds()

    assert len(folds) == 2
    for fold in folds:
        max_tr = fold.train_df['match_id'].max()
        min_val = fold.val_df['match_id'].min()
        max_val = fold.val_df['match_id'].max()
        min_test = fold.test_df['match_id'].min()

        # Strict chronological ordering
        assert max_tr < min_val, f"Leakage: Train overlaps Val in fold {fold.fold_idx}"
        assert max_val < min_test, f"Leakage: Val overlaps Test in fold {fold.fold_idx}"

        # No set overlap
        assert len(set(fold.train_df['match_id']) & set(fold.val_df['match_id'])) == 0
        assert len(set(fold.train_df['match_id']) & set(fold.test_df['match_id'])) == 0
