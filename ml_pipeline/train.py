"""
Dota 2 Drafter - Leakage-Free Training Pipeline with Empirical-Bayes Shrinkage & Learned Combiner
Implements Phase 2 & Phase 4:
- Strict chronological time-based split (Train 70%, Validation 15%, Test 15%)
- Patch-aware recency weighting configured via training_config.json
- Empirical-Bayes / Beta-prior shrinkage for matchup and synergy matrices
- Sample size and confidence level tracking
- LightGBM model training with early stopping
- Learned combination weights via Logistic Regression on the validation slice
- Model versioning: writes to model/<version>/ with metadata.json
- Records data freshness (latest match ID, patch, match count, git commit hash)
"""

import argparse
import ast
import datetime
import json
import os
import pickle
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import requests
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score


def clean_team(x):
    """Clean team string or list into list of valid hero integers."""
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


def get_git_commit_hash():
    """Retrieve current git commit hash."""
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"


def load_hero_metadata():
    """Load hero names and roles from OpenDota API with local cache fallback."""
    try:
        resp = requests.get("https://api.opendota.com/api/heroes", timeout=8)
        if resp.status_code == 200:
            hero_data = resp.json()
            hero_map = {int(h['id']): h['localized_name'] for h in hero_data}
            api_roles = {int(h['id']): h.get('roles', []) for h in hero_data}

            hero_roles = {}
            for hid, roles in api_roles.items():
                clean = []
                if "Carry" in roles: clean.append("carry")
                if "Nuker" in roles: clean.append("mid")
                if "Initiator" in roles or "Durable" in roles: clean.append("offlane")
                if "Support" in roles: clean.append("support")
                if not clean: clean = ["offlane"]
                hero_roles[hid] = list(set(clean))
            return hero_map, hero_roles
    except Exception as e:
        print(f"Warning: OpenDota API unavailable ({e}), falling back to cached hero metadata.")

    cache_dir = Path(__file__).resolve().parent.parent / "backend" / "model"
    hero_map_path = cache_dir / "hero_map.pkl"
    roles_path = cache_dir / "roles.pkl"
    if hero_map_path.exists() and roles_path.exists():
        with open(hero_map_path, "rb") as f: hero_map = pickle.load(f)
        with open(roles_path, "rb") as f: hero_roles = pickle.load(f)
        return hero_map, hero_roles

    return {}, {}


def build_lgb_features(df_in, sorted_heroes, hero_to_idx, hero_wr):
    """Build input vectors for LightGBM."""
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
    """Extract symmetric draft score components: Matchup (M), Synergy (S), and Meta WR (W)."""
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


