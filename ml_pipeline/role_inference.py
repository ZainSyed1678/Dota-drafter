"""Data-driven role inference from match dataset.

Estimates P(role | hero, patch) empirically from team draft composition and co-occurrence.
Falls back to static taxonomy when sample size < 50.
Builds role-conditioned matchup matrices for core matchups (pos 1 vs pos 3, pos 2 vs pos 2).
"""

import sys
import json
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Canonical roles
ROLES = ["carry", "mid", "offlane", "support"]

# Well-known Dota 2 primary archetypes for prior calibration
PRIMARY_ARCHETYPES = {
    "carry": {
        1, 6, 8, 10, 12, 15, 18, 19, 41, 42, 44, 48, 54, 56, 67, 70, 72, 73, 77, 80,
        81, 82, 89, 93, 94, 95, 106, 109, 114
    },
    "mid": {
        11, 13, 17, 22, 25, 34, 35, 39, 43, 45, 46, 47, 49, 52, 53, 74, 75, 76,
        105, 108, 120, 121, 126
    },
    "offlane": {
        2, 7, 9, 14, 16, 23, 28, 29, 38, 51, 55, 59, 69, 78, 96, 97, 98, 99, 103,
        107, 110, 129, 135, 137
    },
    "support": {
        3, 4, 5, 20, 21, 26, 27, 30, 31, 32, 33, 36, 37, 58, 62, 64, 65, 66, 68,
        71, 79, 83, 84, 85, 86, 87, 88, 90, 91, 92, 100, 101, 102, 104, 111, 112,
        113, 119, 123, 128, 131, 136, 138
    }
}


def load_static_taxonomy(roles_pkl_path: str = "backend/model/roles.pkl") -> Dict[int, List[str]]:
    """Load baseline static taxonomy."""
    with open(roles_pkl_path, "rb") as f:
        return pickle.load(f)


def build_hero_role_priors(static_taxonomy: Dict[int, List[str]]) -> Dict[int, Dict[str, float]]:
    """Convert static taxonomy and archetypes to prior probability distributions."""
    priors = {}
    for hid, roles in static_taxonomy.items():
        r_set = set(r.lower() for r in roles)
        dist = {}
        for r in ROLES:
            w = 1.0
            if hid in PRIMARY_ARCHETYPES.get(r, set()):
                w += 15.0
            elif r in r_set:
                w += 3.0
            else:
                w = 0.05
            dist[r] = w
        tot = sum(dist.values())
        priors[hid] = {r: w / tot for r, w in dist.items()}
    return priors


def assign_team_roles(team_heroes: List[int], priors: Dict[int, Dict[str, float]]) -> List[Tuple[int, str]]:
    """
    Optimal bipartite matching assigning team heroes to roles:
    1 carry, 1 mid, 1 offlane, 2 supports.
    """
    slots = ["carry", "mid", "offlane", "support", "support"]
    heroes = list(team_heroes[:5])
    if len(heroes) < 5:
        return [(h, max(ROLES, key=lambda r: priors.get(h, {}).get(r, 0.25))) for h in heroes]

    # Cost matrix for linear sum assignment
    cost_matrix = np.zeros((5, 5), dtype=np.float64)
    for i, h in enumerate(heroes):
        h_prior = priors.get(h, {})
        for j, role in enumerate(slots):
            p = h_prior.get(role, 0.01)
            cost_matrix[i, j] = -np.log(max(p, 1e-4))

    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    assignments = []
    for r_i, c_i in zip(row_ind, col_ind):
        assignments.append((heroes[r_i], slots[c_i]))

    return assignments


