"""
API integration tests for FastAPI endpoints:
- /health (data freshness and model status)
- /heroes (numeric IDs and metadata schema)
- /suggest (draft recommendations, roles, bans, confidence, and caching)
- Validation errors (max 5 enemies, max 4 allies, deduplication, unknown heroes)
"""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app
from app.model_loader import store

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["heroes"] > 0
    assert "model_version" in data
    assert "data_freshness" in data
    assert "match_count" in data["data_freshness"]


def test_database_stats_endpoint():
    res = client.get('/database/stats')
    assert res.status_code == 200
    data = res.json()
    assert 'status' in data
    assert 'model_freshness' in data


def test_heroes_endpoint():
    res = client.get("/heroes")
    assert res.status_code == 200
    heroes = res.json()
    assert isinstance(heroes, list)
    assert len(heroes) >= 120
    sample = heroes[0]
    assert "id" in sample
    assert "name" in sample
    assert "roles" in sample
    assert "attribute" in sample
    assert "image_url" in sample
    assert isinstance(sample["id"], int)


def test_suggest_basic_flow():
    payload = {
        "enemy": ["Pudge", "Viper", "Sniper"],
        "team": ["Crystal Maiden"],
        "bans": ["Lion"]
    }
    res = client.post("/suggest", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "picks" in data
    picks = data["picks"]
    assert len(picks) > 0
    top = picks[0]
    assert "id" in top
    assert "name" in top
    assert "score" in top
    assert "confidence" in top
    assert top["confidence"] in ["low", "medium", "high"]
    assert "sample_size" in top
    assert "reasons" in top
    assert "reason_details" in top

    # Banned and picked heroes must never be in picks
    pick_ids = {p["id"] for p in picks}
    assert store.name_to_id["lion"] not in pick_ids
    assert store.name_to_id["pudge"] not in pick_ids
    assert store.name_to_id["crystal maiden"] not in pick_ids


def test_suggest_numeric_ids():
    # 14 = Pudge, 47 = Viper, 5 = Crystal Maiden
    payload = {
        "enemy": [14, 47],
        "team": [5],
        "bans": [35]  # Sniper
    }
    res = client.post("/suggest", json=payload)
    assert res.status_code == 200
    picks = res.json()["picks"]
    assert len(picks) > 0
    pick_ids = {p["id"] for p in picks}
    assert 14 not in pick_ids
    assert 47 not in pick_ids
    assert 5 not in pick_ids
    assert 35 not in pick_ids


def test_suggest_validation_too_many_enemies():
    payload = {"enemy": ["Pudge", "Viper", "Sniper", "Axe", "Lion", "Drow Ranger"]}
    res = client.post("/suggest", json=payload)
    assert res.status_code == 422
    data = res.json()
    assert "Maximum allowed is 5 heroes" in str(data)


def test_suggest_validation_too_many_allies():
    payload = {"team": ["Pudge", "Viper", "Sniper", "Axe", "Lion"]}
    res = client.post("/suggest", json=payload)
    assert res.status_code == 422
    data = res.json()
    assert "Maximum allowed is 4 heroes" in str(data)


def test_suggest_validation_duplicate_heroes():
    payload = {"enemy": ["Pudge", "Pudge"]}
    res = client.post("/suggest", json=payload)
    assert res.status_code == 422
    data = res.json()
    assert "Duplicate heroes detected" in str(data)


def test_suggest_validation_cross_team_overlap():
    payload = {"enemy": ["Pudge"], "team": ["Pudge"]}
    res = client.post("/suggest", json=payload)
    assert res.status_code == 422
    data = res.json()
    assert "cannot be picked on both teams simultaneously" in str(data)


def test_suggest_validation_ban_overlap():
    payload = {"team": ["Pudge"], "bans": ["Pudge"]}
    res = client.post("/suggest", json=payload)
    assert res.status_code == 422
    data = res.json()
    assert "cannot be both banned and picked" in str(data)


def test_suggest_validation_unknown_hero():
    payload = {"enemy": ["TotallyFakeHero123"]}
    res = client.post("/suggest", json=payload)
    assert res.status_code == 422
    data = res.json()
    assert "Unknown hero" in str(data)


def test_suggest_role_aware_mode():
    payload = {
        "enemy": ["Pudge"],
        "team": ["Anti-Mage", "Puck", "Centaur Warrunner"],
        "role_aware": True
    }
    res = client.post("/suggest", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["role_aware"] is True
    assert "support" in data["roles_needed"]
    # Top pick should include support
    picks = data["picks"]
    assert any("support" in p["roles"] for p in picks[:3])


def test_suggest_lru_caching():
    payload = {"enemy": ["Pudge"], "team": ["Viper"]}
    res1 = client.post("/suggest", json=payload)
    assert res1.status_code == 200
    assert res1.headers.get("x-cache") == "MISS"

    res2 = client.post("/suggest", json=payload)
    assert res2.status_code == 200
    assert res2.headers.get("x-cache") == "HIT"


def test_security_headers_present():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"

