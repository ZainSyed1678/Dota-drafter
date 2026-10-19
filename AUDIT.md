# Repository Audit: Dota 2 Drafter (Phase 0)

**Date:** 2026-10-19  
**Repository:** `Dota-drafter`  
**Auditor:** Automated Engineering Audit  

---

## 1. Repository Structure & Root Script Inventory

The repository represents an evolution from a standalone prototype script and exploratory notebooks into a multi-service architecture (FastAPI backend, React frontend, PostgreSQL match storage, Prometheus/Grafana telemetry, and a Telegram supervisor bot). However, legacy files and exploratory scripts remain in the root directory.

| Script / Component | Role & Status | Findings / Issues |
| :--- | :--- | :--- |
| `backend/main.py` | **Active API Server** | Production FastAPI application exposing `/suggest`, `/health`, `/heroes`, `/metrics`, and `/model/reload`. |
| `backend/scoring.py` | **Active Scoring Engine** | Implements matrix lookups, normalized advantages, beginner rationale, and candidate scoring. Default engine is `"heuristic"`. |
| `main.py` (root) | **Dead / Legacy API** | Early single-file prototype. Uses hard-coded heuristic formulas and loads models from `./model/`. Superseded by `backend/main.py`. |
| `orchestrator.py` | **Active Orchestrator** | Coordinates patch training pipeline: queries `lifecycle_manager` for ready patches, spawns `train_from_psql.py`, and issues hot-reload request to backend. |
| `lifecycle_manager.py` | **Active DB State Machine** | Manages PostgreSQL tables (`patches`, `patch_lifecycle`, `dataset_metadata`, `feature_metadata`) tracking training states. |
| `patch_aware_collector.py` | **Active Data Collector** | Scrapes OpenDota public matches with MMR >= 4500, enforces ~50 req/min rate limit, saves to PostgreSQL, and exports Prometheus metrics on port 8002. |
| `collect_to_psql.py` | **Deprecated Collector** | Early collector lacking patch-awareness, rate-limiting guards, and lifecycle integration. Superseded by `patch_aware_collector.py`. |
| `train_from_psql.py` | **Active Training Bridge** | Extracts patch match data from PostgreSQL into `notebooks/matches_{patch}_{dataset}.csv` and invokes `ml_pipeline/train.py`. |
| `train_scheduler.py` | **Dead / Outdated Scheduler** | Attempts to run nonexistent `notebooks/Untitled.ipynb` via `jupyter nbconvert`. Uncoupled from `lifecycle_manager`. |
| `patch.py` | **Dead Scratchpad** | 15-line script modifying `notebooks/second.ipynb` print statements. Throwaway script left in root. |
| `bot/` (`bot.py`, `ingest_patch.py`) | **Active Telegram Bot Service** | Supervisor bot providing telemetry (`/stats`, `/health`), Qdrant patch notes semantic search (`/hero <name>`), and model reload. |
| `core/` (`utils.py`) | **Dead Prototype Logic** | Contains helper functions that reference nonexistent `app.py`. Duplicates prediction feature vector logic. |
| `ml_pipeline/` (`train.py`, `compare.py`)| **Active ML Pipeline** | Production training script using XGBoost and evaluation comparison tool. Contains data leakage issues (see Section 3). |
| `notebooks/` | **Exploration** | Contains `first.ipynb` and `second.ipynb` exploratory work, along with local match CSVs. |

---

## 2. Machine Learning Model Usage in `/suggest`

- **Configuration:** In `backend/config.py`, the setting `PREDICTION_ENGINE` defaults to `"heuristic"`.
- **Endpoint Execution:** In `backend/main.py` (`suggest()` endpoint), `engine = scoring.settings.PREDICTION_ENGINE` is passed into `scoring.predict()`.
- **Scoring Branch:** In `backend/scoring.py` (lines 216–260):
  ```python
  def predict(hero_id: int, enemy_ids: List[int], ally_ids: List[int], engine: str = 'heuristic') -> float:
      if engine == 'ml' and ml_model is not None:
          # Construct feature vector and call ml_model.predict_proba
          ...
      else:
          # Heuristic formula
          m = norm_matchup(hero_id, enemy_ids)
          s = synergy_score(hero_id, ally_ids)
          wr = hero_winrate.get(hero_id, 0.5)
          score = 1.50 * m + 0.35 * s + 0.06 * (wr - 0.5)
          if abs(m) < 0.005:
              score -= 0.02
          return score
  ```
- **Conclusion:** **The ML model's output does NOT influence candidate rankings in production.** The backend runs strictly on the hand-tuned heuristic formula.
- **Further finding:** When `engine == 'ml'` is forced:
  1. The loaded model in `model.pkl` is an `XGBClassifier` (not LightGBM as claimed in the README).
  2. The model predicts raw radiant win probability $P(\text{Win})$, completely bypassing the normalized matchup advantages and synergy explanations.
  3. Any exception in vector calculation defaults to a flat score of `0.5`, destroying ranking separation.

---

## 3. Data Leakage and Evaluation Assessment

Inspection of `ml_pipeline/train.py` (lines 108–228) reveals critical methodological flaws and severe data leakage:

### A. Feature Precomputation on Full Dataset (Data Leakage)
- The matchup matrix (`matchup_matrix`), synergy matrix (`synergy_matrix`), and global hero win rates (`hero_winrate`) are calculated across the **entire dataset** `df` prior to any train/test split:
  ```python
  # Line 109-124: Matchup Matrix computed on all matches in df
  # Line 126-149: Synergy Matrix computed on all matches in df
  # Line 151-167: Hero Winrates computed on all matches in df
  # Line 169-206: Feature vector X constructed using these matrices
  ```
- Only *after* feature extraction is the data split into training and test sets on line 214:
  ```python
  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
  ```
