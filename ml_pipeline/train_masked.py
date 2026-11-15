"""
Dota 2 Drafter - Partial-Draft (Masked) LightGBM Training Pipeline
Trains gradient boosted decision trees on realistic partial draft states (0-9 revealed heroes)
with explicit mask channels and draft progress indicators.
"""

import argparse
import datetime
import json
import pickle
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml_pipeline.adaptive_shrinkage import (
    compute_adaptive_matchup_shrinkage,
    compute_adaptive_synergy_shrinkage,
)
from ml_pipeline.masked_data import (
    build_masked_feature_vector,
    generate_masked_draft_sample,
)
from ml_pipeline.metrics import compute_all_metrics
from scripts.run_baseline_evaluation import clean_team_list


def extract_masked_score_components(
    masked_samples: List[Dict],
    hero_winrate: Dict[int, float],
    global_prior: float,
    matchup_dict: Dict[Tuple[int, int], float],
    synergy_dict: Dict[Tuple[int, int], float]
) -> np.ndarray:
    """Extract score components [M, S, W, progress] under partial draft masking."""
    M_list, S_list, W_list, Prog_list = [], [], [], []

    for s in masked_samples:
        r_team = s["revealed_radiant"]
        d_team = s["revealed_dire"]
        n_r = len(r_team)
        n_d = len(d_team)

        m_score = 0.0
        if n_r > 0 and n_d > 0:
            for r in r_team:
                prior_r = hero_winrate.get(r, global_prior)
                for d in d_team:
                    m_score += (matchup_dict.get((r, d), prior_r) - prior_r)
            for d in d_team:
                prior_d = hero_winrate.get(d, global_prior)
                for r in r_team:
                    m_score -= (matchup_dict.get((d, r), prior_d) - prior_d)
            m_score /= float(n_r * n_d)
        M_list.append(m_score)

        s_score = 0.0
        r_pairs = 0
        for i in range(len(r_team)):
            for j in range(i + 1, len(r_team)):
                p = (min(r_team[i], r_team[j]), max(r_team[i], r_team[j]))
                s_score += (synergy_dict.get(p, 0.50) - 0.50)
                r_pairs += 1
        d_pairs = 0
        for i in range(len(d_team)):
            for j in range(i + 1, len(d_team)):
                p = (min(d_team[i], d_team[j]), max(d_team[i], d_team[j]))
                s_score -= (synergy_dict.get(p, 0.50) - 0.50)
                d_pairs += 1
        total_pairs = r_pairs + d_pairs
        s_score = (s_score / float(total_pairs)) if total_pairs > 0 else 0.0
        S_list.append(s_score)

        r_wr = float(np.mean([hero_winrate.get(h, global_prior) for h in r_team])) if n_r > 0 else global_prior
        d_wr = float(np.mean([hero_winrate.get(h, global_prior) for h in d_team])) if n_d > 0 else global_prior
        W_list.append(r_wr - d_wr)
        Prog_list.append((n_r + n_d) / 10.0)

    return np.column_stack([M_list, S_list, W_list, Prog_list])


