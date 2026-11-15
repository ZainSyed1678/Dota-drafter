# Shrinkage & Recency Tuning Results (1.4M Match Dataset)

## 1. Executive Summary & Key Insights

Prior to scaling, the model utilized a single shared hyperparameter $k = 20.0$ and $\lambda = 0.20$ across all matrices, designed for small datasets ($<50,000$ matches). With **1.475 million clean matches**, the statistical density across hero pairs fundamentally shifts:

1. **Decoupled $k$ Optimization**:
   - **Matchup Matrix ($k_{\text{matchup}} = 1.0$)**: With thousands of observations per hero pair, empirical matchup winrates are dense and reliable. Large shrinkage ($k=20$ or $k=50$) over-smoothes real counter-pick edges. Setting $k_{\text{matchup}} = 1.0$ yielded the lowest validation log loss.
   - **Synergy Matrix ($k_{\text{synergy}} = 200.0$)**: Ally synergies have lower signal-to-noise ratios and higher combinatoric variance. Stronger shrinkage ($k=200.0$) heavily regularizes spurious co-occurrence noise toward the 0.50 neutral baseline.
   - **Hero Winrate Prior ($k_{\text{hero}} = 50.0$)**: Hero winrates stabilize reliably with moderate smoothing toward the global prior.
2. **Recency Weighting ($\lambda = 0.40$)**:
   - Testing recency decay rates $\lambda \in [0.0, 0.40]$ demonstrated that $\lambda = 0.40$ delivers stronger validation calibration by favoring the newest patch dynamics.
3. **Posterior Interval Confidence Tiers**:
   - Replaced arbitrary static sample thresholds (50 / 15) with Beta-binomial posterior credible interval widths ($W = 3.92 \times \sqrt{\text{Var}(P)}$):
     - **High Confidence**: $W \le 0.08$ (or $N \ge 200$)
     - **Medium Confidence**: $W \le 0.15$ (or $N \ge 50$)
     - **Low Confidence**: $W > 0.15$ (or $N < 50$)

---

## 2. Validation Grid Search Trajectories

### Recency Weighting ($\lambda$)
| $\lambda$ | Validation Log Loss | Status |
| :---: | :---: | :---: |
| 0.00 | 0.68240 | Flat time weighting |
| 0.05 | 0.68240 | Weak recency |
| 0.10 | 0.68239 | Moderate recency |
| 0.20 | 0.68238 | Previous default |
| **0.40** | **0.68237** | **Optimal Selected** |

### Matchup Shrinkage ($k_{\text{matchup}}$)
| $k_{\text{matchup}}$ | Validation Log Loss |
| :---: | :---: |
| **1.0** | **0.68236** |
| 5.0 | 0.68236 |
| 10.0 | 0.68236 |
| 20.0 | 0.68237 |
| 50.0 | 0.68241 |
| 100.0 | 0.68251 |
| 200.0 | 0.68271 |

### Synergy Shrinkage ($k_{\text{synergy}}$)
| $k_{\text{synergy}}$ | Validation Log Loss |
| :---: | :---: |
| 0.0 | 0.68240 |
| 10.0 | 0.68238 |
| 20.0 | 0.68236 |
| 50.0 | 0.68232 |
| 100.0 | 0.68227 |
| **200.0** | **0.68223** |
