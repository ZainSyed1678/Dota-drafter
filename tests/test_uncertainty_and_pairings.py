"""Tests for uncertainty intervals and data-grounded explanations payload."""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app

client = TestClient(app)


def test_suggest_payload_includes_uncertainty_and_pairings():
    """Verify that suggestions return 95% credible intervals and data-grounded pairings."""
    res = client.post("/suggest", json={
        "enemy_heroes": ["Anti-Mage", "Invoker"],
        "ally_heroes": ["Crystal Maiden"],
        "role": "all"
    })
    assert res.status_code == 200
    data = res.json()
    assert "picks" in data
    assert len(data["picks"]) > 0

    top_pick = data["picks"][0]

    # 1. Uncertainty intervals
    assert "credible_interval" in top_pick
    assert top_pick["credible_interval"] is not None
    lower, upper = top_pick["credible_interval"]
    assert 0.0 <= lower <= upper <= 1.0

    assert "credible_interval_width" in top_pick
    assert top_pick["credible_interval_width"] > 0.0

    assert "effective_sample_size" in top_pick
    assert top_pick["effective_sample_size"] >= 10

    # 2. Data-grounded pairings
    assert "top_positive_pairings" in top_pick
    assert "top_negative_pairings" in top_pick

    # If pairings exist, verify schema
    for pairing in top_pick["top_positive_pairings"] + top_pick["top_negative_pairings"]:
        assert "pairing_type" in pairing
        assert "target_hero" in pairing
        assert "winrate" in pairing
        assert "games" in pairing
        assert "text" in pairing
        assert "%" in pairing["text"]
