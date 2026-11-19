"""Tests for optional model loading and graceful degradation."""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app
from app.model_loader import ModelStore, store
from app.scoring import predict, compute_embedding_win_prob, compute_model_win_prob

client = TestClient(app)


def test_embedding_model_graceful_fallback_when_none():
    """Verify that when embedding_model is None, scoring falls back without crash."""
    orig_emb = store.embedding_model
    try:
        store.embedding_model = None
        prob = compute_embedding_win_prob(1, [2, 3], [4, 5])
        assert prob == 0.50

        # Full predict with candidate
        score = predict(1, [2, 3], [4, 5])
        assert isinstance(score, float)
        assert -1.0 <= score <= 1.0
    finally:
        store.embedding_model = orig_emb


def test_ml_model_graceful_fallback_when_none():
    """Verify that when ml_model is None, scoring falls back to heuristic engine."""
    orig_ml = store.ml_model
    try:
        store.ml_model = None
        score = predict(1, [2, 3], [4, 5])
        assert isinstance(score, float)
        assert -1.0 <= score <= 1.0
    finally:
        store.ml_model = orig_ml


def test_api_suggest_remains_operational_without_embedding():
    """Verify public /suggest endpoint functions properly when embedding model is None."""
    orig_emb = store.embedding_model
    try:
        store.embedding_model = None
        res = client.post("/suggest", json={
            "enemy_heroes": ["Anti-Mage", "Invoker"],
            "ally_heroes": ["Crystal Maiden"],
            "banned_heroes": ["Pudge"],
            "role": "core"
        })
        assert res.status_code == 200
        data = res.json()
        assert "picks" in data
        assert len(data["picks"]) > 0
    finally:
        store.embedding_model = orig_emb
