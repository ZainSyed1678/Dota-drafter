"""Training and evaluation pipeline for HeroEmbeddingDeepSet model.

Trains on chronological training fold, evaluates on validation fold,
runs bootstrap CI comparison against baseline, and saves artifacts.
"""

import sys
import os
import json
import time
import pickle
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml_pipeline.metrics import compute_all_metrics
from ml_pipeline.bootstrap import compute_paired_bootstrap_ci
from ml_pipeline.masked_data import (
    generate_masked_draft_sample,
    build_masked_feature_vector
)
from ml_pipeline.train_masked import extract_masked_score_components

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import TensorDataset, DataLoader
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from ml_pipeline.embedding_model import HeroEmbeddingDeepSet, build_embedding_features


def generate_embedding_dataset(
    samples: List[Dict],
    hero_to_idx: Dict[int, int],
    hero_winrates: Dict[int, float]
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Generate (rad_indices, dire_indices, state_features, targets) arrays from sample dicts."""
    rad_list = []
    dire_list = []
    state_list = []
    target_list = []

    for s in samples:
        r_rev = s["revealed_radiant"]
        d_rev = s["revealed_dire"]
        label = float(s["radiant_win"])

        r_slots, d_slots, s_feat = build_embedding_features(
            r_rev, d_rev, hero_to_idx, hero_winrates
        )
        rad_list.append(r_slots)
        dire_list.append(d_slots)
        state_list.append(s_feat)
        target_list.append(label)

    return (
        np.array(rad_list, dtype=np.int64),
        np.array(dire_list, dtype=np.int64),
        np.array(state_list, dtype=np.float32),
        np.array(target_list, dtype=np.float32)
    )


def run_embedding_pipeline(
    parquet_path: str = "data/snapshots/matches_clean.parquet",
    model_dir: str = "backend/model/v2026.11.15-masked",
    batch_size: int = 512,
    epochs: int = 4,
    lr: float = 1e-3,
    train_limit: int = 150000,
    val_limit: int = 40000,
    test_limit: int = 40000,
    seed: int = 42
) -> Dict:
    if not HAS_TORCH:
        raise RuntimeError("PyTorch is required to run embedding pipeline.")

    torch.manual_seed(seed)
    np.random.seed(seed)
    rng = np.random.RandomState(seed)

    print(f"Loading matches from {parquet_path}...")
    df = pd.read_parquet(parquet_path)
    n = len(df)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    train_df = df.iloc[:train_end]
    val_df = df.iloc[train_end:val_end]
    test_df = df.iloc[val_end:]

    if len(train_df) > train_limit:
        train_df = train_df.iloc[-train_limit:]
    if len(val_df) > val_limit:
        val_df = val_df.iloc[:val_limit]
    if len(test_df) > test_limit:
        test_df = test_df.iloc[:test_limit]

    out_path = Path(model_dir)

    # Load artifacts from model_dir
    with open(out_path / "hero_map.pkl", "rb") as f:
        hero_map = pickle.load(f)
    with open(out_path / "hero_winrate.pkl", "rb") as f:
        hero_winrate = pickle.load(f)
    with open(out_path / "matchup.pkl", "rb") as f:
        shrunk_matchup = pickle.load(f)
    with open(out_path / "synergy.pkl", "rb") as f:
        shrunk_synergy = pickle.load(f)
    with open(out_path / "model.pkl", "rb") as f:
        lgb_model = pickle.load(f)

    sorted_heroes = sorted(list(hero_map.keys()))
    hero_to_idx = {h: i for i, h in enumerate(sorted_heroes)}
    global_prior = float(np.mean(list(hero_winrate.values())))

    print("Generating masked draft samples...")
    train_samples = [generate_masked_draft_sample(r['radiant_team'], r['dire_team'], int(r['radiant_win']), rng) for _, r in train_df.iterrows()]
    val_samples = [generate_masked_draft_sample(r['radiant_team'], r['dire_team'], int(r['radiant_win']), rng) for _, r in val_df.iterrows()]
    test_samples = [generate_masked_draft_sample(r['radiant_team'], r['dire_team'], int(r['radiant_win']), rng) for _, r in test_df.iterrows()]

    print("Building feature tensors...")
    r_tr, d_tr, s_tr, y_tr = generate_embedding_dataset(train_samples, hero_to_idx, hero_winrate)
    r_val, d_val, s_val, y_val = generate_embedding_dataset(val_samples, hero_to_idx, hero_winrate)
    r_te, d_te, s_te, y_te = generate_embedding_dataset(test_samples, hero_to_idx, hero_winrate)

    train_ds = TensorDataset(torch.from_numpy(r_tr), torch.from_numpy(d_tr), torch.from_numpy(s_tr), torch.from_numpy(y_tr).unsqueeze(1))
    val_ds = TensorDataset(torch.from_numpy(r_val), torch.from_numpy(d_val), torch.from_numpy(s_val), torch.from_numpy(y_val).unsqueeze(1))

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    num_heroes = len(sorted_heroes)
    model = HeroEmbeddingDeepSet(num_heroes=num_heroes, embedding_dim=32)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    print(f"Training HeroEmbeddingDeepSet ({epochs} epochs)...")
    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        n_batches = 0
        for r_b, d_b, s_b, y_b in train_loader:
            optimizer.zero_grad()
            logits = model(r_b, d_b, s_b)
            loss = criterion(logits, y_b)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            n_batches += 1

        model.eval()
        val_loss = 0.0
        val_batches = 0
        with torch.no_grad():
            for r_b, d_b, s_b, y_b in val_loader:
                logits = model(r_b, d_b, s_b)
                loss = criterion(logits, y_b)
                val_loss += loss.item()
                val_batches += 1

        print(f"Epoch {epoch+1}/{epochs}: Train Loss = {total_loss/n_batches:.4f}, Val Loss = {val_loss/val_batches:.4f}")

    # Benchmark CPU latency
    print("Benchmarking single-draft CPU latency...")
    r_s = torch.from_numpy(r_te[:1])
    d_s = torch.from_numpy(d_te[:1])
    s_s = torch.from_numpy(s_te[:1])
    model.eval()
    for _ in range(10):
        _ = model(r_s, d_s, s_s)

    latencies = []
    for _ in range(200):
        t0 = time.perf_counter()
        _ = model(r_s, d_s, s_s)
        latencies.append((time.perf_counter() - t0) * 1000.0)
    mean_lat = float(np.mean(latencies))
    p95_lat = float(np.percentile(latencies, 95))
    print(f"Mean CPU Latency: {mean_lat:.3f} ms | P95: {p95_lat:.3f} ms")

    # Save model weights & TorchScript trace
    weights_path = out_path / "embedding_model.pt"
    torch.save(model.state_dict(), weights_path)
    traced_model = torch.jit.trace(model, (r_s, d_s, s_s))
    traced_path = out_path / "embedding_model_traced.pt"
    traced_model.save(str(traced_path))
    print(f"Saved PyTorch weights to {weights_path} and traced model to {traced_path}")

    # Generate predictions for Val and Test sets
    with torch.no_grad():
        preds_val_emb = torch.sigmoid(model(torch.from_numpy(r_val), torch.from_numpy(d_val), torch.from_numpy(s_val))).squeeze().numpy()
        preds_test_emb = torch.sigmoid(model(torch.from_numpy(r_te), torch.from_numpy(d_te), torch.from_numpy(s_te))).squeeze().numpy()

    # LightGBM predictions
    X_val_lgb = np.array([build_masked_feature_vector(s["revealed_radiant"], s["revealed_dire"], hero_to_idx, hero_winrate, global_prior) for s in val_samples], dtype=np.float32)
    X_test_lgb = np.array([build_masked_feature_vector(s["revealed_radiant"], s["revealed_dire"], hero_to_idx, hero_winrate, global_prior) for s in test_samples], dtype=np.float32)

    if hasattr(lgb_model, "predict_proba"):
        preds_val_lgb = lgb_model.predict_proba(X_val_lgb)[:, 1]
        preds_test_lgb = lgb_model.predict_proba(X_test_lgb)[:, 1]
    else:
        preds_val_lgb = lgb_model.predict(X_val_lgb)
        preds_test_lgb = lgb_model.predict(X_test_lgb)

    # Combiner components
    val_comps = extract_masked_score_components(val_samples, hero_winrate, global_prior, shrunk_matchup, shrunk_synergy)
    test_comps = extract_masked_score_components(test_samples, hero_winrate, global_prior, shrunk_matchup, shrunk_synergy)

    # 1. Baseline Combiner: [matchup, synergy, winrate, progress, lgbm_prob]
    X_comb_val_base = np.column_stack([val_comps, preds_val_lgb - 0.5])
    X_comb_test_base = np.column_stack([test_comps, preds_test_lgb - 0.5])

    comb_base = LogisticRegression(C=1.0, fit_intercept=True, random_state=42)
    comb_base.fit(X_comb_val_base, y_val.astype(int))
    p_test_base = comb_base.predict_proba(X_comb_test_base)[:, 1]

    # 2. Candidate Combiner with Embeddings: [matchup, synergy, winrate, progress, lgbm_prob, emb_prob]
    X_comb_val_emb = np.column_stack([val_comps, preds_val_lgb - 0.5, preds_val_emb - 0.5])
    X_comb_test_emb = np.column_stack([test_comps, preds_test_lgb - 0.5, preds_test_emb - 0.5])

    comb_emb = LogisticRegression(C=1.0, fit_intercept=True, random_state=42)
    comb_emb.fit(X_comb_val_emb, y_val.astype(int))
    p_test_emb = comb_emb.predict_proba(X_comb_test_emb)[:, 1]

    # Metrics
    metrics_base = compute_all_metrics(y_te.astype(int), p_test_base)
    metrics_emb = compute_all_metrics(y_te.astype(int), p_test_emb)
    metrics_emb_only = compute_all_metrics(y_te.astype(int), preds_test_emb)
    metrics_lgb_only = compute_all_metrics(y_te.astype(int), preds_test_lgb)

    print("\n" + "=" * 70)
    print("EVALUATION COMPARISON ON TEST FOLD:")
    print(f"  LightGBM Alone:         Log Loss = {metrics_lgb_only['log_loss']:.4f}, AUC = {metrics_lgb_only['roc_auc']:.4f}, Brier = {metrics_lgb_only['brier_score']:.4f}")
    print(f"  Embedding DeepSet Alone:Log Loss = {metrics_emb_only['log_loss']:.4f}, AUC = {metrics_emb_only['roc_auc']:.4f}, Brier = {metrics_emb_only['brier_score']:.4f}")
    print(f"  Baseline Combiner:      Log Loss = {metrics_base['log_loss']:.4f}, AUC = {metrics_base['roc_auc']:.4f}, Brier = {metrics_base['brier_score']:.4f}")
    print(f"  Combiner + Embeddings:  Log Loss = {metrics_emb['log_loss']:.4f}, AUC = {metrics_emb['roc_auc']:.4f}, Brier = {metrics_emb['brier_score']:.4f}")

    # Bootstrap Paired Difference Test (Delta = Candidate - Baseline)
    print("\nRunning paired bootstrap test (1000 resamples)...")
    ci_res = compute_paired_bootstrap_ci(
        y_true=y_te.astype(int),
        prob_baseline=p_test_base,
        prob_candidate=p_test_emb,
        n_bootstraps=1000,
        metric="log_loss",
        random_state=42
    )
    print(f"Bootstrap Log Loss Delta (Candidate - Baseline): {ci_res['diff_mean']:.5f}")
    print(f"95% CI: [{ci_res['ci_lower']:.5f}, {ci_res['ci_upper']:.5f}] (p-value: {ci_res['p_value']:.4f})")
    print(f"Statistically significant improvement: {ci_res['is_significant_improvement']}")

    decision_keep_embeddings = bool(ci_res["is_significant_improvement"] and ci_res["ci_upper"] < 0)

    # Save Combiner Weights
    if decision_keep_embeddings:
        print("\nDecision: KEEP embedding model in combiner (CI excludes zero).")
        combiner_weights = {
            "matchup": float(comb_emb.coef_[0][0]),
            "synergy": float(comb_emb.coef_[0][1]),
            "winrate": float(comb_emb.coef_[0][2]),
            "progress": float(comb_emb.coef_[0][3]),
            "model": float(comb_emb.coef_[0][4]),
            "embedding": float(comb_emb.coef_[0][5]),
            "intercept": float(comb_emb.intercept_[0]),
            "is_masked": True,
            "has_embedding": True
        }
        with open(out_path / "combiner.pkl", "wb") as f:
            pickle.dump(comb_emb, f)
    else:
        print("\nDecision: Fall back to baseline combiner without embeddings (CI includes zero).")
        combiner_weights = {
            "matchup": float(comb_base.coef_[0][0]),
            "synergy": float(comb_base.coef_[0][1]),
            "winrate": float(comb_base.coef_[0][2]),
            "progress": float(comb_base.coef_[0][3]),
            "model": float(comb_base.coef_[0][4]),
            "intercept": float(comb_base.intercept_[0]),
            "is_masked": True,
            "has_embedding": False
        }

    with open(out_path / "combiner_weights.pkl", "wb") as f:
        pickle.dump(combiner_weights, f)

    # Update metadata
    meta_path = out_path / "metadata.json"
    if meta_path.exists():
        with open(meta_path, "r") as f:
            meta = json.load(f)
        meta["combiner_weights"] = combiner_weights
        meta["has_embedding"] = decision_keep_embeddings
        meta["embedding_metrics"] = {
            "mean_latency_ms": mean_lat,
            "p95_latency_ms": p95_lat,
            "deepset_standalone": metrics_emb_only,
            "combiner_with_embedding": metrics_emb,
            "bootstrap_ci": ci_res,
            "decision_keep_embeddings": decision_keep_embeddings
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

    # Write documentation report
    report_content = f"""# Hero Embedding Set Model Evaluation Report

## Model Overview
- **Architecture**: 32-dim hero embeddings $\\to$ DeepSets permutation-invariant aggregation $\\sum \\phi(x)$ $\\to$ draft state features concat $\\to$ MLP $\\to$ win probability.
- **Learned Mask Token**: Token 0 handles unrevealed draft slots.
- **Permutation Invariance**: Mathematically guaranteed by sum aggregation over hero embedding transformations.

## CPU Inference Latency Benchmark
- **Target**: $< 15.0$ ms
- **Mean Latency**: {mean_lat:.3f} ms
- **P95 Latency**: {p95_lat:.3f} ms
- **TorchScript Tracing**: Saved to `embedding_model_traced.pt`

## Standalone Performance (Holdout Test Fold)
| Metric | LightGBM Alone | Embedding DeepSet Alone |
|---|---|---|
| Log Loss | {metrics_lgb_only['log_loss']:.4f} | {metrics_emb_only['log_loss']:.4f} |
| ROC-AUC | {metrics_lgb_only['roc_auc']:.4f} | {metrics_emb_only['roc_auc']:.4f} |
| Brier Score | {metrics_lgb_only['brier_score']:.4f} | {metrics_emb_only['brier_score']:.4f} |
| ECE | {metrics_lgb_only['ece']:.4f} | {metrics_emb_only['ece']:.4f} |

## Combiner Stacking Performance
| Metric | Baseline Combiner (No Embeddings) | Stacking Combiner (+ Embeddings) |
|---|---|---|
| Log Loss | {metrics_base['log_loss']:.4f} | {metrics_emb['log_loss']:.4f} |
| ROC-AUC | {metrics_base['roc_auc']:.4f} | {metrics_emb['roc_auc']:.4f} |
| Brier Score | {metrics_base['brier_score']:.4f} | {metrics_emb['brier_score']:.4f} |
| ECE | {metrics_base['ece']:.4f} | {metrics_emb['ece']:.4f} |

## Paired Bootstrap Difference Test
- **Metric**: Log Loss Difference (Candidate - Baseline)
- **Bootstrap Resamples**: 1,000
- **Mean Difference**: {ci_res['diff_mean']:.5f}
- **95% Confidence Interval**: [{ci_res['ci_lower']:.5f}, {ci_res['ci_upper']:.5f}]
- **Empirical p-value**: {ci_res['p_value']:.4f}
- **Statistically Significant Improvement**: {ci_res['is_significant_improvement']}
- **Governance Decision**: {'KEEP embedding model in active combiner stack' if decision_keep_embeddings else 'FALLBACK to baseline combiner stack (improvement CI does not strictly exclude zero)'}
"""
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    with open(reports_dir / "embedding_results.md", "w") as f:
        f.write(report_content)
    print(f"\nWrote results report to reports/embedding_results.md")

    return {
        "metrics_base": metrics_base,
        "metrics_emb": metrics_emb,
        "ci_result": ci_res,
        "decision": decision_keep_embeddings
    }


if __name__ == "__main__":
    run_embedding_pipeline()
