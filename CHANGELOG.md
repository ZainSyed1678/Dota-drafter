# Changelog: Dota 2 Drafter

All notable changes and technical design decisions across project phases will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Phase 0 — Audit & System Baseline] - 2026-10-19

### Added
- `AUDIT.md`: Complete audit of repository architecture, root scripts, model usage in `/suggest`, data leakage analysis, hero ID fragmentation, and documentation mismatches.
- `CHANGELOG.md`: Initialization of project change tracking ledger.

### Findings & Decisions
- Identified critical data leakage in `ml_pipeline/train.py`: matchup and synergy matrices were computed over the full dataset before random train/test splitting.
- Confirmed that the LightGBM/XGBoost model is bypassed in production `/suggest` due to `PREDICTION_ENGINE = "heuristic"`.
- Identified that frontend hardcodes arbitrary hero IDs (1..121) rather than Valve/OpenDota hero IDs, passing strings over the wire.
- Documented dead scripts: `patch.py`, `train_scheduler.py`, `collect_to_psql.py`, `core/utils.py`, `main.py` (root).

## [Phase 1 — Fix Evaluation & Leakage Elimination] - 2026-10-19

### Added
- `ml_pipeline/evaluate.py`: Standalone evaluation script enforcing strict chronological time-based splitting (train: 10,434, val: 2,236, test: 2,237 matches).
- `ml_pipeline/reports/metrics.json`: Empirical benchmark evaluation on test set across accuracy, log-loss, ROC-AUC, and Brier score.
- `ml_pipeline/reports/calibration_curve.png`: Calibration reliability diagrams for baselines and LightGBM model.

### Changed
- `Readme.md`: Replaced fabricated 69–72% accuracy claim with real, leakage-free benchmark numbers (52.79% - 55.52%) and an explanation of the statistical ceiling of draft-only win prediction.

### Fixed
- **Zero-Leakage Guarantee**: Hero global win rates, matchup matrices, and synergy matrices are calculated strictly using training data only, eliminating target leakage into validation and test sets.

## [Phase 2 — Empirical-Bayes Shrinkage, Confidence & Learned Scoring] - 2026-10-19

### Added
- `ml_pipeline/reports/ablation.md`: Systematic ablation study across 8 configurations on the unseen test set, establishing that the Full Learned Combiner achieves the highest discriminative ranking power (0.5757 ROC-AUC).
- `backend/model/matchup_samples.pkl` & `backend/model/synergy_samples.pkl`: Persistent weighted sample sizes per hero pair.
- `backend/model/combiner_weights.pkl` & `backend/model/metadata.json`: Empirical maximum-likelihood weights and metadata learned from validation slice.

### Changed
- `ml_pipeline/train.py`:
  - Upgraded to enforce chronological train/val/test splits without data leakage.
  - Applied Empirical-Bayes / Beta-prior shrinkage with tuned parameter $k=20.0$ and recency decay $\lambda=0.2$.
  - Integrated LightGBM model training with early stopping.
  - Trained Logistic Regression combiner on validation slice to learn optimal component weights ($w_M=1.5644, w_S=1.5201, w_W=0.9665, w_{\text{model}}=2.1890$, intercept $0.1045$).
- `backend/scoring.py`:
  - Implemented the learned combiner in `predict()` combining LightGBM $P(\text{win} \mid \dots)$ with shrunk matchup, synergy, and winrate signals.
  - Implemented confidence rating (`high`, `medium`, `low`) and sample size reporting on all suggestions and reasons.
  - Suppressed or flagged low-sample ($< 15$ games) counters.
- `backend/models.py`:
  - Added `sample_size` and `confidence` fields to `ReasonDetail` and `HeroSuggestion`.
- `backend/config.py`:
  - Default `PREDICTION_ENGINE` upgraded to `"combined"`.

## [Phase 3 — Draft Realism, Bans, Roles & Validation] - 2026-10-20

### Added
- Role-aware recommendation engine (`backend/scoring.py:infer_missing_roles`): automatically identifies unfulfilled team positions (carry, mid, offlane, support) from current allies or honors explicit `roles_needed` parameter.
- Ban filtering: accepts optional `bans` list and guarantees banned and picked heroes are completely removed from recommendation pool.
- Rank bracket filtering support: accepts optional `bracket` filter; gracefully falls back to global matrices with explanatory `bracket_note` when bracket-specific splits are unavailable.
- Robust Pydantic schema validation:
  - Strict team size limits: maximum 5 enemies, maximum 4 allies (user picks the 5th).
  - Intra-list duplicate detection across enemy, ally, and ban lists.
  - Cross-list disjoint validation: prevents heroes from appearing on both teams or simultaneously in ban and pick lists.
  - Unknown hero detection: validates all hero inputs against loaded heroes, raising HTTP 422 with a clear error message.
  - Transparent dual input contract: seamlessly accepts both numeric Dota 2 hero IDs and string localized names.

## [Phase 4 — Data Architecture, Hero Metadata & Model Versioning] - 2026-10-20

### Added
- `ml_pipeline/training_config.json`: Configuration for patch-aware recency decay rates and Empirical-Bayes shrinkage hyperparameters.
- `backend/model/heroes_metadata.json`: Comprehensive canonical Dota 2 hero database (127 heroes) with numeric ID, localized name, short name, roles, primary attribute, and CDN image/icon URLs.
- Model versioning pipeline in `ml_pipeline/train.py`: training runs now serialize artifacts directly to `backend/model/<version>/` (e.g. `v2.2.0/`) alongside `metadata.json` recording git commit hash, data freshness, hyperparameter config, and test evaluation metrics.

### Changed
- `backend/scoring.py`:
  - Implemented automatic version discovery: scans `backend/model/` and loads the latest version by default.
  - Added support for targeting specific model versions via `load_models(version=...)`.
  - Added structured data freshness tracking in `model_metadata`.
- `backend/main.py`:
  - Updated `GET /heroes` to return full hero metadata (numeric ID, name, roles, attribute, CDN image URL).
  - Updated `GET /health` to surface active model version and data freshness metrics.
  - Added version parameter support to `POST /model/reload?version=...` for zero-downtime hot reloading.



