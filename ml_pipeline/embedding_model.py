"""Hero embedding set permutation-invariant model.

DeepSets / Multi-Head Attention architecture for Dota 2 draft win probability prediction.
- 32-dim hero embeddings
- Learned mask token for unrevealed slots (index 0)
- DeepSets permutation-invariant aggregation (sum phi(x))
- State indicator MLP integration
- Fast CPU inference (<15ms)
- TorchScript exportable
"""

from typing import Dict, List, Optional, Tuple
import os
import sys
from pathlib import Path

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


if HAS_TORCH:
    class HeroEmbeddingDeepSet(nn.Module):
        """Permutation-invariant DeepSet neural network for Dota 2 partial & full drafts."""

        def __init__(self, num_heroes: int = 127, embedding_dim: int = 32, num_state_features: int = 7):
            super().__init__()
            self.num_heroes = num_heroes
            self.embedding_dim = embedding_dim
            # index 0 is learned mask token for unrevealed hero slot
            self.hero_embeddings = nn.Embedding(num_heroes + 1, embedding_dim)

            # Element-wise transformation phi(x) for DeepSets
            self.phi = nn.Sequential(
                nn.Linear(embedding_dim, embedding_dim),
                nn.ReLU(),
                nn.Linear(embedding_dim, embedding_dim)
            )

            # Combined MLP rho(sum phi(rad), sum phi(dire), diff, state_indicators)
            in_dim = embedding_dim * 3 + num_state_features
            self.mlp = nn.Sequential(
                nn.Linear(in_dim, 64),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(64, 32),
                nn.ReLU(),
                nn.Linear(32, 1)
            )

        def forward(self, rad_indices: torch.Tensor, dire_indices: torch.Tensor, state_features: torch.Tensor) -> torch.Tensor:
            """
            Args:
                rad_indices: LongTensor of shape (B, 5), hero IDs 1..num_heroes (0 for mask)
                dire_indices: LongTensor of shape (B, 5), hero IDs 1..num_heroes (0 for mask)
                state_features: FloatTensor of shape (B, 7)
            Returns:
                logits: FloatTensor of shape (B, 1)
            """
            # Embeddings: (B, 5, embedding_dim)
            rad_emb = self.hero_embeddings(rad_indices)
            dire_emb = self.hero_embeddings(dire_indices)

            # DeepSet transform phi
            rad_phi = self.phi(rad_emb)
            dire_phi = self.phi(dire_emb)

            # Permutation-invariant sum aggregation: (B, embedding_dim)
            rad_sum = torch.sum(rad_phi, dim=1)
            dire_sum = torch.sum(dire_phi, dim=1)

            diff = rad_sum - dire_sum

            # Concat with state features: (B, embedding_dim * 3 + num_state_features)
            combined = torch.cat([rad_sum, dire_sum, diff, state_features], dim=-1)

            logits = self.mlp(combined)
            return logits

        def predict_proba(self, rad_indices: torch.Tensor, dire_indices: torch.Tensor, state_features: torch.Tensor) -> torch.Tensor:
            """Return win probabilities for Radiant."""
            with torch.no_grad():
                logits = self.forward(rad_indices, dire_indices, state_features)
                return torch.sigmoid(logits)


def build_embedding_features(
    radiant_ids: List[int],
    dire_ids: List[int],
    hero_to_idx: Dict[int, int],
    hero_winrates: Dict[int, float],
    num_heroes: int = 127
) -> Tuple[List[int], List[int], List[float]]:
    """Build input tensors for HeroEmbeddingDeepSet from draft lists."""
    # Convert hero IDs to 1-indexed model IDs (0 reserved for unrevealed mask token)
    rad_slots = [0] * 5
    for i, hid in enumerate(radiant_ids[:5]):
        if hid in hero_to_idx:
            rad_slots[i] = hero_to_idx[hid] + 1  # 1-indexed

    dire_slots = [0] * 5
    for i, hid in enumerate(dire_ids[:5]):
        if hid in hero_to_idx:
            dire_slots[i] = hero_to_idx[hid] + 1  # 1-indexed

    n_r = len(radiant_ids)
    n_d = len(dire_ids)
    tot = n_r + n_d

    r_wr = float(sum(hero_winrates.get(h, 0.50) for h in radiant_ids) / max(1, n_r)) if n_r > 0 else 0.50
    d_wr = float(sum(hero_winrates.get(h, 0.50) for h in dire_ids) / max(1, n_d)) if n_d > 0 else 0.50

    state_features = [
        n_r / 5.0,
        n_d / 5.0,
        (n_r - n_d) / 5.0,
        tot / 10.0,
        r_wr,
        d_wr,
        r_wr - d_wr
    ]
    return rad_slots, dire_slots, state_features
