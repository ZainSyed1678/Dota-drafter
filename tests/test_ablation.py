"""
Unit tests for combiner ablation components.
"""

import sys
from pathlib import Path
import numpy as np
import pytest

root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from sklearn.linear_model import LogisticRegression
from ml_pipeline.bootstrap import compute_paired_bootstrap_ci


def test_ablation_logic_synthetic():
    np.random.seed(42)
    n = 300
    y = np.random.binomial(1, 0.5, size=n)
    
    # 4 synthetic features: M, S, W, P
    M = np.random.normal(0, 1, size=(n, 1)) + y.reshape(-1, 1) * 0.5
    S = np.random.normal(0, 1, size=(n, 1)) + y.reshape(-1, 1) * 0.3
    W = np.random.normal(0, 1, size=(n, 1)) + y.reshape(-1, 1) * 0.2
    P = np.random.normal(0, 1, size=(n, 1)) + y.reshape(-1, 1) * 0.8
    
    full_X = np.hstack([M, S, W, P])
    drop_m_X = np.hstack([S, W, P])
    
    clf_full = LogisticRegression().fit(full_X[:200], y[:200])
    clf_drop = LogisticRegression().fit(drop_m_X[:200], y[:200])
    
    prob_full = clf_full.predict_proba(full_X[200:])[:, 1]
    prob_drop = clf_drop.predict_proba(drop_m_X[200:])[:, 1]
    
    res = compute_paired_bootstrap_ci(y[200:], prob_full, prob_drop, n_bootstraps=200)
    assert "diff_mean" in res
    assert "ci_lower" in res
    assert "ci_upper" in res
