"""
Dota 2 Drafter - Leakage-Free Time-Based Evaluation Pipeline (Phase 1)
Evaluates draft prediction models on strictly temporal splits:
- Train: Oldest matches (70%)
- Validation: Middle slice (15%)
- Test: Newest matches (15%)

Computes ALL hero win rates, matchup matrices, and synergy matrices
STRICTLY on the training set to prevent any data leakage.
"""

import os
import sys
import json
import ast
import argparse
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score, brier_score_loss
from sklearn.calibration import calibration_curve
import lightgbm as lgb


def clean_team(x):
    """Clean team string or list into list of valid integers."""
    try:
        while isinstance(x, str):
            try:
                x = ast.literal_eval(x)
            except Exception:
                break
        if isinstance(x, str):
            x = x.replace('[', '').replace(']', '')
            x = [int(i.strip()) for i in x.split(',') if i.strip().isdigit()]
        return [int(h) for h in x if int(h) > 0]
    except Exception:
        return []


def load_and_clean_data(csv_path: str):
    """Load match data and filter to complete 5v5 matches ordered chronologically by match_id."""
    df = pd.read_csv(csv_path)
    df['radiant_team'] = df['radiant_team'].apply(clean_team)
    df['dire_team'] = df['dire_team'].apply(clean_team)

    # 5v5 validation: exactly 5 distinct heroes per team, no overlap
    valid_mask = (
        df['radiant_team'].apply(lambda t: len(t) == 5 and len(set(t)) == 5) &
        df['dire_team'].apply(lambda t: len(t) == 5 and len(set(t)) == 5) &
        df.apply(lambda r: len(set(r['radiant_team']) & set(r['dire_team'])) == 0, axis=1)
    )
    df = df[valid_mask].copy()

    # Ensure chronological order by match_id
    df['match_id'] = df['match_id'].astype(np.int64)
    df = df.sort_values('match_id', ascending=True).reset_index(drop=True)
    df['radiant_win'] = df['radiant_win'].astype(int)

    return df


def compute_train_features(train_df: pd.DataFrame):
    """
    Compute hero statistics STRICTLY on train_df.
    Zero leakage into val or test.
    """
    # 1. Active hero universe from training set
    hero_counts = Counter()
    for _, row in train_df.iterrows():
        hero_counts.update(row['radiant_team'])
        hero_counts.update(row['dire_team'])

    valid_heroes = sorted(list(hero_counts.keys()))
    hero_to_idx = {h: i for i, h in enumerate(valid_heroes)}
    num_heroes = len(valid_heroes)

    # 2. Individual hero win rates from train
    hero_wins = Counter()
    hero_games = Counter()
    for _, row in train_df.iterrows():
        rw = row['radiant_win']
        for h in row['radiant_team']:
            hero_games[h] += 1
            hero_wins[h] += rw
        for h in row['dire_team']:
            hero_games[h] += 1
            hero_wins[h] += (1 - rw)

    hero_winrate = {}
    for h in valid_heroes:
        hero_winrate[h] = hero_wins[h] / hero_games[h] if hero_games[h] > 0 else 0.5

    # 3. Pairwise Matchup Matrix from train
    matchup_pair_wins = Counter()
    matchup_pair_games = Counter()
    for _, row in train_df.iterrows():
        rw = row['radiant_win']
        for r in row['radiant_team']:
            for d in row['dire_team']:
                matchup_pair_wins[(r, d)] += rw
                matchup_pair_games[(r, d)] += 1
                matchup_pair_wins[(d, r)] += (1 - rw)
                matchup_pair_games[(d, r)] += 1

    matchup_matrix = {}
    for pair, games in matchup_pair_games.items():
        if games > 0:
            matchup_matrix[pair] = matchup_pair_wins[pair] / games

    # Global hero average matchup win rate
    hero_avg_matchup = {}
    for h in valid_heroes:
        opp_winrates = [matchup_matrix[(h, opp)] for opp in valid_heroes if (h, opp) in matchup_matrix]
        hero_avg_matchup[h] = float(np.mean(opp_winrates)) if opp_winrates else hero_winrate.get(h, 0.5)

    # 4. Pairwise Synergy Matrix from train
    synergy_pair_wins = Counter()
    synergy_pair_games = Counter()
    for _, row in train_df.iterrows():
        rw = row['radiant_win']
        r_team = row['radiant_team']
        for i in range(len(r_team)):
            for j in range(i + 1, len(r_team)):
                pair = (min(r_team[i], r_team[j]), max(r_team[i], r_team[j]))
                synergy_pair_wins[pair] += rw
                synergy_pair_games[pair] += 1

        d_team = row['dire_team']
        dw = 1 - rw
        for i in range(len(d_team)):
            for j in range(i + 1, len(d_team)):
                pair = (min(d_team[i], d_team[j]), max(d_team[i], d_team[j]))
                synergy_pair_wins[pair] += dw
                synergy_pair_games[pair] += 1

    synergy_matrix = {}
    for pair, games in synergy_pair_games.items():
        if games > 0:
            synergy_matrix[pair] = synergy_pair_wins[pair] / games

    # Global radiant base win rate in training
    global_radiant_wr = float(train_df['radiant_win'].mean())

    return {
        "valid_heroes": valid_heroes,
        "hero_to_idx": hero_to_idx,
        "num_heroes": num_heroes,
        "hero_winrate": hero_winrate,
        "matchup_matrix": matchup_matrix,
        "hero_avg_matchup": hero_avg_matchup,
        "synergy_matrix": synergy_matrix,
        "global_radiant_wr": global_radiant_wr,
    }


