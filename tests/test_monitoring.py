"""Tests for drift and calibration monitoring, Prometheus metrics, and shadow logging."""

import sys
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app
from app.config import settings
from app.drift_monitor import RollingDriftMonitor, drift_monitor
from app.scoring import predict

client = TestClient(app)


def test_drift_monitor_warmup_and_active_metrics():
    """Verify monitor handles warmup state and accurately computes calibration metrics once populated."""
    mon = RollingDriftMonitor(window_size=100)

    # 1. Warmup state (<20 samples, 50% winrate)
    for i in range(10):
        mon.record_prediction(0.50)
        mon.record_match_outcome(0.50, 1 if i % 2 == 0 else 0)

    m_warm = mon.compute_metrics()
    assert m_warm["status"] == "warming_up"
    assert m_warm["rolling_log_loss"] is None

    # 2. Add remaining to reach 50 well-calibrated samples (50% wins at p=0.50)
    for i in range(40):
        mon.record_prediction(0.50)
        mon.record_match_outcome(0.50, 1 if i % 2 == 0 else 0)

    m_active = mon.compute_metrics()
    assert m_active["status"] == "active"
    assert m_active["sample_count"] == 50
    assert m_active["rolling_log_loss"] is not None
    assert m_active["rolling_brier"] is not None
    assert m_active["rolling_ece"] is not None
    assert m_active["drift_alert"] is False

    # 3. Trigger drift alert by feeding severe miscalibration
    for _ in range(80):
        mon.record_prediction(0.99)
        mon.record_match_outcome(0.99, 0)  # Extreme mismatch

    m_drift = mon.compute_metrics()
    assert m_drift["drift_alert"] is True


def test_prometheus_formatting_exposition():
    """Verify prometheus formatted text contains expected metric names and histogram buckets."""
    mon = RollingDriftMonitor(window_size=100)
    for p in [0.25, 0.45, 0.65, 0.85]:
        mon.record_prediction(p)
        mon.record_match_outcome(p, 1)

    text = mon.format_prometheus_metrics()
    assert "dota_rolling_sample_count 4" in text
    assert "dota_total_predictions_recorded 4" in text
    assert 'dota_prediction_probability_bucket{le="0.3"}' in text
    assert 'dota_prediction_probability_bucket{le="+Inf"}' in text


def test_metrics_api_endpoints():
    """Verify /metrics and /monitoring/drift endpoints return expected content."""
    # Seed singleton drift_monitor so gauges have active values
    for i in range(30):
        drift_monitor.record_prediction(0.50)
        drift_monitor.record_match_outcome(0.50, 1 if i % 2 == 0 else 0)

    res_m = client.get("/metrics")
    assert res_m.status_code == 200
    assert "text/plain" in res_m.headers["content-type"]
    assert "dota_rolling_log_loss" in res_m.text

    res_d = client.get("/monitoring/drift")
    assert res_d.status_code == 200
    data = res_d.json()
    assert "sample_count" in data
    assert "status" in data
    assert "prediction_distribution" in data


def test_shadow_prediction_execution():
    """Verify shadow prediction hook runs safely when enabled without altering primary score."""
    orig_shadow = settings.ENABLE_SHADOW_LOGGING
    try:
        settings.ENABLE_SHADOW_LOGGING = True
        score_shadow = predict(1, [2, 3], [4, 5])

        settings.ENABLE_SHADOW_LOGGING = False
        score_normal = predict(1, [2, 3], [4, 5])

        assert abs(score_shadow - score_normal) < 1e-6
    finally:
        settings.ENABLE_SHADOW_LOGGING = orig_shadow
