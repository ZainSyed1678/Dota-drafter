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


def test_suggest_ten_picks_per_category_and_oneliners():
    payload = {"enemy": ["Anti-Mage"]}
    res = client.post("/suggest", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "categories" in data
    categories = data["categories"]
    required_roles = ["all", "carry", "mid", "offlane", "soft_support", "hard_support"]
    for role in required_roles:
        assert role in categories
        picks = categories[role]
        assert len(picks) == 10, f"Expected 10 picks for {role}, got {len(picks)}"
        for p in picks:
            assert "one_liner" in p
            assert len(p["one_liner"]) > 5


def test_missing_role_explanation_four_allies():
    """
    When user inputs 4 allies with 1 missing role (e.g. Mid), suggestions must:
    1. Explain how the hero performs in the missing role.
    2. Detail their stuns/disables and movement/mobility.
    3. Never output the generic duplicate boilerplate string.
    """
    generic_boilerplate = "provides stable teamfight control and general utility that fits the current draft balance"

    # Case 1: Axe (offlane), PA (carry), CM (support), Lion (support) -> Missing role: Mid
    payload_mid = {
        "enemy": [],
        "team": ["Axe", "Phantom Assassin", "Crystal Maiden", "Lion"]
    }
    res_mid = client.post("/suggest", json=payload_mid)
    assert res_mid.status_code == 200
    data_mid = res_mid.json()
    picks_mid = data_mid["picks"]
    assert len(picks_mid) >= 5

    for p in picks_mid:
        one_liner = p["one_liner"]
        assert len(one_liner) > 10
        assert generic_boilerplate not in one_liner
        # Check details for role fit
        has_role_fit = any(d.get("reason_type") == "role_fit" for d in p.get("reason_details", []))
        assert has_role_fit, f"Hero {p['name']} missing role_fit in reason_details"
        for d in p.get("reason_details", []):
            assert generic_boilerplate not in d.get("how_and_why", "")

    # Case 2: 4 cores entered -> Missing role: Support
    payload_sup = {
        "enemy": [],
        "team": ["Axe", "Phantom Assassin", "Puck", "Centaur Warrunner"]
    }
    res_sup = client.post("/suggest", json=payload_sup)
    assert res_sup.status_code == 200
    data_sup = res_sup.json()
    categories = data_sup["categories"]
    hard_sup_picks = categories.get("hard_support", [])
    assert len(hard_sup_picks) == 10

    # Ensure Ogre Magi, Shadow Shaman, Lich have distinct, unique one-liners and no generic boilerplate
    one_liners = [p["one_liner"] for p in hard_sup_picks]
    assert len(set(one_liners)) == len(one_liners), "Hard support picks must have unique one-liners without duplicates"
    for ol in one_liners:
        assert generic_boilerplate not in ol



