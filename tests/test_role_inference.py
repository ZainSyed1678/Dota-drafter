"""Tests for data-driven role inference and role contamination regression."""

import sys
import json
import pickle
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml_pipeline.role_inference import (
    load_static_taxonomy,
    build_hero_role_priors,
    assign_team_roles,
    ROLES
)


def test_static_taxonomy_priors_normalization():
    """Verify that prior distributions are normalized to 1.0 for every hero."""
    tax = load_static_taxonomy()
    priors = build_hero_role_priors(tax)
    assert len(priors) > 100

    for hid, dist in priors.items():
        assert abs(sum(dist.values()) - 1.0) < 1e-4
        for r in ROLES:
            assert dist[r] > 0.0


def test_team_role_assignment_diversity():
    """Verify that a team of 5 standard heroes gets assigned 1 carry, 1 mid, 1 offlane, 2 supports."""
    tax = load_static_taxonomy()
    priors = build_hero_role_priors(tax)

    # Team: Anti-Mage (1, carry), Invoker (74, mid), Axe (2, offlane), Crystal Maiden (5, support), Lion (26, support)
    team = [1, 74, 2, 5, 26]
    assignments = assign_team_roles(team, priors)

    role_counts = {}
    for h, r in assignments:
        role_counts[r] = role_counts.get(r, 0) + 1

    assert role_counts.get("carry") == 1
    assert role_counts.get("mid") == 1
    assert role_counts.get("offlane") == 1
    assert role_counts.get("support") == 2

    # Specific hero assignments
    assigned_dict = dict(assignments)
    assert assigned_dict[1] == "carry"
    assert assigned_dict[74] == "mid"
    assert assigned_dict[2] == "offlane"
    assert assigned_dict[5] == "support"
    assert assigned_dict[26] == "support"


def test_inferred_role_distributions_ground_truth():
    """Verify inferred distributions match known Dota 2 archetypes without contamination."""
    dist_path = Path("backend/model/v2026.11.15-masked/role_distributions.json")
    if not dist_path.exists():
        pytest.skip("role_distributions.json not yet generated")

    with open(dist_path, "r") as f:
        data = json.load(f)

    # 1. Anti-Mage (ID 1)
    am = data.get("1")
    assert am is not None
    assert am["primary_role"] == "carry"
    assert am["distribution"]["carry"] >= 0.70
    assert am["distribution"]["support"] < 0.10, "Anti-Mage must never be contaminated with support"

    # 2. Crystal Maiden (ID 5)
    cm = data.get("5")
    assert cm is not None
    assert cm["primary_role"] == "support"
    assert cm["distribution"]["support"] >= 0.70
    assert cm["distribution"]["carry"] < 0.10, "Crystal Maiden must never be contaminated with carry"

    # 3. Invoker (ID 74)
    invoker = data.get("74")
    assert invoker is not None
    assert invoker["primary_role"] == "mid"
    assert invoker["distribution"]["mid"] >= 0.50

    # 4. Axe (ID 2)
    axe = data.get("2")
    assert axe is not None
    assert axe["primary_role"] == "offlane"
    assert axe["distribution"]["offlane"] >= 0.50


def test_probabilistic_role_filtering_and_fallback():
    """Verify role filtering with threshold and fallback for low sample heroes."""
    dist_path = Path("backend/model/v2026.11.15-masked/role_distributions.json")
    if not dist_path.exists():
        pytest.skip("role_distributions.json not yet generated")

    with open(dist_path, "r") as f:
        data = json.load(f)

    # Anti-Mage (ID 1)
    am_dist = data["1"]["distribution"]
    threshold = 0.15
    assert am_dist["carry"] >= threshold
    assert am_dist["support"] < threshold

    # Total distribution always sums to ~1.0
    for hid, info in data.items():
        total_p = sum(info["distribution"].values())
        assert abs(total_p - 1.0) < 0.02
