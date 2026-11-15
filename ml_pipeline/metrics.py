"""
Dota 2 Drafter - Model Calibration & Evaluation Metrics
Provides functions to compute Log-Loss, Brier Score, ROC-AUC, and
Expected Calibration Error (ECE) with reliability curve bins.
"""

from typing import Any, Dict, List, Tuple
import numpy as np
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score


def compute_ece(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 15
) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Compute Expected Calibration Error (ECE) and reliability curve data.
    
    ECE = sum_{m=1}^M (|B_m| / N) * |acc(B_m) - conf(B_m)|
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_prob = np.asarray(y_prob, dtype=np.float64)
    
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_indices = np.digitize(y_prob, bin_edges[1:-1])  # 0 to n_bins - 1
    
    n_samples = len(y_prob)
    if n_samples == 0:
        return 0.0, []
    
    ece = 0.0
    reliability_bins = []
    
    for i in range(n_bins):
        mask = bin_indices == i
        bin_count = int(np.sum(mask))
        if bin_count > 0:
            bin_acc = float(np.mean(y_true[mask]))
            bin_conf = float(np.mean(y_prob[mask]))
            abs_err = abs(bin_acc - bin_conf)
            ece += (bin_count / n_samples) * abs_err
            
            reliability_bins.append({
                "bin": i,
                "range": [round(float(bin_edges[i]), 4), round(float(bin_edges[i + 1]), 4)],
                "count": bin_count,
                "accuracy": round(bin_acc, 4),
                "confidence": round(bin_conf, 4),
                "error": round(abs_err, 4)
            })
        else:
            reliability_bins.append({
                "bin": i,
                "range": [round(float(bin_edges[i]), 4), round(float(bin_edges[i + 1]), 4)],
                "count": 0,
                "accuracy": None,
                "confidence": None,
                "error": 0.0
            })
            
    return float(ece), reliability_bins


def compute_all_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 15
) -> Dict[str, Any]:
    """Compute complete suite of draft prediction evaluation metrics."""
    y_true = np.asarray(y_true, dtype=np.int32)
    y_prob = np.clip(np.asarray(y_prob, dtype=np.float64), 1e-7, 1.0 - 1e-7)
    
    acc = float(accuracy_score(y_true, y_prob >= 0.5))
    ll = float(log_loss(y_true, y_prob))
    roc = float(roc_auc_score(y_true, y_prob))
    brier = float(brier_score_loss(y_true, y_prob))
    ece, reliability = compute_ece(y_true, y_prob, n_bins=n_bins)
    
    return {
        "accuracy": round(acc, 4),
        "log_loss": round(ll, 4),
        "roc_auc": round(roc, 4),
        "brier_score": round(brier, 4),
        "ece": round(ece, 4),
        "reliability_bins": reliability
    }
