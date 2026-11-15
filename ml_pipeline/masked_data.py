"""
Dota 2 Drafter - Partial-Draft (Masked) Training Data Generator
Generates realistic mid-draft states with random hero masking (0-9 revealed heroes)
and explicit mask state indicators.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


def generate_masked_draft_sample(
    radiant_team: List[int],
    dire_team: List[int],
    radiant_win: int,
    rng: np.random.RandomState
) -> Dict[str, Any]:
    """
    Sample a partial draft state from a complete 5v5 match.
    Emphasizes realistic mid-draft states (1-4 enemies, 0-4 allies).
    """
    # Distribution over total revealed heroes (0 to 10)
    # Give higher weight to realistic mid-draft states (1 to 8 revealed)
    weights = np.array([0.02, 0.05, 0.10, 0.15, 0.20, 0.18, 0.14, 0.08, 0.05, 0.02, 0.01])
    weights /= weights.sum()
    total_revealed = int(rng.choice(np.arange(11), p=weights))

    # Split total_revealed between radiant and dire
    # e.g., if total_revealed = 5, radiant can have 0..5, dire has the rest bounded by 5
    min_r = max(0, total_revealed - 5)
    max_r = min(5, total_revealed)
    n_r = rng.randint(min_r, max_r + 1)
    n_d = total_revealed - n_r

    # Select random subsets of heroes
    rev_r = list(rng.choice(radiant_team, size=n_r, replace=False)) if n_r > 0 else []
    rev_d = list(rng.choice(dire_team, size=n_d, replace=False)) if n_d > 0 else []

    return {
        "revealed_radiant": rev_r,
        "revealed_dire": rev_d,
        "n_radiant": n_r,
        "n_dire": n_d,
        "total_revealed": total_revealed,
        "radiant_win": radiant_win
    }


def build_masked_feature_vector(
    revealed_radiant: List[int],
    revealed_dire: List[int],
    hero_to_idx: Dict[int, int],
    hero_winrate: Dict[int, float],
    global_prior: float = 0.50
) -> np.ndarray:
    """
    Construct feature vector for partial drafts:
    - Sparse indicator: +1 (Radiant), -1 (Dire), 0 (Unrevealed / not picked)
    - State indicator: [n_r / 5.0, n_d / 5.0, (n_r - n_d) / 5.0, total_revealed / 10.0]
    - Mean revealed winrates: [r_mean_wr, d_mean_wr, diff_wr]
    """
    num_heroes = len(hero_to_idx)
    vec = np.zeros(num_heroes, dtype=np.float32)

    for h in revealed_radiant:
        if h in hero_to_idx:
            vec[hero_to_idx[h]] = 1.0

    for h in revealed_dire:
        if h in hero_to_idx:
            vec[hero_to_idx[h]] = -1.0

    n_r = len(revealed_radiant)
    n_d = len(revealed_dire)
    total_rev = n_r + n_d

    r_wr = float(np.mean([hero_winrate.get(h, global_prior) for h in revealed_radiant])) if n_r > 0 else global_prior
    d_wr = float(np.mean([hero_winrate.get(h, global_prior) for h in revealed_dire])) if n_d > 0 else global_prior

    state_indicators = np.array([
        n_r / 5.0,
        n_d / 5.0,
        (n_r - n_d) / 5.0,
        total_rev / 10.0,
        r_wr,
        d_wr,
        r_wr - d_wr
    ], dtype=np.float32)

    return np.concatenate([vec, state_indicators])
