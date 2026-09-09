from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

def test_heroes():
    response = client.get("/heroes")
    assert response.status_code == 200
    data = response.json()
    # It should return a dict of ID -> Name
    assert len(data) > 0
    assert "1" in data or 1 in data or "2" in data or 2 in data # Some hero exists

def test_suggest():
    payload = {
        "enemy": ["Axe", "Lion"],
        "team": ["Crystal Maiden", "Juggernaut"]
    }
    response = client.post("/suggest", json=payload)
    if response.status_code == 503:
        pytest.skip("Models not loaded yet, skipping suggest test.")
    
    assert response.status_code == 200
    data = response.json()
    assert "picks" in data
    assert isinstance(data["picks"], list)
    if len(data["picks"]) > 0:
        first_pick = data["picks"][0]
        assert "id" in first_pick
        assert "name" in first_pick
        assert "score" in first_pick
        assert "reasons" in first_pick
        assert "roles" in first_pick