def build_feature_vectors(df: pd.DataFrame, stats: dict):
    """
    Construct model feature vectors using strictly training-derived matrices.
    Returns:
    - X_full: hero one-hot presence + aggregated engineered features
    - wr_diff: sum of hero winrates difference (for Baseline B)
    - matchup_score: net matchup score (for Baseline C)
    - y: labels
    """
    num_heroes = stats["num_heroes"]
    hero_to_idx = stats["hero_to_idx"]
    hero_winrate = stats["hero_winrate"]
    matchup_matrix = stats["matchup_matrix"]
    synergy_matrix = stats["synergy_matrix"]
    global_radiant_wr = stats["global_radiant_wr"]

    X_list = []
    wr_diff_list = []
    matchup_score_list = []
    y_list = []

    for _, row in df.iterrows():
        r_team = row['radiant_team']
        d_team = row['dire_team']
        y_val = row['radiant_win']

        # 1. One-hot presence vector (+1 for Radiant, -1 for Dire)
        hero_vec = np.zeros(num_heroes, dtype=np.float32)
        for h in r_team:
            if h in hero_to_idx:
                hero_vec[hero_to_idx[h]] = 1.0
        for h in d_team:
            if h in hero_to_idx:
                hero_vec[hero_to_idx[h]] = -1.0

        # 2. Team winrates
        r_wrs = [hero_winrate.get(h, 0.5) for h in r_team]
        d_wrs = [hero_winrate.get(h, 0.5) for h in d_team]
        r_mean_wr = float(np.mean(r_wrs))
        d_mean_wr = float(np.mean(d_wrs))
        diff_wr = r_mean_wr - d_mean_wr
        sum_diff = float(np.sum(r_wrs) - np.sum(d_wrs))

        # 3. Net Matchup Score
        matchup_score = 0.0
        for r in r_team:
            for d in d_team:
                m_wr = matchup_matrix.get((r, d), 0.5)
                matchup_score += (m_wr - 0.5)

        # 4. Net Synergy Score (Radiant synergy - Dire synergy)
        r_syn = 0.0
        for i in range(len(r_team)):
            for j in range(i + 1, len(r_team)):
                p = (min(r_team[i], r_team[j]), max(r_team[i], r_team[j]))
                r_syn += (synergy_matrix.get(p, 0.5) - 0.5)

        d_syn = 0.0
        for i in range(len(d_team)):
            for j in range(i + 1, len(d_team)):
                p = (min(d_team[i], d_team[j]), max(d_team[i], d_team[j]))
                d_syn += (synergy_matrix.get(p, 0.5) - 0.5)

        net_syn = r_syn - d_syn

        # Assemble full vector
        features = list(hero_vec) + [
            2.0 * r_mean_wr,
            2.0 * d_mean_wr,
            3.0 * diff_wr,
            4.0 * matchup_score,
            2.0 * net_syn
        ]

        X_list.append(features)
        wr_diff_list.append([sum_diff])
        matchup_score_list.append([matchup_score])
        y_list.append(y_val)

    return (
        np.ascontiguousarray(X_list, dtype=np.float32),
        np.ascontiguousarray(wr_diff_list, dtype=np.float32),
        np.ascontiguousarray(matchup_score_list, dtype=np.float32),
        np.ascontiguousarray(y_list, dtype=np.float32)
    )


