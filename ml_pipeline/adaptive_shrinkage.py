"""
Dota 2 Drafter - Adaptive & Hierarchical Empirical-Bayes Shrinkage
Implements pair-level adaptive shrinkage where the shrinkage strength k
is dynamically scaled by pair sample density and empirical variance.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np


def compute_adaptive_matchup_shrinkage(
    matchup_wins: Dict[Tuple[int, int], float],
    matchup_games: Dict[Tuple[int, int], float],
    hero_winrate: Dict[int, float],
    global_prior: float = 0.50,
    base_k: float = 15.0,
    gamma: float = 0.5
) -> Tuple[Dict[Tuple[int, int], float], Dict[Tuple[int, int], float]]:
    """
    Compute adaptive shrinkage for hero matchups.
    
    Pairs with very large sample sizes (e.g. n > 1000 in 1.4M dataset)
    get reduced shrinkage (trusting empirical data), while sparse pairs
    receive strong regularization towards the hero baseline prior.
    
    Returns:
        shrunk_matrix: dict of (h1, h2) -> winrate
        effective_k_matrix: dict of (h1, h2) -> effective_k
    """
    all_games = np.array(list(matchup_games.values()), dtype=np.float64)
    median_games = float(np.median(all_games)) if len(all_games) > 0 else 50.0

    shrunk = {}
    effective_k = {}

    for pair, g in matchup_games.items():
        h1, _ = pair
        prior = hero_winrate.get(h1, global_prior)
        w = matchup_wins.get(pair, 0.0)

        # Adaptive pseudo-count k: scaled down for dense pairs, bounded at [2.0, base_k * 2.0]
        density_ratio = median_games / (g + median_games)
        k_pair = float(np.clip(base_k * (density_ratio ** gamma), 2.0, base_k * 2.5))
        
        shrunk[pair] = float((w + k_pair * prior) / (g + k_pair))
        effective_k[pair] = k_pair

    return shrunk, effective_k


def compute_adaptive_synergy_shrinkage(
    synergy_wins: Dict[Tuple[int, int], float],
    synergy_games: Dict[Tuple[int, int], float],
    base_k: float = 15.0,
    gamma: float = 0.5
) -> Tuple[Dict[Tuple[int, int], float], Dict[Tuple[int, int], float]]:
    """
    Compute adaptive shrinkage for hero allies synergy.
    """
    all_games = np.array(list(synergy_games.values()), dtype=np.float64)
    median_games = float(np.median(all_games)) if len(all_games) > 0 else 50.0

    shrunk = {}
    effective_k = {}

    for pair, g in synergy_games.items():
        w = synergy_wins.get(pair, 0.0)
        density_ratio = median_games / (g + median_games)
        k_pair = float(np.clip(base_k * (density_ratio ** gamma), 2.0, base_k * 2.5))
        
        shrunk[pair] = float((w + k_pair * 0.50) / (g + k_pair))
        effective_k[pair] = k_pair

    return shrunk, effective_k
