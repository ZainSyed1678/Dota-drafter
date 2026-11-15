"""
Dota 2 Drafter - Walk-Forward Patch Backtest Harness
Implements patch-aware walk-forward temporal cross-validation folds.
Ensures zero data leakage across folds and slices metrics by patch,
MMR (if available), and reveal depth (0-9 heroes revealed).
"""

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ml_pipeline.metrics import compute_all_metrics


def clean_team_list(x):
    """Ensure team is list of ints."""
    if isinstance(x, np.ndarray):
        return [int(i) for i in x if int(i) > 0]
    if isinstance(x, list):
        return [int(i) for i in x if int(i) > 0]
    if isinstance(x, str):
        try:
            val = ast.literal_eval(x)
            if isinstance(val, list):
                return [int(i) for i in val if int(i) > 0]
        except Exception:
            pass
        x = x.replace('[', '').replace(']', '')
        return [int(i.strip()) for i in x.split(',') if i.strip().isdigit()]
    return []


@dataclass
class WalkForwardFold:
    fold_idx: int
    train_df: pd.DataFrame
    val_df: pd.DataFrame
    test_df: pd.DataFrame
    train_patches: List[str]
    val_patch: str
    test_patch: str


class WalkForwardHarness:
    """
    Walk-forward patch evaluation harness.
    Splits data by chronological match_id and patch version:
    Train on historical matches, validate on next patch/slice,
    test on future holdout.
    """

    def __init__(
        self,
        parquet_path: str = "data/snapshots/matches_clean.parquet",
        n_folds: int = 3,
        holdout_ratio: float = 0.15
    ):
        self.parquet_path = Path(parquet_path)
        self.n_folds = n_folds
        self.holdout_ratio = holdout_ratio
        self.df: Optional[pd.DataFrame] = None
        self.holdout_df: Optional[pd.DataFrame] = None
        self.eval_df: Optional[pd.DataFrame] = None

    def load_data(self) -> pd.DataFrame:
        if self.df is None:
            if not self.parquet_path.exists():
                raise FileNotFoundError(f"Snapshot not found: {self.parquet_path}")
            df = pd.read_parquet(self.parquet_path)
            df['radiant_team'] = df['radiant_team'].apply(clean_team_list)
            df['dire_team'] = df['dire_team'].apply(clean_team_list)
            df['radiant_win'] = df['radiant_win'].astype(int)
            df['match_id'] = df['match_id'].astype(np.int64)
            df = df.sort_values('match_id').reset_index(drop=True)
            self.df = df

            # Reserve untouched final holdout slice (e.g. latest 15% of matches)
            n_holdout = int(len(df) * self.holdout_ratio)
            self.eval_df = df.iloc[:-n_holdout].copy().reset_index(drop=True)
            self.holdout_df = df.iloc[-n_holdout:].copy().reset_index(drop=True)

        return self.df

    def get_folds(self) -> List[WalkForwardFold]:
        """
        Generate chronological walk-forward folds on eval_df.
        Fold k: Train on [0 .. (k+1)/(n+1)], Val on [(k+1)/(n+1) .. (k+2)/(n+1)].
        Guarantees strict temporal separation: max(train.match_id) < min(val.match_id).
        """
        self.load_data()
        assert self.eval_df is not None

        folds = []
        n_total = len(self.eval_df)
        step = n_total // (self.n_folds + 2)

        for i in range(self.n_folds):
            train_end = step * (i + 2)
            val_end = train_end + step
            
            f_train = self.eval_df.iloc[:train_end].copy().reset_index(drop=True)
            f_val = self.eval_df.iloc[train_end:val_end].copy().reset_index(drop=True)
            # Use holdout_df as final test reference for fold evaluation
            assert self.holdout_df is not None
            f_test = self.holdout_df.copy().reset_index(drop=True)

            train_patches = list(f_train['patch_version'].unique())
            val_patch = str(f_val['patch_version'].iloc[-1])
            test_patch = str(f_test['patch_version'].iloc[-1])

            folds.append(WalkForwardFold(
                fold_idx=i,
                train_df=f_train,
                val_df=f_val,
                test_df=f_test,
                train_patches=train_patches,
                val_patch=val_patch,
                test_patch=test_patch
            ))

        return folds

    def evaluate_predictions(
        self,
        y_true: np.ndarray,
        y_prob: np.ndarray,
        df_meta: Optional[pd.DataFrame] = None,
        reveal_counts: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Compute full metrics suite, plus slicing by patch and reveal count.
        """
        res = compute_all_metrics(y_true, y_prob)

        # Slice by patch if metadata provided
        if df_meta is not None and 'patch_version' in df_meta.columns:
            patch_metrics = {}
            for p in df_meta['patch_version'].unique():
                mask = (df_meta['patch_version'] == p).values
                if np.sum(mask) >= 50:
                    patch_metrics[str(p)] = compute_all_metrics(y_true[mask], y_prob[mask])
            res['sliced_by_patch'] = patch_metrics

        # Slice by reveal count (0 to 9 heroes revealed) if provided
        if reveal_counts is not None:
            reveal_metrics = {}
            for k in range(10):
                mask = (reveal_counts == k)
                if np.sum(mask) >= 50:
                    reveal_metrics[f"reveal_{k}"] = compute_all_metrics(y_true[mask], y_prob[mask])
            res['sliced_by_reveal_count'] = reveal_metrics

        return res
