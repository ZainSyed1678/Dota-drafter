import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_too_many_heroes():
    payload = {
        "team": ["Sven", "Pudge", "Invoker", "Axe", "Lina", "Drow Ranger"],
        "enemy": ["Meepo"]
    }
    response = client.post("/suggest", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert "Too many heroes" in str(data["details"])

def test_duplicate_hero_in_team():
    payload = {
        "team": ["Sven", "sven"],
        "enemy": ["Meepo"]
    }
    response = client.post("/suggest", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert "Duplicate heroes detected" in str(data["details"])

def test_cross_team_duplicate_hero():
    payload = {
        "team": ["Sven"],
        "enemy": ["Sven", "Chaos Knight"]
    }
    response = client.post("/suggest", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert "both teams simultaneously" in str(data["details"])

def test_security_headers_present():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"

def test_valid_draft_success():
    payload = {
        "team": ["Drow Ranger"],
        "enemy": ["Meepo", "Chaos Knight"]
    }
    response = client.post("/suggest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "picks" in data
    assert len(data["picks"]) > 0