def infer_role_distributions(
    parquet_path: str = "data/snapshots/matches_clean.parquet",
    roles_pkl_path: str = "backend/model/roles.pkl",
    train_ratio: float = 0.70,
    min_samples: int = 50,
    max_matches: int = 400000
) -> Tuple[Dict[int, Dict[str, float]], Dict[int, int], Dict[Tuple[int, int, str, str], float]]:
    """
    Infer empirical role distributions and role-conditioned matchup matrix
    from the chronological training split (zero leakage).
    """
    print(f"Loading matches for role inference from {parquet_path}...")
    df = pd.read_parquet(parquet_path)
    n_train = int(len(df) * train_ratio)
    train_df = df.iloc[:n_train]
    if len(train_df) > max_matches:
        train_df = train_df.iloc[-max_matches:]
    print(f"Fitting on training fold: {len(train_df):,} matches...")

    static_tax = load_static_taxonomy(roles_pkl_path)
    priors = build_hero_role_priors(static_tax)

    role_counts: Dict[int, Dict[str, float]] = {h: {r: 0.0 for r in ROLES} for h in static_tax.keys()}
    hero_totals: Dict[int, int] = {h: 0 for h in static_tax.keys()}
    role_matchups: Dict[Tuple[int, int, str, str], List[float]] = {}

    r_teams = train_df["radiant_team"].tolist()
    d_teams = train_df["dire_team"].tolist()
    r_wins = train_df["radiant_win"].tolist()

    for idx in range(len(train_df)):
        r_team = r_teams[idx]
        d_team = d_teams[idx]
        rw = 1.0 if r_wins[idx] else 0.0

        r_assign = assign_team_roles(r_team, priors)
        d_assign = assign_team_roles(d_team, priors)

        for h, r in r_assign:
            if h in role_counts:
                role_counts[h][r] += 1.0
                hero_totals[h] += 1

        for h, r in d_assign:
            if h in role_counts:
                role_counts[h][r] += 1.0
                hero_totals[h] += 1

        # Track lane/role direct matchups (carry vs offlane, mid vs mid)
        r_roles = {r: h for h, r in r_assign}
        d_roles = {r: h for h, r in d_assign}

        # Mid vs Mid
        if "mid" in r_roles and "mid" in d_roles:
            m_r = r_roles["mid"]
            m_d = d_roles["mid"]
            k1 = (m_r, m_d, "mid", "mid")
            k2 = (m_d, m_r, "mid", "mid")
            if k1 not in role_matchups:
                role_matchups[k1] = [0.0, 0.0]
            if k2 not in role_matchups:
                role_matchups[k2] = [0.0, 0.0]
            role_matchups[k1][0] += rw
            role_matchups[k1][1] += 1.0
            role_matchups[k2][0] += (1.0 - rw)
            role_matchups[k2][1] += 1.0

        # Radiant Safe (Carry) vs Dire Offlane
        if "carry" in r_roles and "offlane" in d_roles:
            c_r = r_roles["carry"]
            o_d = d_roles["offlane"]
            k1 = (c_r, o_d, "carry", "offlane")
            k2 = (o_d, c_r, "offlane", "carry")
            if k1 not in role_matchups:
                role_matchups[k1] = [0.0, 0.0]
            if k2 not in role_matchups:
                role_matchups[k2] = [0.0, 0.0]
            role_matchups[k1][0] += rw
            role_matchups[k1][1] += 1.0
            role_matchups[k2][0] += (1.0 - rw)
            role_matchups[k2][1] += 1.0

    # Normalize distributions with fallback when sample size < min_samples
    distributions: Dict[int, Dict[str, float]] = {}
    for h, prior in priors.items():
        tot = hero_totals.get(h, 0)
        if tot < min_samples:
            distributions[h] = dict(prior)
        else:
            smoothed = {}
            for r in ROLES:
                smoothed[r] = (role_counts[h][r] + 10.0 * prior[r]) / (tot + 10.0)
            distributions[h] = smoothed

    # Compute shrunk role matchup winrates (EB shrinkage with k=10)
    shrunk_role_matchup: Dict[Tuple[int, int, str, str], float] = {}
    for k, (w, g) in role_matchups.items():
        if g >= 30:
            shrunk_role_matchup[k] = float((w + 5.0) / (g + 10.0))

    print(f"Role inference complete for {len(distributions)} heroes. Shrunk role matchups: {len(shrunk_role_matchup):,}")
    return distributions, hero_totals, shrunk_role_matchup


def save_role_artifacts(
    distributions: Dict[int, Dict[str, float]],
    hero_totals: Dict[int, int],
    role_matchups: Dict[Tuple[int, int, str, str], float],
    output_dir: str = "backend/model/v2026.11.15-masked"
):
    """Save role distribution and role-conditioned matchup artifacts."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    dist_json = {
        str(h): {
            "distribution": {r: round(p, 4) for r, p in dist.items()},
            "primary_role": max(dist.keys(), key=lambda r: dist[r]),
            "sample_size": hero_totals.get(h, 0)
        }
        for h, dist in distributions.items()
    }
    with open(out_path / "role_distributions.json", "w") as f:
        json.dump(dist_json, f, indent=2)

    with open(out_path / "role_distributions.pkl", "wb") as f:
        pickle.dump(distributions, f)

    with open(out_path / "role_matchup.pkl", "wb") as f:
        pickle.dump(role_matchups, f)

    print(f"Role artifacts saved to {out_path}")


if __name__ == "__main__":
    dists, totals, r_matchups = infer_role_distributions()
    save_role_artifacts(dists, totals, r_matchups)
