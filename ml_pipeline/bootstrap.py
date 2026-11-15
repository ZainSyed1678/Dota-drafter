"""
Dota 2 Drafter - Paired Bootstrap Hypothesis Testing & Confidence Intervals
Computes non-parametric paired bootstrap 95% confidence intervals on metric differences
(Log Loss, Brier Score, ROC-AUC) between candidate models and the baseline.
"""

from typing import Any, Dict, Optional
import numpy as np
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score


def compute_paired_bootstrap_ci(
    y_true: np.ndarray,
    prob_baseline: np.ndarray,
    prob_candidate: np.ndarray,
    n_bootstraps: int = 1000,
    alpha: float = 0.05,
    metric: str = "log_loss",
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Compute paired bootstrap difference CI: Delta = Metric(Candidate) - Metric(Baseline).
    
    For Log Loss and Brier Score:
      Delta < 0 indicates Candidate is better than Baseline.
      Statistically significant improvement requires CI upper < 0 (CI excludes zero).
    
    For ROC-AUC:
      Delta > 0 indicates Candidate is better than Baseline.
      Statistically significant improvement requires CI lower > 0 (CI excludes zero).
    """
    y_true = np.asarray(y_true, dtype=np.int32)
    p_base = np.clip(np.asarray(prob_baseline, dtype=np.float64), 1e-7, 1.0 - 1e-7)
    p_cand = np.clip(np.asarray(prob_candidate, dtype=np.float64), 1e-7, 1.0 - 1e-7)
    
    n_samples = len(y_true)
    rng = np.random.RandomState(random_state)
    
    def calc_metric(y, p):
        if metric == "log_loss":
            return log_loss(y, p)
        elif metric == "brier":
            return brier_score_loss(y, p)
        elif metric == "roc_auc":
            return roc_auc_score(y, p)
        else:
            raise ValueError(f"Unsupported metric: {metric}")

    base_point = calc_metric(y_true, p_base)
    cand_point = calc_metric(y_true, p_cand)
    point_diff = cand_point - base_point

    diffs = np.zeros(n_bootstraps, dtype=np.float64)

    for b in range(n_bootstraps):
        boot_idx = rng.randint(0, n_samples, size=n_samples)
        y_b = y_true[boot_idx]
        # In case all labels in bootstrap sample are identical for ROC-AUC
        if metric == "roc_auc" and len(np.unique(y_b)) < 2:
            diffs[b] = 0.0
            continue
        m_base = calc_metric(y_b, p_base[boot_idx])
        m_cand = calc_metric(y_b, p_cand[boot_idx])
        diffs[b] = m_cand - m_base

    lower_pct = 100.0 * (alpha / 2.0)
    upper_pct = 100.0 * (1.0 - alpha / 2.0)
    ci_lower = float(np.percentile(diffs, lower_pct))
    ci_upper = float(np.percentile(diffs, upper_pct))
    diff_std = float(np.std(diffs))

    # Two-sided empirical p-value for H0: diff == 0
    if metric in ("log_loss", "brier"):
        # Improvement means diff < 0
        p_val = float(np.mean(diffs >= 0))
        is_sig = bool(ci_upper < 0.0)
    else:
        # Improvement means diff > 0
        p_val = float(np.mean(diffs <= 0))
        is_sig = bool(ci_lower > 0.0)

    return {
        "metric": metric,
        "n_bootstraps": n_bootstraps,
        "baseline_metric": round(float(base_point), 5),
        "candidate_metric": round(float(cand_point), 5),
        "diff_mean": round(float(point_diff), 5),
        "diff_std": round(diff_std, 5),
        "ci_lower": round(ci_lower, 5),
        "ci_upper": round(ci_upper, 5),
        "p_value": round(p_val, 4),
        "is_significant_improvement": is_sig,
        "excludes_zero": bool(ci_lower > 0 or ci_upper < 0)
    }
