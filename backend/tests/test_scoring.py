import pytest
import scoring

def test_norm_matchup_empty():
    assert scoring.norm_matchup(1, []) == 0.0

def test_synergy_score_empty():
    assert scoring.synergy_score(1, []) == 0.0

def test_resolve_hero_names():
    # Test valid and invalid
    hero_map_sample = {1: "Anti-Mage", 2: "Axe"}
    scoring.name_to_id = {"anti-mage": 1, "axe": 2}
    
    resolved = scoring.resolve(["Anti-Mage", "InvalidHero"])
    assert resolved == [1]
