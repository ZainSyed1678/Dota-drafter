"""
Unit tests for paired bootstrap confidence intervals.
"""

import sys
from pathlib import Path
import numpy as np
import pytest

root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from ml_pipeline.bootstrap import compute_paired_bootstrap_ci


def test_bootstrap_significant_improvement():
    np.random.seed(42)
    n = 200
    y_true = np.random.binomial(1, 0.5, size=n)
    
    # Candidate clearly better than baseline
    prob_base = np.full(n, 0.5)
    prob_cand = np.where(y_true == 1, 0.85, 0.15)
    
    res = compute_paired_bootstrap_ci(
        y_true=y_true,
        prob_baseline=prob_base,
        prob_candidate=prob_cand,
        n_bootstraps=500,
        metric="log_loss"
    )
    
    assert res["metric"] == "log_loss"
    assert res["diff_mean"] < 0
    assert res["ci_upper"] < 0
    assert res["is_significant_improvement"] is True
    assert res["excludes_zero"] is True


def test_bootstrap_non_significant():
    np.random.seed(42)
    n = 100
    y_true = np.random.binomial(1, 0.5, size=n)
    prob_base = np.random.uniform(0.4, 0.6, size=n)
    # Practically identical predictions
    prob_cand = prob_base + np.random.normal(0, 0.005, size=n)
    
    res = compute_paired_bootstrap_ci(
        y_true=y_true,
        prob_baseline=prob_base,
        prob_candidate=prob_cand,
        n_bootstraps=300,
        metric="log_loss"
    )
    
    assert res["is_significant_improvement"] is False
    assert res["ci_lower"] <= 0 <= res["ci_upper"]