def train_masked_model(
    parquet_path: str = "data/snapshots/matches_clean.parquet",
    output_version: str = "v2026.11.15-masked",
    max_train_samples: int = 300000,
    random_state: int = 42
) -> Dict:
    print("=" * 70)
    print(f"Dota 2 Drafter - Training Masked-Draft LightGBM Model ({output_version})")
    print("=" * 70)
    t0 = time.time()
    rng = np.random.RandomState(random_state)

    path = PROJECT_ROOT / parquet_path
    if not path.exists():
        raise FileNotFoundError(f"Snapshot not found: {path}")

    df = pd.read_parquet(path)
    df['radiant_team'] = df['radiant_team'].apply(clean_team_list)
    df['dire_team'] = df['dire_team'].apply(clean_team_list)
    df = df.sort_values('match_id').reset_index(drop=True)

    n_total = len(df)
    n_train = min(int(n_total * 0.70), max_train_samples)
    n_val = min(int(n_total * 0.15), 50000)
    n_test = min(int(n_total * 0.15), 50000)

    train_df = df.iloc[:n_train].copy().reset_index(drop=True)
    val_df = df.iloc[n_train:n_train + n_val].copy().reset_index(drop=True)
    test_df = df.iloc[n_train + n_val:n_train + n_val + n_test].copy().reset_index(drop=True)

    all_heroes = set()
    for _, r in train_df.iterrows():
        all_heroes.update(r['radiant_team'])
        all_heroes.update(r['dire_team'])
    sorted_heroes = sorted(list(all_heroes))
    hero_to_idx = {h: i for i, h in enumerate(sorted_heroes)}

    print(f"Dataset: Train={len(train_df):,} | Val={len(val_df):,} | Test={len(test_df):,}")
    print(f"Active heroes tracked: {len(sorted_heroes)}")

    # 1. Compute empirical-bayes adaptive matrices strictly on train
    from collections import defaultdict
    hero_wins = defaultdict(float)
    hero_games = defaultdict(float)
    matchup_wins = defaultdict(float)
    matchup_games = defaultdict(float)
    synergy_wins = defaultdict(float)
    synergy_games = defaultdict(float)

    for _, row in train_df.iterrows():
        rw = 1.0 if row['radiant_win'] else 0.0
        r_t = row['radiant_team']
        d_t = row['dire_team']

        for h in r_t:
            hero_wins[h] += rw
            hero_games[h] += 1.0
        for h in d_t:
            hero_wins[h] += (1.0 - rw)
            hero_games[h] += 1.0

        for h1 in r_t:
            for h2 in d_t:
                matchup_wins[(h1, h2)] += rw
                matchup_games[(h1, h2)] += 1.0
                matchup_wins[(h2, h1)] += (1.0 - rw)
                matchup_games[(h2, h1)] += 1.0

        for i in range(len(r_t)):
            for j in range(i + 1, len(r_t)):
                p1 = (min(r_t[i], r_t[j]), max(r_t[i], r_t[j]))
                synergy_wins[p1] += rw
                synergy_games[p1] += 1.0

        for i in range(len(d_t)):
            for j in range(i + 1, len(d_t)):
                p2 = (min(d_t[i], d_t[j]), max(d_t[i], d_t[j]))
                synergy_wins[p2] += (1.0 - rw)
                synergy_games[p2] += 1.0

    hero_winrate = {h: hero_wins[h] / hero_games[h] if hero_games[h] > 0 else 0.50 for h in sorted_heroes}
    global_prior = float(np.mean(list(hero_winrate.values())))

    shrunk_matchup, _ = compute_adaptive_matchup_shrinkage(matchup_wins, matchup_games, hero_winrate, global_prior, base_k=15.0)
    shrunk_synergy, _ = compute_adaptive_synergy_shrinkage(synergy_wins, synergy_games, base_k=15.0)

    # 2. Generate masked samples for Train, Val, Test
    print("Generating masked draft training states (0-9 revealed heroes)...")
    train_samples = [generate_masked_draft_sample(r['radiant_team'], r['dire_team'], int(r['radiant_win']), rng) for _, r in train_df.iterrows()]
    val_samples = [generate_masked_draft_sample(r['radiant_team'], r['dire_team'], int(r['radiant_win']), rng) for _, r in val_df.iterrows()]
    test_samples = [generate_masked_draft_sample(r['radiant_team'], r['dire_team'], int(r['radiant_win']), rng) for _, r in test_df.iterrows()]

    X_train = np.array([build_masked_feature_vector(s["revealed_radiant"], s["revealed_dire"], hero_to_idx, hero_winrate, global_prior) for s in train_samples], dtype=np.float32)
    y_train = np.array([s["radiant_win"] for s in train_samples], dtype=np.int32)

    X_val = np.array([build_masked_feature_vector(s["revealed_radiant"], s["revealed_dire"], hero_to_idx, hero_winrate, global_prior) for s in val_samples], dtype=np.float32)
    y_val = np.array([s["radiant_win"] for s in val_samples], dtype=np.int32)

    X_test = np.array([build_masked_feature_vector(s["revealed_radiant"], s["revealed_dire"], hero_to_idx, hero_winrate, global_prior) for s in test_samples], dtype=np.float32)
    y_test = np.array([s["radiant_win"] for s in test_samples], dtype=np.int32)

    # 3. Train LightGBM model on masked drafts
    print("Fitting LightGBM booster on partial draft features...")
    lgb_train = lgb.Dataset(X_train, label=y_train)
    lgb_val = lgb.Dataset(X_val, label=y_val, reference=lgb_train)

    params = {
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

    lgb_model = lgb.train(
        params,
        lgb_train,
        num_boost_round=600,
        valid_sets=[lgb_val],
        callbacks=[lgb.early_stopping(stopping_rounds=30, verbose=False)]
    )

    preds_val_lgb = lgb_model.predict(X_val)
    preds_test_lgb = lgb_model.predict(X_test)

    # 4. Fit Stacking Combiner on masked validation fold
    print("Fitting stacking combiner under masked conditions...")
    val_comps = extract_masked_score_components(val_samples, hero_winrate, global_prior, shrunk_matchup, shrunk_synergy)
    test_comps = extract_masked_score_components(test_samples, hero_winrate, global_prior, shrunk_matchup, shrunk_synergy)

    X_comb_val = np.column_stack([val_comps, preds_val_lgb - 0.5])
    X_comb_test = np.column_stack([test_comps, preds_test_lgb - 0.5])

    combiner = LogisticRegression(C=1.0, fit_intercept=True, random_state=42)
    combiner.fit(X_comb_val, y_val)

    comb_preds_test = combiner.predict_proba(X_comb_test)[:, 1]

    # Metrics sliced by number of revealed heroes
    test_reveals = np.array([s["total_revealed"] for s in test_samples])
    overall_metrics = compute_all_metrics(y_test, comb_preds_test)

    reveal_sliced_metrics = {}
    for k in range(11):
        mask = (test_reveals == k)
        if np.sum(mask) >= 30:
            reveal_sliced_metrics[f"reveal_{k}"] = compute_all_metrics(y_test[mask], comb_preds_test[mask])

    print("=" * 70)
    print("Masked Training Results:")
    print(f"  Overall Masked Log Loss: {overall_metrics['log_loss']:.4f}")
    print(f"  Overall Masked Brier:    {overall_metrics['brier_score']:.4f}")
    print(f"  Overall Masked ROC-AUC:  {overall_metrics['roc_auc']:.4f}")
    print(f"  Overall Masked ECE:      {overall_metrics['ece']:.4f}")
    print("Calibration by reveal depth:")
    for rev_key, m in reveal_sliced_metrics.items():
        print(f"    {rev_key:10s} -> Log Loss: {m['log_loss']:.4f} | ECE: {m['ece']:.4f} | Brier: {m['brier_score']:.4f}")

    # Save artifacts into new versioned folder
    out_dir = PROJECT_ROOT / "backend" / "model" / output_version
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "model.pkl", "wb") as f:
        pickle.dump(lgb_model, f)
    with open(out_dir / "combiner.pkl", "wb") as f:
        pickle.dump(combiner, f)
    with open(out_dir / "hero_winrate.pkl", "wb") as f:
        pickle.dump(hero_winrate, f)
    with open(out_dir / "matchup.pkl", "wb") as f:
        pickle.dump(shrunk_matchup, f)
    with open(out_dir / "synergy.pkl", "wb") as f:
        pickle.dump(shrunk_synergy, f)
    with open(out_dir / "matchup_samples.pkl", "wb") as f:
        pickle.dump({k: int(round(v)) for k, v in matchup_games.items()}, f)
    with open(out_dir / "synergy_samples.pkl", "wb") as f:
        pickle.dump({k: int(round(v)) for k, v in synergy_games.items()}, f)
    with open(out_dir / "combiner_weights.pkl", "wb") as f:
        pickle.dump({
            "matchup": float(combiner.coef_[0][0]),
            "synergy": float(combiner.coef_[0][1]),
            "winrate": float(combiner.coef_[0][2]),
            "progress": float(combiner.coef_[0][3]),
            "model": float(combiner.coef_[0][4]),
            "intercept": float(combiner.intercept_[0]),
            "is_masked": True
        }, f)

    meta = {
        "version": output_version,
        "trained_at": datetime.datetime.now().isoformat(),
        "is_masked": True,
        "feature_dim": X_train.shape[1],
        "data_freshness": {
            "latest_match_id": int(df["match_id"].max()) if "match_id" in df else 9087939856,
            "latest_patch": str(df["patch_version"].dropna().iloc[-1]) if "patch_version" in df and len(df["patch_version"].dropna()) > 0 else "7.35f",
            "match_count": len(df),
            "training_matches": len(train_df),
            "validation_matches": len(val_df),
            "test_matches": len(test_df),
            "latest_match_timestamp": datetime.datetime.now().isoformat()
        },
        "metrics": overall_metrics,
        "sliced_by_reveal": reveal_sliced_metrics,
        "combiner_weights": {
            "matchup": float(combiner.coef_[0][0]),
            "synergy": float(combiner.coef_[0][1]),
            "winrate": float(combiner.coef_[0][2]),
            "progress": float(combiner.coef_[0][3]),
            "model": float(combiner.coef_[0][4]),
            "intercept": float(combiner.intercept_[0])
        }
    }
    with open(out_dir / "metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Artifacts saved to {out_dir}")
    print("=" * 70)
    return meta


if __name__ == "__main__":
    train_masked_model()
