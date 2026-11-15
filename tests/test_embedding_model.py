"""Tests for hero embedding set model and permutation invariance."""

import sys
import time
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml_pipeline.embedding_model import HAS_TORCH

if HAS_TORCH:
    import torch
    from ml_pipeline.embedding_model import HeroEmbeddingDeepSet, build_embedding_features


@pytest.mark.skipif(not HAS_TORCH, reason="PyTorch is required for embedding model tests")
def test_deepset_permutation_invariance():
    """Verify that re-ordering heroes on a team produces identical prediction."""
    torch.manual_seed(42)
    model = HeroEmbeddingDeepSet(num_heroes=127, embedding_dim=32)
    model.eval()

    # Radiant heroes in order [10, 25, 42, 77, 99]
    rad_orig = torch.tensor([[10, 25, 42, 77, 99]], dtype=torch.long)
    dire_orig = torch.tensor([[5, 12, 19, 33, 80]], dtype=torch.long)
    state = torch.tensor([[1.0, 1.0, 0.0, 1.0, 0.52, 0.49, 0.03]], dtype=torch.float32)

    with torch.no_grad():
        out_orig = model.predict_proba(rad_orig, dire_orig, state).item()

    # Radiant heroes permuted: [77, 10, 99, 42, 25]
    rad_perm = torch.tensor([[77, 10, 99, 42, 25]], dtype=torch.long)
    with torch.no_grad():
        out_perm = model.predict_proba(rad_perm, dire_orig, state).item()

    assert abs(out_orig - out_perm) < 1e-5, f"DeepSet must be permutation invariant: {out_orig} vs {out_perm}"


@pytest.mark.skipif(not HAS_TORCH, reason="PyTorch is required for embedding model tests")
def test_masked_slots_and_bounds():
    """Verify that unrevealed slots (0 index) are handled cleanly and outputs in (0, 1)."""
    torch.manual_seed(42)
    model = HeroEmbeddingDeepSet(num_heroes=127, embedding_dim=32)
    model.eval()

    # Partial draft: 2 Radiant heroes, 1 Dire hero, rest 0
    rad = torch.tensor([[15, 30, 0, 0, 0]], dtype=torch.long)
    dire = torch.tensor([[44, 0, 0, 0, 0]], dtype=torch.long)
    state = torch.tensor([[0.4, 0.2, 0.2, 0.3, 0.51, 0.50, 0.01]], dtype=torch.float32)

    with torch.no_grad():
        prob = model.predict_proba(rad, dire, state).item()

    assert 0.0 <= prob <= 1.0, f"Probability must be bounded in [0, 1], got {prob}"


@pytest.mark.skipif(not HAS_TORCH, reason="PyTorch is required for embedding model tests")
def test_cpu_inference_latency():
    """Verify CPU inference latency is strictly < 15ms per draft."""
    torch.manual_seed(42)
    model = HeroEmbeddingDeepSet(num_heroes=127, embedding_dim=32)
    model.eval()

    rad = torch.tensor([[10, 20, 30, 40, 50]], dtype=torch.long)
    dire = torch.tensor([[11, 21, 31, 41, 51]], dtype=torch.long)
    state = torch.tensor([[1.0, 1.0, 0.0, 1.0, 0.50, 0.50, 0.0]], dtype=torch.float32)

    # Warmup
    for _ in range(10):
        _ = model.predict_proba(rad, dire, state)

    times = []
    for _ in range(100):
        t0 = time.perf_counter()
        _ = model.predict_proba(rad, dire, state)
        times.append((time.perf_counter() - t0) * 1000.0)

    mean_ms = float(np.mean(times))
    p95_ms = float(np.percentile(times, 95))
    print(f"\nCPU latency: mean={mean_ms:.3f}ms, p95={p95_ms:.3f}ms")
    assert mean_ms < 15.0, f"Mean latency must be < 15ms, got {mean_ms:.3f}ms"
    assert p95_ms < 20.0, f"P95 latency must be < 20ms, got {p95_ms:.3f}ms"
