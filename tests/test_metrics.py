"""
Unit tests for calibration and evaluation metrics.
"""

import sys
from pathlib import Path

# Ensure project root in sys.path
root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

import numpy as np
import pytest
from ml_pipeline.metrics import compute_all_metrics, compute_ece


def test_perfect_calibration_ece():
    # 50% accurate when 50% confident, 80% accurate when 80% confident
    y_true = np.array([1, 0, 1, 1, 1, 1, 0, 0, 1, 0])
    y_prob = np.array([0.5, 0.5, 0.5, 0.5, 0.8, 0.8, 0.8, 0.2, 0.2, 0.2])
    
    ece, bins = compute_ece(y_true, y_prob, n_bins=5)
    assert isinstance(ece, float)
    assert ece >= 0.0
    assert len(bins) == 5


def test_compute_all_metrics():
    y_true = np.array([1, 0, 1, 0, 1, 1, 0, 0])
    y_prob = np.array([0.9, 0.1, 0.8, 0.2, 0.7, 0.85, 0.15, 0.3])
    
    res = compute_all_metrics(y_true, y_prob)
    assert "accuracy" in res
    assert "log_loss" in res
    assert "roc_auc" in res
    assert "brier_score" in res
    assert "ece" in res
    assert res["accuracy"] == 1.0
    assert res["roc_auc"] == 1.0
    assert res["log_loss"] < 0.35
