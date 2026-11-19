"""Incremental count updates with periodic full-recompute integrity verification.

Maintains online accumulators for hero winrates, matchup matrices, and synergy matrices,
allowing new matches to be ingested without scanning the entire 1.4M dataset.
Periodically verifies incremental counts against full recomputation to numerical tolerance (<1e-6).
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np


class DraftCountAccumulator:
    """Online accumulator for match statistics with exact mathematical equivalence to batch scanning."""

    def __init__(self):
        self.hero_wins: Dict[int, float] = {}
        self.hero_games: Dict[int, float] = {}
        self.matchup_wins: Dict[Tuple[int, int], float] = {}
        self.matchup_games: Dict[Tuple[int, int], float] = {}
        self.synergy_wins: Dict[Tuple[int, int], float] = {}
        self.synergy_games: Dict[Tuple[int, int], float] = {}
        self.total_matches: int = 0

    def add_match(self, radiant_team: List[int], dire_team: List[int], radiant_win: bool, weight: float = 1.0):
        """Incorporate a single match into running tallies."""
        rw = 1.0 if radiant_win else 0.0
        w = float(weight)

        for h in radiant_team:
            self.hero_wins[h] = self.hero_wins.get(h, 0.0) + (rw * w)
            self.hero_games[h] = self.hero_games.get(h, 0.0) + w

        for h in dire_team:
            self.hero_wins[h] = self.hero_wins.get(h, 0.0) + ((1.0 - rw) * w)
            self.hero_games[h] = self.hero_games.get(h, 0.0) + w

        # Matchups
        for h1 in radiant_team:
            for h2 in dire_team:
                p1 = (h1, h2)
                p2 = (h2, h1)
                self.matchup_wins[p1] = self.matchup_wins.get(p1, 0.0) + (rw * w)
                self.matchup_games[p1] = self.matchup_games.get(p1, 0.0) + w
                self.matchup_wins[p2] = self.matchup_wins.get(p2, 0.0) + ((1.0 - rw) * w)
                self.matchup_games[p2] = self.matchup_games.get(p2, 0.0) + w

        # Synergies
        for i in range(len(radiant_team)):
            for j in range(i + 1, len(radiant_team)):
                pair = (min(radiant_team[i], radiant_team[j]), max(radiant_team[i], radiant_team[j]))
                self.synergy_wins[pair] = self.synergy_wins.get(pair, 0.0) + (rw * w)
                self.synergy_games[pair] = self.synergy_games.get(pair, 0.0) + w

        for i in range(len(dire_team)):
            for j in range(i + 1, len(dire_team)):
                pair = (min(dire_team[i], dire_team[j]), max(dire_team[i], dire_team[j]))
                self.synergy_wins[pair] = self.synergy_wins.get(pair, 0.0) + ((1.0 - rw) * w)
                self.synergy_games[pair] = self.synergy_games.get(pair, 0.0) + w

        self.total_matches += 1

    def add_batch(self, matches: List[Dict[str, Any]]):
        """Add a batch of matches."""
        for m in matches:
            self.add_match(
                radiant_team=m["radiant_team"],
                dire_team=m["dire_team"],
                radiant_win=m["radiant_win"],
                weight=m.get("weight", 1.0)
            )

    def compute_matrices(
        self,
        k_matchup: float = 1.0,
        k_synergy: float = 200.0,
        k_hero: float = 50.0
    ) -> Dict[str, Any]:
        """Compute shrunk winrates and matrices from accumulated counts."""
        hero_winrate = {}
        for h, g in self.hero_games.items():
            w = self.hero_wins.get(h, 0.0)
            hero_winrate[h] = (w + k_hero * 0.50) / (g + k_hero) if (g + k_hero) > 0 else 0.50

        global_prior = float(np.mean(list(hero_winrate.values()))) if hero_winrate else 0.50

        shrunk_matchup = {}
        for pair, g in self.matchup_games.items():
            h1, h2 = pair
            w = self.matchup_wins.get(pair, 0.0)
            prior = 0.50 + 0.5 * (hero_winrate.get(h1, 0.50) - hero_winrate.get(h2, 0.50))
            shrunk_matchup[pair] = (w + k_matchup * prior) / (g + k_matchup)

        shrunk_synergy = {}
        for pair, g in self.synergy_games.items():
            h1, h2 = pair
            w = self.synergy_wins.get(pair, 0.0)
            prior = 0.50 + 0.5 * (hero_winrate.get(h1, 0.50) + hero_winrate.get(h2, 0.50) - 1.0)
            shrunk_synergy[pair] = (w + k_synergy * prior) / (g + k_synergy)

        return {
            "hero_winrate": hero_winrate,
            "matchup": shrunk_matchup,
            "synergy": shrunk_synergy,
            "total_matches": self.total_matches
        }

    def verify_against_full_recompute(self, full_matches: List[Dict[str, Any]], tolerance: float = 1e-6) -> Tuple[bool, float]:
        """
        Periodically recompute full matrix from scratch and assert
        max absolute difference < tolerance.
        """
        full_acc = DraftCountAccumulator()
        full_acc.add_batch(full_matches)

        inc_res = self.compute_matrices()
        full_res = full_acc.compute_matrices()

        max_diff = 0.0
        # Check hero winrates
        for h, wr in full_res["hero_winrate"].items():
            inc_wr = inc_res["hero_winrate"].get(h, 0.50)
            max_diff = max(max_diff, abs(wr - inc_wr))

        # Check matchup matrix
        for p, m in full_res["matchup"].items():
            inc_m = inc_res["matchup"].get(p, 0.50)
            max_diff = max(max_diff, abs(m - inc_m))

        # Check synergy matrix
        for p, s in full_res["synergy"].items():
            inc_s = inc_res["synergy"].get(p, 0.50)
            max_diff = max(max_diff, abs(s - inc_s))

        is_valid = bool(max_diff < tolerance)
        return is_valid, float(max_diff)
