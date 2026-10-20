# Dota-Drafter: Methodology & Mathematical Formulations

This document formalizes the statistical and machine learning methods implemented in Dota-Drafter to provide leakage-free, calibrated counter-pick suggestions.

---

## 1. Zero-Leakage Temporal Evaluation

Traditional random $k$-fold cross-validation introduces severe forward lookahead leakage in esports drafts: hero matchups and win rates shift across balance patches and metagame evolutions.

We partition $N$ chronological matches strictly by `match_id` ascending:
- **Train ($D_{\text{train}}$)**: Oldest 70% of matches.
- **Validation ($D_{\text{val}}$)**: Middle 15% of matches (used exclusively for tuning shrinkage $k$, early stopping, and fitting stacking combiner weights).
- **Test ($D_{\text{test}}$)**: Newest 15% of matches (held out; touched only for final benchmark reporting).

All feature baselines—hero global win rates, matchup matrices, and synergy pairs—are computed **strictly on $D_{\text{train}}$**. No statistic from $D_{\text{val}}$ or $D_{\text{test}}$ ever informs the model features.

---

## 2. Patch-Aware Exponential Recency Weighting

Matches played on older balance patches or earlier in a patch lifecycle receive exponentially decaying weights relative to the current patch anchor:

$$w_i = \exp(-\lambda \cdot \Delta t_i)$$

where:
- $\Delta t_i \ge 0$ is the normalized temporal distance in days or patch version steps.
- $\lambda \ge 0$ is the decay parameter ($\lambda = 0.20$ by default).

For any hero pairing $(A, B)$, the weighted game count $N_{AB}$ and weighted win count $W_{AB}$ are:

$$N_{AB} = \sum_{i \in \text{matches}(A, B)} w_i, \quad W_{AB} = \sum_{i \in \text{matches}(A \text{ wins vs } B)} w_i$$

---

## 3. Empirical-Bayes (Beta-Prior) Shrinkage

Raw win rates $\frac{W_{AB}}{N_{AB}}$ suffer high variance when sample sizes are small (e.g., niche hero matchups with few observed games). We shrink observed win rates toward a robust prior:

$$\hat{P}(A \text{ beats } B) = \frac{W_{AB} + k \cdot \bar{P}_A}{N_{AB} + k}$$

where:
- $\bar{P}_A$ is hero $A$'s global baseline win rate on $D_{\text{train}}$.
- $k > 0$ is the pseudo-count prior strength ($k = 20.0$ for matchups, $k = 15.0$ for synergies, tuned on validation loss).

### Properties:
- As $N_{AB} \to \infty$, $\hat{P}(A \text{ beats } B) \to \frac{W_{AB}}{N_{AB}}$ (observed empirical rate dominates).
- As $N_{AB} \to 0$, $\hat{P}(A \text{ beats } B) \to \bar{P}_A$ (regresses safely to baseline, avoiding extreme outliers).

Synergy pairs $(A, C)$ are shrunk identically toward the baseline pair prior:

$$\hat{P}(A \text{ with } C) = \frac{W_{AC} + k_s \cdot \frac{\bar{P}_A + \bar{P}_C}{2}}{N_{AC} + k_s}$$

---

## 4. Normalization and Centering

To isolate the specific tactical advantage of a counter-pick from the hero's general strength in the metagame, matchup terms are centered relative to the hero's average matchup expectation:

$$\Delta M(A, B) = \hat{P}(A \text{ beats } B) - \bar{M}_A$$

where $\bar{M}_A = \frac{1}{|E|} \sum_{e \in E} \hat{P}(A \text{ beats } e)$ is hero $A$'s mean matchup performance across all enemies.

Similarly, synergy terms are centered around 0.50:

$$\Delta S(A, C) = \hat{P}(A \text{ with } C) - 0.50$$

---

## 5. Learned Stacking Combiner

Rather than relying on hand-tuned heuristic coefficients, the final draft score is computed by stacking multiple feature signals into a Logistic Regression combiner fitted on $D_{\text{val}}$:

$$z = w_0 + w_M \cdot \overline{\Delta M} + w_S \cdot \overline{\Delta S} + w_W \cdot (\bar{P}_{\text{allies}} - \bar{P}_{\text{enemies}}) + w_{\text{model}} \cdot \text{logit}(P_{\text{LGBM}})$$

$$P(\text{Win} \mid \text{Draft}) = \sigma(z) = \frac{1}{1 + \exp(-z)}$$

### Fitted Weights (Validation Set):
- $w_M = 1.5644$ (Matchup counter effect)
- $w_S = 1.5201$ (Team synergy effect)
- $w_W = 0.9665$ (Baseline win rate advantage)
- $w_{\text{model}} = 2.1890$ (Nonlinear LightGBM interaction model)
- $w_0 = 0.1045$ (Radiant side map advantage intercept)

---

## 6. Confidence Scoring

Each counter suggestion assigns a confidence tier based on the effective sample size $N_{AB}$:
- **High Confidence**: $N_{AB} \ge 100$ games.
- **Medium Confidence**: $30 \le N_{AB} < 100$ games.
- **Low Confidence**: $N_{AB} < 30$ games (flagged in UI; heavily regressed toward prior).