def train_pipeline(
    input_csv: str,
    output_dir: str,
    config_path: str = "ml_pipeline/training_config.json",
    version: str = "v2.2.0"
):
    print("=" * 70)
    print(f"Dota 2 Drafter - Model Training & Versioning Pipeline ({version})")
    print("=" * 70)

    # 1. Load config
    cfg_file = Path(config_path)
    if cfg_file.exists():
        with open(cfg_file, "r") as f:
            cfg = json.load(f)
        print(f"Loaded training config from {cfg_file}")
    else:
        cfg = {
            "recency": {"decay_type": "patch_exponential", "lambda_time": 0.2, "patch_weights": {"7.35d": 1.0}, "default_patch_weight": 0.5},
            "shrinkage": {"k_matchup": 20.0, "k_synergy": 20.0},
            "splits": {"train_ratio": 0.70, "val_ratio": 0.15, "test_ratio": 0.15}
        }

    k_matchup = cfg.get("shrinkage", {}).get("k_matchup", 20.0)
    k_synergy = cfg.get("shrinkage", {}).get("k_synergy", 20.0)
    recency_lambda = cfg.get("recency", {}).get("lambda_time", 0.2)
    patch_weights = cfg.get("recency", {}).get("patch_weights", {})
    default_patch_weight = cfg.get("recency", {}).get("default_patch_weight", 0.5)

    input_path = Path(input_csv)
    if not input_path.exists():
        raise FileNotFoundError(f"Dataset not found at {input_path}")

    print(f"Loading match data from {input_path}...")
    df = pd.read_csv(input_path)
    df['radiant_team'] = df['radiant_team'].apply(clean_team)
    df['dire_team'] = df['dire_team'].apply(clean_team)

    valid_mask = (
        df['radiant_team'].apply(lambda t: len(t) == 5 and len(set(t)) == 5) &
        df['dire_team'].apply(lambda t: len(t) == 5 and len(set(t)) == 5) &
        df.apply(lambda r: len(set(r['radiant_team']) & set(r['dire_team'])) == 0, axis=1)
    )
    df = df[valid_mask].sort_values('match_id').reset_index(drop=True)
    total_valid = len(df)
    print(f"Valid 5v5 matches: {total_valid}")

    # Freshness info
    latest_match_id = int(df['match_id'].max())
    latest_patch = str(df['patch_version'].iloc[-1]) if 'patch_version' in df.columns else "unknown"

    # Time-based split
    train_ratio = cfg.get("splits", {}).get("train_ratio", 0.70)
    val_ratio = cfg.get("splits", {}).get("val_ratio", 0.15)
    n_train = int(total_valid * train_ratio)
    n_val = int(total_valid * val_ratio)

    train_df = df.iloc[:n_train].copy().reset_index(drop=True)
    val_df = df.iloc[n_train:n_train + n_val].copy().reset_index(drop=True)
    test_df = df.iloc[n_train + n_val:].copy().reset_index(drop=True)

    y_train = train_df['radiant_win'].astype(int).values
    y_val = val_df['radiant_win'].astype(int).values
    y_test = test_df['radiant_win'].astype(int).values

    print(f"Splits: Train={len(train_df)} | Val={len(val_df)} | Test={len(test_df)}")

    # Heroes in training
    all_heroes = set()
    for _, r in train_df.iterrows():
        all_heroes.update(r['radiant_team'])
        all_heroes.update(r['dire_team'])
    sorted_heroes = sorted(list(all_heroes))
    hero_to_idx = {h: i for i, h in enumerate(sorted_heroes)}

    hero_map, hero_roles = load_hero_metadata()
    for h in sorted_heroes:
        if h not in hero_map:
            hero_map[h] = f"Hero_{h}"
        if h not in hero_roles:
            hero_roles[h] = ["offlane"]

    # Patch-aware recency weighting
    N_tr = len(train_df)
    weights = np.zeros(N_tr)
    for idx, row in train_df.iterrows():
        pos = idx / N_tr
        time_factor = np.exp(-recency_lambda * (1.0 - pos))
        patch_ver = str(row.get('patch_version', ''))
        patch_factor = patch_weights.get(patch_ver, default_patch_weight)
        weights[idx] = time_factor * patch_factor

    print(f"Computed patch-aware recency weights (mean={np.mean(weights):.3f}, min={np.min(weights):.3f}, max={np.max(weights):.3f})")

    hero_wins = defaultdict(float)
    hero_games = defaultdict(float)
    matchup_wins = defaultdict(float)
    matchup_games = defaultdict(float)
    synergy_wins = defaultdict(float)
    synergy_games = defaultdict(float)

    for idx, row in train_df.iterrows():
        w = weights[idx]
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
    hero_avg_matchup = {h: hero_winrate.get(h, 0.50) for h in sorted_heroes}

    # Empirical-Bayes Shrinkage
    shrunk_matchup = {}
    matchup_sample_sizes = {}
    for pair, g in matchup_games.items():
        h1, h2 = pair
        prior = hero_winrate.get(h1, global_prior)
        shrunk_matchup[pair] = (matchup_wins[pair] + k_matchup * prior) / (g + k_matchup)
        matchup_sample_sizes[pair] = int(round(g))

    shrunk_synergy = {}
    synergy_sample_sizes = {}
    for pair, g in synergy_games.items():
        shrunk_synergy[pair] = (synergy_wins[pair] + k_synergy * 0.50) / (g + k_synergy)
        synergy_sample_sizes[pair] = int(round(g))

    # Train LightGBM
    X_lgb_train = build_lgb_features(train_df, sorted_heroes, hero_to_idx, hero_winrate)
    X_lgb_val = build_lgb_features(val_df, sorted_heroes, hero_to_idx, hero_winrate)
    X_lgb_test = build_lgb_features(test_df, sorted_heroes, hero_to_idx, hero_winrate)

    lgb_train_data = lgb.Dataset(X_lgb_train, label=y_train)
    lgb_val_data = lgb.Dataset(X_lgb_val, label=y_val, reference=lgb_train_data)

    lgb_params = {
        'objective': 'binary',
        'metric': 'binary_logloss',
        'boosting_type': 'gbdt',
        'learning_rate': 0.03,
        'num_leaves': 31,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 1,
        'min_child_samples': 20,
        'verbose': -1,
        'random_state': 42
    }

    lgb_model = lgb.train(
        lgb_params,
        lgb_train_data,
        num_boost_round=600,
        valid_sets=[lgb_val_data],
        callbacks=[lgb.early_stopping(stopping_rounds=30, verbose=False)]
    )

    lgb_preds_val = lgb_model.predict(X_lgb_val)
    lgb_preds_test = lgb_model.predict(X_lgb_test)

    # Learned Combiner
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
        'k_matchup': float(k_matchup),
        'k_synergy': float(k_synergy),
        'recency_lambda': float(recency_lambda),
    }

    comb_preds_test = combiner.predict_proba(X_comb_test)[:, 1]
    comb_test_acc = accuracy_score(y_test, comb_preds_test >= 0.5)
    comb_test_loss = log_loss(y_test, comb_preds_test)
    comb_test_auc = roc_auc_score(y_test, comb_preds_test)
    comb_test_brier = brier_score_loss(y_test, comb_preds_test)

    print(f"Learned Combiner Test Metrics: Acc={comb_test_acc*100:.2f}%, AUC={comb_test_auc:.4f}, Loss={comb_test_loss:.4f}")

    # Model Versioning: Save to model/<version>/
    root_dir = Path(output_dir)
    ver_dir = root_dir / version
    ver_dir.mkdir(parents=True, exist_ok=True)
    print(f"Saving model artifacts to version directory: {ver_dir}")

    git_hash = get_git_commit_hash()
    data_freshness = {
        "latest_match_id": latest_match_id,
        "latest_patch": latest_patch,
        "match_count": total_valid,
        "training_matches": len(train_df),
        "validation_matches": len(val_df),
        "test_matches": len(test_df),
        "latest_match_timestamp": datetime.datetime.now().isoformat()
    }

    metadata = {
        "version": version,
        "trained_at": datetime.datetime.now().isoformat(),
        "git_commit": git_hash,
        "data_freshness": data_freshness,
        "config": cfg,
        "learned_weights": comb_weights,
        "test_metrics": {
            "accuracy": round(float(comb_test_acc), 4),
            "log_loss": round(float(comb_test_loss), 4),
            "roc_auc": round(float(comb_test_auc), 4),
            "brier_score": round(float(comb_test_brier), 4)
        }
    }

    for target_dir in [ver_dir, root_dir]:
        with open(target_dir / "model.pkl", "wb") as f: pickle.dump(lgb_model, f)
        with open(target_dir / "hero_map.pkl", "wb") as f: pickle.dump(hero_map, f)
        with open(target_dir / "roles.pkl", "wb") as f: pickle.dump(hero_roles, f)
        with open(target_dir / "hero_winrate.pkl", "wb") as f: pickle.dump(hero_winrate, f)
        with open(target_dir / "hero_avg_matchup.pkl", "wb") as f: pickle.dump(hero_avg_matchup, f)
        with open(target_dir / "matchup.pkl", "wb") as f: pickle.dump(shrunk_matchup, f)
        with open(target_dir / "matchup_samples.pkl", "wb") as f: pickle.dump(matchup_sample_sizes, f)
        with open(target_dir / "synergy.pkl", "wb") as f: pickle.dump(shrunk_synergy, f)
        with open(target_dir / "synergy_samples.pkl", "wb") as f: pickle.dump(synergy_sample_sizes, f)
        with open(target_dir / "combiner_weights.pkl", "wb") as f: pickle.dump(comb_weights, f)
        with open(target_dir / "metadata.json", "w") as f: json.dump(metadata, f, indent=2)

    # Copy heroes_metadata.json if present
    src_meta = root_dir / "heroes_metadata.json"
    if src_meta.exists():
        shutil.copy2(src_meta, ver_dir / "heroes_metadata.json")

    print(f"Successfully saved versioned model to {ver_dir} and synced to {root_dir}")
    return comb_weights, metadata


def main():
    parser = argparse.ArgumentParser(description="Train Dota 2 Drafter models with versioning")
    parser.add_argument("--input_csv", type=str, default="notebooks/matches.csv", help="Path to matches CSV")
    default_out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "model")
    parser.add_argument("--output_dir", type=str, default=default_out, help="Output directory for model artifacts")
    parser.add_argument("--config", type=str, default="ml_pipeline/training_config.json", help="Path to training config JSON")
    parser.add_argument("--version", type=str, default="v2.2.0", help="Model version identifier")
    args = parser.parse_args()

    train_pipeline(
        input_csv=args.input_csv,
        output_dir=args.output_dir,
        config_path=args.config,
        version=args.version
    )


if __name__ == "__main__":
    main()
