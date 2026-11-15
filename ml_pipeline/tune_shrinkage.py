"""
Dota 2 Drafter - Per-Matrix Shrinkage (k) and Recency (lambda) Tuning
Grid searches over validation fold to find optimal hyper-parameters:
- k_matchup in [0, 1, 2, 5, 10, 20, 50, 100, 200]
- k_synergy in [0, 1, 2, 5, 10, 20, 50, 100, 200]
- k_hero in [0, 1, 2, 5, 10, 20, 50, 100, 200]
- lambda_recency in [0.0, 0.05, 0.1, 0.2, 0.4]
Tunes matrices separately (not sharing one k).
"""

import argparse
import datetime
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml_pipeline.harness import WalkForwardHarness
from scripts.run_baseline_evaluation import clean_team_list, extract_score_components


def compute_weighted_counts(
    train_df: pd.DataFrame,
    sorted_heroes: List[int],
    recency_lambda: float = 0.2
) -> Tuple[Dict[int, float], Dict[int, float], Dict[Tuple[int, int], float], Dict[Tuple[int, int], float], Dict[Tuple[int, int], float], Dict[Tuple[int, int], float]]:
    """Compute raw frequency accumulators on train with time decay."""
    N_tr = len(train_df)
    weights = np.zeros(N_tr, dtype=np.float32)
    for idx in range(N_tr):
        weights[idx] = np.exp(-recency_lambda * (1.0 - (idx / N_tr))) if recency_lambda > 0 else 1.0

    hero_wins = defaultdict(float)
    hero_games = defaultdict(float)
    matchup_wins = defaultdict(float)
    matchup_games = defaultdict(float)
    synergy_wins = defaultdict(float)
    synergy_games = defaultdict(float)

    for idx, row in train_df.iterrows():
        w = float(weights[idx])
        r_win = 1.0 if row['radiant_win'] else 0.0
        r_team = row['radiant_team']
        d_team = row['dire_team']

        for h in r_team:
            hero_wins[h] += w * r_win
            hero_games[h] += w
        for h in d_team:
            hero_wins[h] += w * (1.0 - r_win)
            hero_games[h] += w

        for h1 in r_team:
            for h2 in d_team:
                matchup_wins[(h1, h2)] += w * r_win
                matchup_games[(h1, h2)] += w
                matchup_wins[(h2, h1)] += w * (1.0 - r_win)
                matchup_games[(h2, h1)] += w

        for i in range(len(r_team)):
            for j in range(i + 1, len(r_team)):
                p1 = (min(r_team[i], r_team[j]), max(r_team[i], r_team[j]))
                synergy_wins[p1] += w * r_win
                synergy_games[p1] += w

        for i in range(len(d_team)):
            for j in range(i + 1, len(d_team)):
                p2 = (min(d_team[i], d_team[j]), max(d_team[i], d_team[j]))
                synergy_wins[p2] += w * (1.0 - r_win)
                synergy_games[p2] += w

    return hero_wins, hero_games, matchup_wins, matchup_games, synergy_wins, synergy_games


def build_shrunk_matrices(
    sorted_heroes: List[int],
    hero_wins: Dict[int, float],
    hero_games: Dict[int, float],
    matchup_wins: Dict[Tuple[int, int], float],
    matchup_games: Dict[Tuple[int, int], float],
    synergy_wins: Dict[Tuple[int, int], float],
    synergy_games: Dict[Tuple[int, int], float],
    k_hero: float = 10.0,
    k_matchup: float = 20.0,
    k_synergy: float = 20.0
) -> Tuple[Dict[int, float], float, Dict[Tuple[int, int], float], Dict[Tuple[int, int], float]]:
    """Compute decoupled shrunk matrices."""
    # Global winrate prior (unweighted mean across heroes)
    raw_wrs = [hero_wins[h] / hero_games[h] for h in sorted_heroes if hero_games[h] > 0]
    global_prior = float(np.mean(raw_wrs)) if raw_wrs else 0.50

    hero_winrate = {}
    for h in sorted_heroes:
        g = hero_games[h]
        hero_winrate[h] = (hero_wins[h] + k_hero * global_prior) / (g + k_hero) if (g + k_hero) > 0 else global_prior

    shrunk_matchup = {}
    for pair, g in matchup_games.items():
        h1, _ = pair
        prior = hero_winrate.get(h1, global_prior)
        shrunk_matchup[pair] = (matchup_wins[pair] + k_matchup * prior) / (g + k_matchup)

    shrunk_synergy = {}
    for pair, g in synergy_games.items():
        shrunk_synergy[pair] = (synergy_wins[pair] + k_synergy * 0.50) / (g + k_synergy)

    return hero_winrate, global_prior, shrunk_matchup, shrunk_synergy


