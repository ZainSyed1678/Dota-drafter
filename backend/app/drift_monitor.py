"""Drift and calibration monitoring for live Dota 2 Drafter predictions.

Tracks rolling prediction-vs-outcome pairs, computing:
- Rolling Log Loss
- Rolling Brier Score
- Rolling Expected Calibration Error (ECE)
- Prediction probability distribution histogram
- Prometheus metrics exposition (/metrics)
"""

from collections import deque
from typing import Dict, List, Optional, Tuple, Any
import numpy as np


class RollingDriftMonitor:
    """In-memory rolling buffer for monitoring model calibration and distribution drift."""

    def __init__(self, window_size: int = 2000):
        self.window_size = window_size
        self.history: deque = deque(maxlen=window_size)  # (predicted_prob, actual_label)
        self.prediction_history: deque = deque(maxlen=window_size)  # predicted_prob only

    def record_prediction(self, predicted_prob: float):
        """Record an outgoing prediction for distribution monitoring."""
        p = float(np.clip(predicted_prob, 0.0, 1.0))
        self.prediction_history.append(p)

    def record_match_outcome(self, predicted_prob: float, actual_win: int):
        """Record a completed match prediction and outcome."""
        p = float(np.clip(predicted_prob, 1e-7, 1.0 - 1e-7))
        y = int(actual_win)
        self.history.append((p, y))

    def compute_metrics(self) -> Dict[str, Any]:
        """Compute rolling metrics over the current buffer."""
        n_pairs = len(self.history)
        n_preds = len(self.prediction_history)

        # Prediction distribution histogram (10 bins: [0, 0.1), [0.1, 0.2), ...)
        hist_counts = [0] * 10
        if n_preds > 0:
            for p in self.prediction_history:
                bin_idx = min(9, int(p * 10.0))
                hist_counts[bin_idx] += 1

        if n_pairs < 20:
            return {
                "sample_count": n_pairs,
                "total_predictions": n_preds,
                "status": "warming_up",
                "rolling_log_loss": None,
                "rolling_brier": None,
                "rolling_ece": None,
                "drift_alert": False,
                "prediction_distribution": hist_counts
            }

        probs = np.array([p for p, _ in self.history], dtype=np.float64)
        labels = np.array([y for _, y in self.history], dtype=np.int32)

        # Log Loss
        eps = 1e-15
        p_c = np.clip(probs, eps, 1.0 - eps)
        ll = float(-np.mean(labels * np.log(p_c) + (1.0 - labels) * np.log(1.0 - p_c)))

        # Brier Score
        brier = float(np.mean((probs - labels) ** 2))

        # ECE (10 equal bins)
        bin_limits = np.linspace(0.0, 1.0, 11)
        ece = 0.0
        for i in range(10):
            mask = (probs >= bin_limits[i]) & (probs < bin_limits[i+1])
            count = int(np.sum(mask))
            if count > 0:
                acc = float(np.mean(labels[mask]))
                conf = float(np.mean(probs[mask]))
                ece += (count / n_pairs) * abs(acc - conf)

        # Drift alert triggers if Log Loss > 0.72 or ECE > 0.06
        drift_alert = bool(ll > 0.72 or ece > 0.06)

        return {
            "sample_count": n_pairs,
            "total_predictions": n_preds,
            "status": "active",
            "rolling_log_loss": round(ll, 4),
            "rolling_brier": round(brier, 4),
            "rolling_ece": round(ece, 4),
            "drift_alert": drift_alert,
            "prediction_distribution": hist_counts
        }

    def format_prometheus_metrics(self) -> str:
        """Format metrics as standard Prometheus exposition text."""
        metrics = self.compute_metrics()
        lines = [
            "# HELP dota_rolling_sample_count Number of verified match outcome pairs in rolling buffer",
            "# TYPE dota_rolling_sample_count gauge",
            f"dota_rolling_sample_count {metrics['sample_count']}",
            "# HELP dota_total_predictions_recorded Total live predictions recorded in rolling window",
            "# TYPE dota_total_predictions_recorded counter",
            f"dota_total_predictions_recorded {metrics['total_predictions']}"
        ]

        if metrics["rolling_log_loss"] is not None:
            lines.extend([
                "# HELP dota_rolling_log_loss Rolling log loss of predictions vs outcomes",
                "# TYPE dota_rolling_log_loss gauge",
                f"dota_rolling_log_loss {metrics['rolling_log_loss']}",
                "# HELP dota_rolling_brier_score Rolling Brier score of predictions vs outcomes",
                "# TYPE dota_rolling_brier_score gauge",
                f"dota_rolling_brier_score {metrics['rolling_brier']}",
                "# HELP dota_rolling_ece Rolling Expected Calibration Error (ECE)",
                "# TYPE dota_rolling_ece gauge",
                f"dota_rolling_ece {metrics['rolling_ece']}",
                "# HELP dota_drift_alert Binary indicator of calibration drift alert",
                "# TYPE dota_drift_alert gauge",
                f"dota_drift_alert {1 if metrics['drift_alert'] else 0}"
            ])

        # Prediction distribution histogram buckets
        lines.append("# HELP dota_prediction_probability_bucket Histogram of predicted probabilities")
        lines.append("# TYPE dota_prediction_probability_bucket histogram")
        cumulative = 0
        for i, count in enumerate(metrics["prediction_distribution"]):
            upper = round((i + 1) * 0.1, 1)
            cumulative += count
            lines.append(f'dota_prediction_probability_bucket{{le="{upper}"}} {cumulative}')
        lines.append(f'dota_prediction_probability_bucket{{le="+Inf"}} {metrics["total_predictions"]}')
        lines.append(f'dota_prediction_probability_count {metrics["total_predictions"]}')

        return "\n".join(lines) + "\n"


# Global singleton instance for live service
drift_monitor = RollingDriftMonitor()
