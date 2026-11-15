"""
Dota 2 Drafter - Combiner Feature Ablation Runner
Fits and evaluates combiner variants by dropping each input one at a time:
[Matchup (M), Synergy (S), Winrate (W), Model (P)]
Computes paired bootstrap 95% CIs against the full combiner to quantify marginal value.
Outputs reports/<run_id>.json and reports/ablation.md.
"""

import argparse
import datetime
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml_pipeline.bootstrap import compute_paired_bootstrap_ci
from ml_pipeline.metrics import compute_all_metrics
from scripts.run_baseline_evaluation import (
    build_lgb_features,
    clean_team_list,
    extract_score_components,
)


def run_ablation(
    parquet_path: str = "data/snapshots/matches_clean.parquet",
    output_prefix: str = "ablation_1.4m"
) -> Dict[str, Any]:
    print("=" * 70)
    print("Dota 2 Drafter - Combiner Feature Ablation Runner")
    print("=" * 70)
    t0 = time.time()

    path = PROJECT_ROOT / parquet_path
    if not path.exists():
        raise FileNotFoundError(f"Snapshot not found: {path}")

    print(f"Loading data from {path}...")
    df = pd.read_parquet(path)
    df['radiant_team'] = df['radiant_team'].apply(clean_team_list)
    df['dire_team'] = df['dire_team'].apply(clean_team_list)
    df = df.sort_values('match_id').reset_index(drop=True)

    n_total = len(df)
    n_train = int(n_total * 0.70)
    n_val = int(n_total * 0.15)

    train_df = df.iloc[:n_train].copy().reset_index(drop=True)
    val_df = df.iloc[n_train:n_train + n_val].copy().reset_index(drop=True)
    test_df = df.iloc[n_train + n_val:].copy().reset_index(drop=True)

    y_train = train_df['radiant_win'].astype(int).values
    y_val = val_df['radiant_win'].astype(int).values
    y_test = test_df['radiant_win'].astype(int).values

    print(f"Dataset: Train={len(train_df):,} | Val={len(val_df):,} | Test={len(test_df):,}")

    # Compute baseline matrices on train
    all_heroes = set()
    for _, r in train_df.iterrows():
        all_heroes.update(r['radiant_team'])
        all_heroes.update(r['dire_team'])
    sorted_heroes = sorted(list(all_heroes))
    hero_to_idx = {h: i for i, h in enumerate(sorted_heroes)}

    k_matchup = 20.0
    k_synergy = 20.0
    recency_lambda = 0.2

    N_tr = len(train_df)
    weights = np.zeros(N_tr, dtype=np.float32)
    for idx in range(N_tr):
        weights[idx] = np.exp(-recency_lambda * (1.0 - (idx / N_tr)))

    from collections import defaultdict
    hero_wins = defaultdict(float)
    hero_games = defaultdict(float)
    matchup_wins = defaultdict(float)
    matchup_games = defaultdict(float)
    synergy_wins = defaultdict(float)
    synergy_games = defaultdict(float)

    for idx, row in train_df.iterrows():
        w = float(weights[idx])
        r_win = 1.0 if row['radiant_win'] else 0.0
        r_t = row['radiant_team']
        d_t = row['dire_team']

        for h in r_t:
            hero_wins[h] += w * r_win
            hero_games[h] += w
        for h in d_t:
            hero_wins[h] += w * (1.0 - r_win)
            hero_games[h] += w

        for h1 in r_t:
            for h2 in d_t:
                matchup_wins[(h1, h2)] += w * r_win
                matchup_games[(h1, h2)] += w
                matchup_wins[(h2, h1)] += w * (1.0 - r_win)
                matchup_games[(h2, h1)] += w

        for i in range(len(r_t)):
            for j in range(i + 1, len(r_t)):
                p1 = (min(r_t[i], r_t[j]), max(r_t[i], r_t[j]))
                synergy_wins[p1] += w * r_win
                synergy_games[p1] += w

        for i in range(len(d_t)):
            for j in range(i + 1, len(d_t)):
                p2 = (min(d_t[i], d_t[j]), max(d_t[i], d_t[j]))
                synergy_wins[p2] += w * (1.0 - r_win)
                synergy_games[p2] += w

    hero_winrate = {h: hero_wins[h] / hero_games[h] if hero_games[h] > 0 else 0.50 for h in sorted_heroes}
    global_prior = float(np.mean(list(hero_winrate.values())))

    shrunk_matchup = {}
    for pair, g in matchup_games.items():
        h1, _ = pair
        prior = hero_winrate.get(h1, global_prior)
        shrunk_matchup[pair] = (matchup_wins[pair] + k_matchup * prior) / (g + k_matchup)

    shrunk_synergy = {}
    for pair, g in synergy_games.items():
        shrunk_synergy[pair] = (synergy_wins[pair] + k_synergy * 0.50) / (g + k_synergy)

    print("Extracting score components [M, S, W]...")
    val_comps = extract_score_components(val_df, hero_winrate, global_prior, shrunk_matchup, shrunk_synergy)
    test_comps = extract_score_components(test_df, hero_winrate, global_prior, shrunk_matchup, shrunk_synergy)

    # Train LightGBM for P component
    import lightgbm as lgb
    X_lgb_train = build_lgb_features(train_df, sorted_heroes, hero_to_idx, hero_winrate)
    X_lgb_val = build_lgb_features(val_df, sorted_heroes, hero_to_idx, hero_winrate)
    X_lgb_test = build_lgb_features(test_df, sorted_heroes, hero_to_idx, hero_winrate)

    lgb_train_data = lgb.Dataset(X_lgb_train, label=y_train)
    lgb_val_data = lgb.Dataset(X_lgb_val, label=y_val, reference=lgb_train_data)
    lgb_model = lgb.train(
        {
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
        },
        lgb_train_data,
        num_boost_round=500,
        valid_sets=[lgb_val_data],
        callbacks=[lgb.early_stopping(stopping_rounds=30, verbose=False)]
    )
    lgb_preds_val = (lgb_model.predict(X_lgb_val) - 0.5).reshape(-1, 1)
    lgb_preds_test = (lgb_model.predict(X_lgb_test) - 0.5).reshape(-1, 1)

    # Individual components: M=0, S=1, W=2, P=3
    M_val, S_val, W_val = val_comps[:, 0:1], val_comps[:, 1:2], val_comps[:, 2:3]
    M_test, S_test, W_test = test_comps[:, 0:1], test_comps[:, 1:2], test_comps[:, 2:3]

    configs = {
        "full_combiner": {
            "cols_val": np.column_stack([M_val, S_val, W_val, lgb_preds_val]),
            "cols_test": np.column_stack([M_test, S_test, W_test, lgb_preds_test]),
            "desc": "Full Combiner: [Matchup, Synergy, Winrate, Model]"
        },
        "drop_matchup": {
            "cols_val": np.column_stack([S_val, W_val, lgb_preds_val]),
            "cols_test": np.column_stack([S_test, W_test, lgb_preds_test]),
            "desc": "Drop Matchup: [Synergy, Winrate, Model]"
        },
        "drop_synergy": {
            "cols_val": np.column_stack([M_val, W_val, lgb_preds_val]),
            "cols_test": np.column_stack([M_test, W_test, lgb_preds_test]),
            "desc": "Drop Synergy: [Matchup, Winrate, Model]"
        },
        "drop_winrate": {
            "cols_val": np.column_stack([M_val, S_val, lgb_preds_val]),
            "cols_test": np.column_stack([M_test, S_test, lgb_preds_test]),
            "desc": "Drop Winrate: [Matchup, Synergy, Model]"
        },
        "drop_model": {
            "cols_val": np.column_stack([M_val, S_val, W_val]),
            "cols_test": np.column_stack([M_test, S_test, W_test]),
            "desc": "Drop Model: [Matchup, Synergy, Winrate] (Heuristic Only)"
        },
        "model_only": {
            "cols_val": lgb_preds_val,
            "cols_test": lgb_preds_test,
            "desc": "Model Only: [LightGBM Probability]"
        }
    }

    results = {}
    preds_dict = {}

    print("\nFitting combiner variants...")
    for name, cfg in configs.items():
        clf = LogisticRegression(C=1.0, fit_intercept=True, random_state=42)
        clf.fit(cfg["cols_val"], y_val)
        probs = clf.predict_proba(cfg["cols_test"])[:, 1]
        preds_dict[name] = probs
        metrics = compute_all_metrics(y_test, probs)
        results[name] = {
            "description": cfg["desc"],
            "metrics": metrics,
            "coefficients": [float(c) for c in clf.coef_[0]],
            "intercept": float(clf.intercept_[0])
        }
        print(f"  {name:15s} -> Log Loss: {metrics['log_loss']:.4f} | ROC-AUC: {metrics['roc_auc']:.4f} | Brier: {metrics['brier_score']:.4f}")

    # Bootstrap CIs comparing each ablation against Full Combiner
    print("\nComputing bootstrap 95% CIs against Full Combiner...")
    full_probs = preds_dict["full_combiner"]
    bootstrap_comparisons = {}

    for name in configs:
        if name == "full_combiner":
            continue
        cand_probs = preds_dict[name]
        ci_res = compute_paired_bootstrap_ci(
            y_true=y_test,
            prob_baseline=full_probs,
            prob_candidate=cand_probs,
            n_bootstraps=1000,
            metric="log_loss"
        )
        bootstrap_comparisons[name] = ci_res
        diff = ci_res["diff_mean"]
        ci_l = ci_res["ci_lower"]
        ci_u = ci_res["ci_upper"]
        print(f"  {name:15s} vs Full -> Delta Log-Loss: {diff:+.5f} (95% CI: [{ci_l:+.5f}, {ci_u:+.5f}])")

    ablation_report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "elapsed_seconds": round(time.time() - t0, 1),
        "results": results,
        "bootstrap_vs_full": bootstrap_comparisons
    }

    # Save JSON report
    rep_dir = PROJECT_ROOT / "reports"
    rep_dir.mkdir(parents=True, exist_ok=True)
    json_path = rep_dir / f"{output_prefix}.json"
    with open(json_path, 'w') as f:
        json.dump(ablation_report, f, indent=2)

    # Save Markdown summary
    md_path = rep_dir / "ablation.md"
    md_content = f"""# Combiner Feature Ablation Report (1.4M Dataset)

**Date**: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Dataset**: 1,475,139 matches (Train: 70%, Val: 15%, Test: 15%)  
**Bootstrap Iterations**: 1,000 paired resamples (95% Confidence Interval)

## Ablation Results Summary

| Model Configuration | Log Loss | ROC-AUC | Brier Score | ECE | $\\Delta$ Log Loss vs Full | 95% Bootstrap CI | Significant Deficit? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    full_ll = results["full_combiner"]["metrics"]["log_loss"]
    for name, data in results.items():
        m = data["metrics"]
        if name == "full_combiner":
            delta_str = "0.0000 (Baseline)"
            ci_str = "—"
            sig_str = "—"
        else:
            b = bootstrap_comparisons[name]
            delta_str = f"{b['diff_mean']:+.4f}"
            ci_str = f"[{b['ci_lower']:+.4f}, {b['ci_upper']:+.4f}]"
            # If delta > 0 and CI lower > 0, dropping this component significantly hurt performance
            sig_str = "YES (Hurt)" if b["ci_lower"] > 0 else "No"

        md_content += f"| **{name}** | {m['log_loss']:.4f} | {m['roc_auc']:.4f} | {m['brier_score']:.4f} | {m['ece']:.4f} | {delta_str} | {ci_str} | {sig_str} |\n"

    with open(md_path, 'w') as f:
        f.write(md_content)

    print(f"\nAblation reports saved to:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")
    return ablation_report


if __name__ == "__main__":
    run_ablation()
