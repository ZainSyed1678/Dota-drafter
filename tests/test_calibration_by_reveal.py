"""
Unit tests verifying model calibration by draft reveal depth (0 to 10 heroes revealed).
"""

import sys
from pathlib import Path
import json
import numpy as np
import pytest

root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from ml_pipeline.metrics import compute_all_metrics


def test_reveal_count_calibration_monotonicity():
    """
    Test that masked model evaluation metadata shows valid calibration
    (ECE < 0.05) and general error reduction as more heroes are revealed.
    """
    meta_path = root_path / "backend" / "model" / "v2026.11.15-masked" / "metadata.json"
    assert meta_path.exists(), "Masked model metadata.json not found"

    with open(meta_path, "r") as f:
        meta = json.load(f)

    reveal_metrics = meta.get("sliced_by_reveal", {})
    assert len(reveal_metrics) >= 8, "Expected at least 8 reveal depth slices"

    # Verify each reveal slice is well-calibrated (ECE < 0.05)
    for rev_key, m in reveal_metrics.items():
        assert m["ece"] < 0.05, f"{rev_key} ECE too high: {m['ece']}"
        assert 0.60 <= m["log_loss"] <= 0.72, f"{rev_key} log_loss abnormal: {m['log_loss']}"

    # Verify 10-hero draft has lower log loss than 0-hero draft
    if "reveal_0" in reveal_metrics and "reveal_10" in reveal_metrics:
        ll_0 = reveal_metrics["reveal_0"]["log_loss"]
        ll_10 = reveal_metrics["reveal_10"]["log_loss"]
        assert ll_10 < ll_0, f"Expected 10-hero log loss ({ll_10}) < 0-hero log loss ({ll_0})"
