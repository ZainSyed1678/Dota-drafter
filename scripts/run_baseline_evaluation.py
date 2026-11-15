"""
Dota 2 Drafter - Baseline Evaluation on Clean Parquet Snapshot
Runs current baseline pipeline (k=20, lambda=0.2, LightGBM + Logistic Combiner)
on the clean Parquet snapshot and records baseline metrics to reports/baseline.json.
"""

import ast
import datetime
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml_pipeline.metrics import compute_all_metrics


def clean_team_list(x):
    """Ensure team is list of ints."""
    if isinstance(x, np.ndarray):
        return [int(i) for i in x if int(i) > 0]
    if isinstance(x, list):
        return [int(i) for i in x if int(i) > 0]
    if isinstance(x, str):
        try:
            val = ast.literal_eval(x)
            if isinstance(val, list):
                return [int(i) for i in val if int(i) > 0]
        except Exception:
            pass
        x = x.replace('[', '').replace(']', '')
        return [int(i.strip()) for i in x.split(',') if i.strip().isdigit()]
    return []


def build_lgb_features(df_in, sorted_heroes, hero_to_idx, hero_wr):
    num_heroes = len(sorted_heroes)
    X = []
    for _, row in df_in.iterrows():
        vec = np.zeros(num_heroes, dtype=np.float32)
        for h in row['radiant_team']:
            if h in hero_to_idx:
                vec[hero_to_idx[h]] = 1.0
        for h in row['dire_team']:
            if h in hero_to_idx:
                vec[hero_to_idx[h]] = -1.0
        r_wr = float(np.mean([hero_wr.get(h, 0.50) for h in row['radiant_team']]))
        d_wr = float(np.mean([hero_wr.get(h, 0.50) for h in row['dire_team']]))
        extra = [r_wr, d_wr, r_wr - d_wr]
        X.append(np.concatenate([vec, extra]))
    return np.array(X, dtype=np.float32)


def extract_score_components(df_in, hero_wr, global_prior, matchup_dict, synergy_dict):
    M_list, S_list, W_list = [], [], []
    for _, row in df_in.iterrows():
        r_team = row['radiant_team']
        d_team = row['dire_team']

        m_score = 0.0
        for r in r_team:
            prior_r = hero_wr.get(r, global_prior)
            for d in d_team:
                m_score += (matchup_dict.get((r, d), prior_r) - prior_r)
        for d in d_team:
            prior_d = hero_wr.get(d, global_prior)
            for r in r_team:
                m_score -= (matchup_dict.get((d, r), prior_d) - prior_d)
        M_list.append(m_score / 25.0)

        s_score = 0.0
        for i in range(len(r_team)):
            for j in range(i + 1, len(r_team)):
                p = (min(r_team[i], r_team[j]), max(r_team[i], r_team[j]))
                s_score += (synergy_dict.get(p, 0.50) - 0.50)
        for i in range(len(d_team)):
            for j in range(i + 1, len(d_team)):
                p = (min(d_team[i], d_team[j]), max(d_team[i], d_team[j]))
                s_score -= (synergy_dict.get(p, 0.50) - 0.50)
        S_list.append(s_score / 10.0)

        w_score = np.mean([hero_wr.get(h, 0.50) for h in r_team]) - np.mean([hero_wr.get(h, 0.50) for h in d_team])
        W_list.append(w_score)

    return np.column_stack([M_list, S_list, W_list])


