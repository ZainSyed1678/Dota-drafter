# Hero Embedding Set Model Evaluation Report

## Model Overview
- **Architecture**: 32-dim hero embeddings $\to$ DeepSets permutation-invariant aggregation $\sum \phi(x)$ $\to$ draft state features concat $\to$ MLP $\to$ win probability.
- **Learned Mask Token**: Token 0 handles unrevealed draft slots.
- **Permutation Invariance**: Mathematically guaranteed by sum aggregation over hero embedding transformations.

## CPU Inference Latency Benchmark
- **Target**: $< 15.0$ ms
- **Mean Latency**: 0.319 ms
- **P95 Latency**: 0.490 ms
- **TorchScript Tracing**: Saved to `embedding_model_traced.pt`

## Standalone Performance (Holdout Test Fold)
| Metric | LightGBM Alone | Embedding DeepSet Alone |
|---|---|---|
| Log Loss | 0.6878 | 0.6880 |
| ROC-AUC | 0.5492 | 0.5464 |
| Brier Score | 0.2473 | 0.2474 |
| ECE | 0.0117 | 0.0046 |

## Combiner Stacking Performance
| Metric | Baseline Combiner (No Embeddings) | Stacking Combiner (+ Embeddings) |
|---|---|---|
| Log Loss | 0.6872 | 0.6872 |
| ROC-AUC | 0.5521 | 0.5524 |
| Brier Score | 0.2471 | 0.2470 |
| ECE | 0.0089 | 0.0063 |

## Paired Bootstrap Difference Test
- **Metric**: Log Loss Difference (Candidate - Baseline)
- **Bootstrap Resamples**: 1,000
- **Mean Difference**: -0.00007
- **95% Confidence Interval**: [-0.00027, 0.00014]
- **Empirical p-value**: 0.2630
- **Statistically Significant Improvement**: False
- **Governance Decision**: FALLBACK to baseline combiner stack (improvement CI does not strictly exclude zero)