def compute_metrics(y_true, y_prob):
    """Compute Accuracy, Log-Loss, ROC-AUC, and Brier Score."""
    y_true_int = np.asarray(y_true, dtype=np.int32)
    y_pred = (y_prob >= 0.5).astype(int)
    acc = float(accuracy_score(y_true_int, y_pred))
    ll = float(log_loss(y_true_int, np.clip(y_prob, 1e-7, 1 - 1e-7)))
    roc = float(roc_auc_score(y_true_int, y_prob))
    brier = float(brier_score_loss(y_true_int, y_prob))
    return {
        "accuracy": round(acc, 4),
        "log_loss": round(ll, 4),
        "roc_auc": round(roc, 4),
        "brier_score": round(brier, 4)
    }


def main():
    parser = argparse.ArgumentParser(description="Leakage-Free Time-Based Evaluation")
    parser.add_argument("--csv", type=str, default="notebooks/matches.csv", help="Path to matches CSV")
    parser.add_argument("--train_ratio", type=float, default=0.70, help="Train split ratio")
    parser.add_argument("--val_ratio", type=float, default=0.15, help="Validation split ratio")
    parser.add_argument("--reports_dir", type=str, default="ml_pipeline/reports", help="Output directory for reports")
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading matches from {args.csv}...")
    df = load_and_clean_data(args.csv)
    n_total = len(df)
    print(f"Total valid 5v5 matches: {n_total}")

    # Time-based split by match_id
    n_train = int(n_total * args.train_ratio)
    n_val = int(n_total * args.val_ratio)
    train_df = df.iloc[:n_train].copy()
    val_df = df.iloc[n_train:n_train + n_val].copy()
    test_df = df.iloc[n_train + n_val:].copy()

    print(f"Time-based split: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    print(f"Train match_id range: [{train_df['match_id'].min()} - {train_df['match_id'].max()}]")
    print(f"Val match_id range:   [{val_df['match_id'].min()} - {val_df['match_id'].max()}]")
    print(f"Test match_id range:  [{test_df['match_id'].min()} - {test_df['match_id'].max()}]")

    # Verify strictly non-overlapping temporal order
    assert train_df['match_id'].max() < val_df['match_id'].min(), "Leakage detected: Train and Val overlap in time!"
    assert val_df['match_id'].max() < test_df['match_id'].min(), "Leakage detected: Val and Test overlap in time!"

    print("\nComputing statistics strictly on TRAIN DATA ONLY...")
    stats = compute_train_features(train_df)
    print(f"Active heroes tracked: {stats['num_heroes']}")
    print(f"Train radiant win rate: {stats['global_radiant_wr']:.4f}")

    print("\nTransforming train, val, and test feature vectors...")
    X_train, wr_diff_train, matchup_train, y_train = build_feature_vectors(train_df, stats)
    X_val, wr_diff_val, matchup_val, y_val = build_feature_vectors(val_df, stats)
    X_test, wr_diff_test, matchup_test, y_test = build_feature_vectors(test_df, stats)

    # ─────────────────────────────────────────────────────────────────────────────
    # BASELINES & MODELS
    # ─────────────────────────────────────────────────────────────────────────────
    results = {}
    probs_dict = {}

    # (a) Baseline: Always predict Radiant Base Rate
    print("\n--- Evaluating Baseline (a): Radiant Prior ---")
    p_radiant_prior = np.full_like(y_test, fill_value=stats["global_radiant_wr"], dtype=float)
    results["baseline_radiant_prior"] = compute_metrics(y_test, p_radiant_prior)
    probs_dict["Radiant Prior"] = p_radiant_prior

    # (b) Baseline: Sum of Hero Win Rates
    print("--- Evaluating Baseline (b): Sum of Hero Win Rates ---")
    lr_wr = LogisticRegression(random_state=42)
    lr_wr.fit(wr_diff_train, y_train)
    p_hero_wr = lr_wr.predict_proba(wr_diff_test)[:, 1]
    results["baseline_hero_winrate_sum"] = compute_metrics(y_test, p_hero_wr)
    probs_dict["Hero Win Rates"] = p_hero_wr

    # (c) Baseline: Matchup-Only Score
    print("--- Evaluating Baseline (c): Matchup-Only Score ---")
    lr_matchup = LogisticRegression(random_state=42)
    lr_matchup.fit(matchup_train, y_train)
    p_matchup = lr_matchup.predict_proba(matchup_test)[:, 1]
    results["baseline_matchup_only"] = compute_metrics(y_test, p_matchup)
    probs_dict["Matchup Only"] = p_matchup

    print("--- Training and Evaluating (d): LightGBM Classifier ---")
    gbm = lgb.LGBMClassifier(
        n_estimators=300,
        learning_rate=0.03,
        num_leaves=31,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.5,
        reg_lambda=2.0,
        random_state=42,
        verbosity=-1
    )
    gbm.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        callbacks=[lgb.early_stopping(stopping_rounds=30, verbose=False)]
    )

    p_lgb = gbm.predict_proba(X_test)[:, 1]
    results["lightgbm"] = compute_metrics(y_test, p_lgb)
    probs_dict["LightGBM"] = p_lgb

    # Print summary table
    print("\n=======================================================")
    print("TEST SET EVALUATION SUMMARY (Strictly Time-Based, No Leakage)")
    print("=======================================================")
    print(f"{'Model / Baseline':<28} | {'Accuracy':<8} | {'Log-Loss':<8} | {'ROC-AUC':<8} | {'Brier':<8}")
    print("-" * 71)
    for model_name, m in results.items():
        print(f"{model_name:<28} | {m['accuracy']:<8.4f} | {m['log_loss']:<8.4f} | {m['roc_auc']:<8.4f} | {m['brier_score']:<8.4f}")
    print("=======================================================")

    # Save metrics.json
    metrics_payload = {
        "dataset": {
            "total_matches": n_total,
            "train_matches": len(train_df),
            "val_matches": len(val_df),
            "test_matches": len(test_df),
            "split_type": "time_based",
            "leakage_free": True
        },
        "metrics": results,
        "best_iteration": int(gbm.best_iteration_ if hasattr(gbm, "best_iteration_") and gbm.best_iteration_ else 300)
    }

    metrics_file = reports_dir / "metrics.json"
    with open(metrics_file, "w") as f:
        json.dump(metrics_payload, f, indent=2)
    print(f"\nSaved metrics to {metrics_file}")

    # Plot Calibration Curves
    print("Generating calibration curve plot...")
    plt.figure(figsize=(9, 6), dpi=150)
    plt.plot([0, 1], [0, 1], "k:", label="Perfect Calibration")

    colors = {
        "Radiant Prior": "#718096",
        "Hero Win Rates": "#3182ce",
        "Matchup Only": "#d69e2e",
        "LightGBM": "#38a169"
    }

    key_map = {
        "Hero Win Rates": "baseline_hero_winrate_sum",
        "Matchup Only": "baseline_matchup_only",
        "LightGBM": "lightgbm"
    }

    for name, p in probs_dict.items():
        if name == "Radiant Prior":
            continue  # Constant line
        prob_true, prob_pred = calibration_curve(y_test, p, n_bins=10)
        res_key = key_map.get(name, name.lower().replace(' ', '_'))
        brier_val = results.get(res_key, {}).get('brier_score', 0)
        plt.plot(prob_pred, prob_true, "s-", color=colors.get(name, "#e53e3e"), label=f"{name} (Brier: {brier_val:.4f})")

    plt.title("Model Calibration Curves on Test Set (Time-Based Split)", fontsize=13, fontweight='bold', pad=12)
    plt.xlabel("Mean Predicted Probability (Radiant Win)", fontsize=11)
    plt.ylabel("Observed Fraction of Positives", fontsize=11)
    plt.legend(loc="lower right", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    plot_file = reports_dir / "calibration_curve.png"
    plt.savefig(plot_file)
    plt.close()
    print(f"Saved calibration curve to {plot_file}")


if __name__ == "__main__":
    main()