def run_baseline(
    parquet_path: str = "data/snapshots/matches_clean.parquet",
    output_report: str = "reports/baseline.json"
):
    print("=" * 70)
    print("Dota 2 Drafter - Running Baseline Evaluation on Parquet Snapshot")
    print("=" * 70)
    t0 = time.time()

    path = PROJECT_ROOT / parquet_path
    if not path.exists():
        raise FileNotFoundError(f"Snapshot not found at {path}")

    print(f"Loading matches from {path}...")
    df = pd.read_parquet(path)
    df['radiant_team'] = df['radiant_team'].apply(clean_team_list)
    df['dire_team'] = df['dire_team'].apply(clean_team_list)

    # Ensure chronological order
    df = df.sort_values('match_id').reset_index(drop=True)
    total_matches = len(df)
    print(f"Loaded {total_matches:,} clean matches.")

    # Chronological Split (70% Train, 15% Val, 15% Test)
    n_train = int(total_matches * 0.70)
    n_val = int(total_matches * 0.15)

    train_df = df.iloc[:n_train].copy().reset_index(drop=True)
    val_df = df.iloc[n_train:n_train + n_val].copy().reset_index(drop=True)
    test_df = df.iloc[n_train + n_val:].copy().reset_index(drop=True)

    y_train = train_df['radiant_win'].astype(int).values
    y_val = val_df['radiant_win'].astype(int).values
    y_test = test_df['radiant_win'].astype(int).values

    print(f"Split sizes: Train={len(train_df):,} | Val={len(val_df):,} | Test={len(test_df):,}")

    # Zero leakage check
    assert train_df['match_id'].max() < val_df['match_id'].min(), "Leakage: Train overlaps Val!"
    assert val_df['match_id'].max() < test_df['match_id'].min(), "Leakage: Val overlaps Test!"

    # Active heroes in training
    all_heroes = set()
    for _, r in train_df.iterrows():
        all_heroes.update(r['radiant_team'])
        all_heroes.update(r['dire_team'])
    sorted_heroes = sorted(list(all_heroes))
    hero_to_idx = {h: i for i, h in enumerate(sorted_heroes)}

    # Baseline config: k=20, lambda=0.2
    k_matchup = 20.0
    k_synergy = 20.0
    recency_lambda = 0.2

    print("Computing recency weights and empirical-bayes matrices on train...")
    N_tr = len(train_df)
    weights = np.zeros(N_tr, dtype=np.float32)
    for idx in range(N_tr):
        pos = idx / N_tr
        weights[idx] = np.exp(-recency_lambda * (1.0 - pos))

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

    hero_winrate = {}
    for h in sorted_heroes:
        hero_winrate[h] = hero_wins[h] / hero_games[h] if hero_games[h] > 0 else 0.50
    global_prior = float(np.mean(list(hero_winrate.values()))) if hero_winrate else 0.50

    shrunk_matchup = {}
    for pair, g in matchup_games.items():
        h1, _ = pair
        prior = hero_winrate.get(h1, global_prior)
        shrunk_matchup[pair] = (matchup_wins[pair] + k_matchup * prior) / (g + k_matchup)

    shrunk_synergy = {}
    for pair, g in synergy_games.items():
        shrunk_synergy[pair] = (synergy_wins[pair] + k_synergy * 0.50) / (g + k_synergy)

    print("Building LightGBM feature representations...")
    X_lgb_train = build_lgb_features(train_df, sorted_heroes, hero_to_idx, hero_winrate)
    X_lgb_val = build_lgb_features(val_df, sorted_heroes, hero_to_idx, hero_winrate)
    X_lgb_test = build_lgb_features(test_df, sorted_heroes, hero_to_idx, hero_winrate)

    lgb_train_data = lgb.Dataset(X_lgb_train, label=y_train)
    lgb_val_data = lgb.Dataset(X_lgb_val, label=y_val, reference=lgb_train_data)

    lgb_params = {
        'objective': 'binary',
        'metric': 'binary_logloss',
        'boosting_type': 'gbdt',
        'learning_rate': 0.05,
        'num_leaves': 31,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 1,
        'min_child_samples': 20,
        'verbose': -1,
        'random_state': 42
    }

    print("Training LightGBM model with early stopping on validation fold...")
    lgb_model = lgb.train(
        lgb_params,
        lgb_train_data,
        num_boost_round=500,
        valid_sets=[lgb_val_data],
        callbacks=[lgb.early_stopping(stopping_rounds=30, verbose=False)]
    )

    lgb_preds_val = lgb_model.predict(X_lgb_val)
    lgb_preds_test = lgb_model.predict(X_lgb_test)

    print("Fitting learned stacking combiner on validation fold...")
    val_comps = extract_score_components(val_df, hero_winrate, global_prior, shrunk_matchup, shrunk_synergy)
    test_comps = extract_score_components(test_df, hero_winrate, global_prior, shrunk_matchup, shrunk_synergy)

    X_comb_val = np.column_stack([val_comps, lgb_preds_val - 0.5])
    X_comb_test = np.column_stack([test_comps, lgb_preds_test - 0.5])

    combiner = LogisticRegression(C=1.0, fit_intercept=True, random_state=42)
    combiner.fit(X_comb_val, y_val)

    comb_weights = {
        'matchup': float(combiner.coef_[0][0]),
        'synergy': float(combiner.coef_[0][1]),
        'winrate': float(combiner.coef_[0][2]),
        'model': float(combiner.coef_[0][3]),
        'intercept': float(combiner.intercept_[0]),
    }
    print(f"Combiner weights: {comb_weights}")

    # Predictions and metrics on test fold
    comb_preds_test = combiner.predict_proba(X_comb_test)[:, 1]
    overall_metrics = compute_all_metrics(y_test, comb_preds_test)

    # Slice metrics by patch
    patch_slices = {}
    for p in test_df['patch_version'].unique():
        mask = (test_df['patch_version'] == p).values
        if np.sum(mask) >= 100:
            patch_slices[str(p)] = compute_all_metrics(y_test[mask], comb_preds_test[mask])

    elapsed = round(time.time() - t0, 1)
    baseline_report = {
        "run_id": "baseline_1.4m_reproduction",
        "timestamp": datetime.datetime.now().isoformat(),
        "elapsed_seconds": elapsed,
        "dataset": {
            "snapshot_path": parquet_path,
            "total_matches": total_matches,
            "train_matches": len(train_df),
            "val_matches": len(val_df),
            "test_matches": len(test_df),
            "patches_in_dataset": list(df['patch_version'].unique())
        },
        "config": {
            "k_matchup": k_matchup,
            "k_synergy": k_synergy,
            "recency_lambda": recency_lambda,
            "split": "70/15/15 chronological"
        },
        "combiner_weights": comb_weights,
        "overall_test_metrics": overall_metrics,
        "patch_sliced_metrics": patch_slices
    }

    rep_path = PROJECT_ROOT / output_report
    rep_path.parent.mkdir(parents=True, exist_ok=True)
    with open(rep_path, 'w') as f:
        json.dump(baseline_report, f, indent=2)

    print("=" * 70)
    print(f"Baseline Evaluation Complete in {elapsed}s!")
    print(f"Overall Test Log Loss: {overall_metrics['log_loss']}")
    print(f"Overall Test Brier:    {overall_metrics['brier_score']}")
    print(f"Overall Test ROC-AUC:  {overall_metrics['roc_auc']}")
    print(f"Overall Test ECE:      {overall_metrics['ece']}")
    print(f"Report saved to: {rep_path}")
    print("=" * 70)
    return baseline_report


if __name__ == "__main__":
    run_baseline()