- **Impact:** Matches in `X_test` have their outcomes directly baked into the matchup and synergy probabilities provided as features to the classifier. The model is being tested on features containing future knowledge of the exact match outcomes.

### B. Random vs. Time-Based Splitting
- The split is completely randomized (`train_test_split` with `random_state=42`).
- Dota 2 is a rapidly shifting meta game with frequent patches, balance shifts, and strategic adaptations. A random split permits matches from the same day or hour to appear in both train and test, destroying temporal independence.
- A legitimate evaluation requires a strictly **time-based or patch-based split** (train on historical matches, validate on intermediate matches, test strictly on the newest unseen matches).

### C. Recency Weighting
- `ml_pipeline/train.py` contains **no recency weighting whatsoever**; all matches are weighted uniformly ($1.0$).
- Where recency was attempted in early notebooks, weights were calculated relative to `datetime.now()` rather than relative to the match timestamp, creating inconsistent time-dilation across historical records.

---

## 4. Hero Identification Across Components (Names vs. IDs)

Hero identification is fragmented and fragile across the stack:

| Component | Identifier Type | Mechanism | Issues |
| :--- | :--- | :--- | :--- |
| **Frontend** (`Dota2Drafter.jsx`) | Local sequential IDs (`1..121`) | Static array `HEROES` with arbitrary indices (e.g. Arc Warden = 2). | Does not match Valve / OpenDota hero IDs (Arc Warden is 113). |
| **Network Payload** (`/suggest`) | English Hero Names | Converts local ID to string (e.g. `"Anti-Mage"`, `"Nature's Prophet"`). | Inefficient string serialization; vulnerable to casing, punctuation, and typographical bugs. |
| **Backend Resolution** (`scoring.py`) | Name-to-ID lookup | `name_to_id = {v.lower(): k for k, v in hero_map.items()}` | Drops any hero if spelling differs (e.g., apostrophes, hyphens). |
| **Model Pickles** (`*.pkl`) | Numeric OpenDota IDs | Keys are integer tuples `(hero_id, enemy_id)`. | Correct, but decoupled from frontend IDs. |

**Resolution Required:** Numeric Valve/OpenDota hero IDs must be the immutable API contract. The backend will serve `/heroes` with ID, localized name, roles, attribute, and image assets, and frontend will key exclusively on numeric IDs.

---

## 5. Dead Code, Duplicated Logic & Documentation Mismatches

### Dead Code Identified
1. `patch.py`: Hardcoded Jupyter notebook search-and-replace script.
2. `train_scheduler.py`: Dead scheduler referencing non-existent `notebooks/Untitled.ipynb`.
3. `main.py` (root): Legacy API superseded by `backend/main.py`.
4. `collect_to_psql.py`: Legacy collector superseded by `patch_aware_collector.py`.
5. `core/utils.py`: Prototype code referencing non-existent `app.py`.
6. `notebooks/second.py`: Redundant Python export of `second.ipynb`.
7. `matches.csv` (root): 104 KB static file tracked in git repository.

### Duplicated Logic
- **Heuristic formula:** `1.50 * m + 0.35 * s + 0.06 * (wr - 0.5)` is duplicated across `main.py`, `backend/scoring.py`, `ml_pipeline/compare.py`, and `core/utils.py`.
- **Feature vector assembly:** Repeated across `ml_pipeline/train.py`, `backend/scoring.py`, `ml_pipeline/compare.py`, and `core/utils.py`.

### README vs. Repository Discrepancies
1. **Model Architecture:** README claims `LightGBM (1200 estimators, 127 leaves)`. Code actually trains `XGBClassifier` in `ml_pipeline/train.py`.
2. **Reported Accuracy:** README claims `~69–72% test accuracy`. This figure was an illusion caused by data leakage (matrices computed over entire dataset including test set) and random splitting.
3. **Pipeline Directories:** README lists `fetch/` as the data fetching directory. No such directory exists in the repo.
4. **Makefile:** All targets in `Makefile` invoke non-existent scripts inside `fetch/` (`fetch/fetch.py`, `fetch/validator.py`, `fetch/scheduler.py`).
5. **Model Artifacts Location:** Docker Compose mounts `./model:/app/model`, but `./model` lacks `hero_avg_matchup.pkl` and `hero_winrate.pkl`, whereas `backend/model` contains them.

---

## 6. Action Plan for Remediation

1. **Phase 1 (Fix Evaluation):** Implement strict time-based train/val/test splitting. Compute all matchup, synergy, and win rate matrices strictly on `X_train`. Report honest metrics (Accuracy, Log-Loss, ROC-AUC, Brier score, calibration curve) against radiant-bias and matchup baselines.
2. **Phase 2 (Improve Scoring):** Implement Empirical-Bayes / Beta-prior shrinkage with recency weighting on matrices. Record sample sizes and assign confidence levels (`low`, `medium`, `high`). Calibrate a learned model combiner for `/suggest`.
3. **Phase 3 (Draft Realism):** Add role-aware drafting (`roles_needed` inference), ban list enforcement, and strict Pydantic draft validations.
4. **Phase 4 (Data & IDs):** Transition all API contracts to numeric hero IDs. Add patch-aware recency and model versioning under `model/<version>/`.
5. **Phase 5 (Codebase Quality):** Modularize backend into `app/`, add LRU request caching, update frontend with confidence meters, and enable environment configurability.
6. **Phase 6 (Tests, CI & Hygiene):** Provide minimal fixture dataset for zero-network testing, write comprehensive unit and integration tests, restore clean `Makefile`, and clean dead scripts.
7. **Phase 7 (Documentation):** Rewrite README with genuine metrics, document statistical methodology in `docs/METHOD.md`, and record changes in `CHANGELOG.md`.