def evaluate_param_set(
    val_df: pd.DataFrame,
    y_val: np.ndarray,
    hero_winrate: Dict[int, float],
    global_prior: float,
    shrunk_matchup: Dict[Tuple[int, int], float],
    shrunk_synergy: Dict[Tuple[int, int], float]
) -> float:
    """Evaluate log loss on validation set with heuristic logistic regression."""
    val_comps = extract_score_components(val_df, hero_winrate, global_prior, shrunk_matchup, shrunk_synergy)
    # Fit simple logistic regression on first half of val, evaluate on second half
    n_split = len(val_df) // 2
    X_v1, y_v1 = val_comps[:n_split], y_val[:n_split]
    X_v2, y_v2 = val_comps[n_split:], y_val[n_split:]

    clf = LogisticRegression(C=1.0, fit_intercept=True, random_state=42)
    clf.fit(X_v1, y_v1)
    probs = clf.predict_proba(X_v2)[:, 1]
    return float(log_loss(y_v2, np.clip(probs, 1e-7, 1.0 - 1e-7)))


def run_tuning(
    parquet_path: str = "data/snapshots/matches_clean.parquet",
    subsample_train: int = 200000,
    subsample_val: int = 50000,
    output_path: str = "reports/tuning_results.json"
) -> Dict[str, Any]:
    print("=" * 70)
    print("Dota 2 Drafter - Per-Matrix Shrinkage & Recency Tuning")
    print("=" * 70)
    t0 = time.time()

    harness = WalkForwardHarness(parquet_path=parquet_path, n_folds=1, holdout_ratio=0.15)
    folds = harness.get_folds()
    fold = folds[0]

    train_df = fold.train_df.iloc[-subsample_train:].copy().reset_index(drop=True)
    val_df = fold.val_df.iloc[:subsample_val].copy().reset_index(drop=True)
    y_val = val_df['radiant_win'].astype(int).values

    all_heroes = set()
    for _, r in train_df.iterrows():
        all_heroes.update(r['radiant_team'])
        all_heroes.update(r['dire_team'])
    sorted_heroes = sorted(list(all_heroes))

    k_values = [0.0, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0]
    lambda_values = [0.0, 0.05, 0.1, 0.2, 0.4]

    print(f"Tuning dataset: Train subsample={len(train_df):,} | Val subsample={len(val_df):,}")
    print(f"Testing k in {k_values}")
    print(f"Testing lambda in {lambda_values}")

    # Step 1: Tune lambda_recency with baseline k=(20, 20, 20)
    best_lambda = 0.2
    best_ll_lambda = 999.0
    lambda_history = {}

    for lam in lambda_values:
        hw, hg, mw, mg, sw, sg = compute_weighted_counts(train_df, sorted_heroes, recency_lambda=lam)
        h_wr, g_prior, s_matchup, s_synergy = build_shrunk_matrices(
            sorted_heroes, hw, hg, mw, mg, sw, sg, k_hero=10.0, k_matchup=20.0, k_synergy=20.0
        )
        ll = evaluate_param_set(val_df, y_val, h_wr, g_prior, s_matchup, s_synergy)
        lambda_history[str(lam)] = round(ll, 5)
        print(f"  lambda={lam:.2f} -> Val Log-Loss: {ll:.5f}")
        if ll < best_ll_lambda:
            best_ll_lambda = ll
            best_lambda = lam

    print(f"Optimal recency lambda: {best_lambda} (Log-Loss: {best_ll_lambda:.5f})")

    # Recompute counts with best lambda
    hw, hg, mw, mg, sw, sg = compute_weighted_counts(train_df, sorted_heroes, recency_lambda=best_lambda)

    # Step 2: Coordinate grid search for (k_matchup, k_synergy, k_hero)
    best_k_matchup = 20.0
    best_k_synergy = 20.0
    best_k_hero = 10.0
    min_ll = best_ll_lambda

    # Tune k_matchup
    matchup_history = {}
    print("\nTuning k_matchup...")
    for km in k_values:
        h_wr, g_prior, s_matchup, s_synergy = build_shrunk_matrices(
            sorted_heroes, hw, hg, mw, mg, sw, sg, k_hero=best_k_hero, k_matchup=km, k_synergy=best_k_synergy
        )
        ll = evaluate_param_set(val_df, y_val, h_wr, g_prior, s_matchup, s_synergy)
        matchup_history[str(km)] = round(ll, 5)
        print(f"  k_matchup={km:5.1f} -> Val Log-Loss: {ll:.5f}")
        if ll < min_ll:
            min_ll = ll
            best_k_matchup = km

    # Tune k_synergy
    synergy_history = {}
    print(f"\nTuning k_synergy (with k_matchup={best_k_matchup})...")
    for ks in k_values:
        h_wr, g_prior, s_matchup, s_synergy = build_shrunk_matrices(
            sorted_heroes, hw, hg, mw, mg, sw, sg, k_hero=best_k_hero, k_matchup=best_k_matchup, k_synergy=ks
        )
        ll = evaluate_param_set(val_df, y_val, h_wr, g_prior, s_matchup, s_synergy)
        synergy_history[str(ks)] = round(ll, 5)
        print(f"  k_synergy={ks:5.1f} -> Val Log-Loss: {ll:.5f}")
        if ll < min_ll:
            min_ll = ll
            best_k_synergy = ks

    # Tune k_hero
    hero_history = {}
    print(f"\nTuning k_hero (with k_matchup={best_k_matchup}, k_synergy={best_k_synergy})...")
    for kh in k_values:
        h_wr, g_prior, s_matchup, s_synergy = build_shrunk_matrices(
            sorted_heroes, hw, hg, mw, mg, sw, sg, k_hero=kh, k_matchup=best_k_matchup, k_synergy=best_k_synergy
        )
        ll = evaluate_param_set(val_df, y_val, h_wr, g_prior, s_matchup, s_synergy)
        hero_history[str(kh)] = round(ll, 5)
        print(f"  k_hero={kh:5.1f} -> Val Log-Loss: {ll:.5f}")
        if ll < min_ll:
            min_ll = ll
            best_k_hero = kh

    tuning_summary = {
        "timestamp": datetime.datetime.now().isoformat(),
        "elapsed_seconds": round(time.time() - t0, 1),
        "optimal_parameters": {
            "lambda_recency": best_lambda,
            "k_matchup": best_k_matchup,
            "k_synergy": best_k_synergy,
            "k_hero": best_k_hero
        },
        "baseline_vs_tuned": {
            "baseline_log_loss": round(best_ll_lambda, 5),
            "tuned_log_loss": round(min_ll, 5),
            "absolute_reduction": round(best_ll_lambda - min_ll, 5)
        },
        "search_trajectories": {
            "lambda": lambda_history,
            "k_matchup": matchup_history,
            "k_synergy": synergy_history,
            "k_hero": hero_history
        }
    }

    out_file = PROJECT_ROOT / output_path
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, 'w') as f:
        json.dump(tuning_summary, f, indent=2)

    print("=" * 70)
    print("Tuning Completed!")
    print(f"Optimal Config: lambda={best_lambda}, k_matchup={best_k_matchup}, k_synergy={best_k_synergy}, k_hero={best_k_hero}")
    print(f"Report saved to {out_file}")
    print("=" * 70)
    return tuning_summary


if __name__ == "__main__":
    run_tuning()
