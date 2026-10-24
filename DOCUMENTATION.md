# Dota 2 Drafter — Comprehensive Project Documentation & Technical Architecture

---

## Table of Contents
1. [Executive Summary & Project Mission](#1-executive-summary--project-mission)
2. [High-Level Architecture & System Topology](#2-high-level-architecture--system-topology)
3. [Full Technology Stack & Technical Justifications](#3-full-technology-stack--technical-justifications)
4. [Mathematical Modeling & Machine Learning Methodology](#4-mathematical-modeling--machine-learning-methodology)
5. [Role-Aware Tactical Engine & Kit Breakdown System](#5-role-aware-tactical-engine--kit-breakdown-system)
6. [Chronological Project Evolution (Phases 0 Through 10)](#6-chronological-project-evolution-phases-0-through-10)
7. [Major Problems Encountered & Engineering Solutions](#7-major-problems-encountered--engineering-solutions)
8. [API Contracts, Telemetry & Telegram Bot Integration](#8-api-contracts-telemetry--telegram-bot-integration)
9. [Operational Guides: Setup, Testing, Training & Deployment](#9-operational-guides-setup-testing-training--deployment)

---

## 1. Executive Summary & Project Mission

**Dota 2 Drafter** is an enterprise-grade, mathematically calibrated, leakage-free machine learning counter-pick engine and tactical recommendation advisor for competitive Dota 2.

In high-MMR competitive Dota 2 (4,500+ MMR through Immortal), the drafting phase establishes the fundamental win conditions of the match. Historically, publicly available drafting tools suffered from critical methodological flaws:
1. **Target Data Leakage**: Matchup matrices and hero statistics were calculated across the entire dataset before training/test splits, contaminating test benchmarks and generating wildly inflated accuracy claims (e.g. 70–80%).
2. **Small-Sample Spurious Counters**: Infrequently played hero matchups with 1 or 2 lucky wins were ranked as "100% hard counters", misleading players into drafting ineffective heroes.
3. **Disconnected Production Architectures**: Machine learning models (e.g. LightGBM, XGBoost) were trained offline, yet bypassed in production in favor of arbitrary hardcoded heuristic weights.
4. **Role Contamination & Missing Context**: Recommendations failed to respect standard lane positions (e.g. recommending Hard Supports in the Offlane or Midlane) and lacked explanations detailing *how* or *why* a hero counters enemies or provides needed stuns and mobility.

This project transformed an experimental script into a production-ready, research-grade drafting system featuring:
- **Zero Data Leakage** across strict temporal train/val/test splits.
- **Empirical-Bayes Shrinkage ($k=20.0$)** to eliminate low-sample noise.
- **Learned Stacking Combiner** pairing nonlinear gradient-boosted trees with pairwise matchup advantages and synergies.
- **Role-Aware Tactical Advisor** providing 10 picks per role (Carry, Mid, Offlane, Soft Support, Hard Support) with hero-specific explanations covering disables, stuns, and mobility.
- **Resilient Cloud & CI/CD Infrastructure** deployed to Render and Vercel with automated daily match ingestion, retrain pipelines, and Telegram bot telemetry.

---

## 2. High-Level Architecture & System Topology

The system comprises five decoupled tiers communicating over standardized HTTP and database protocols:

```
                                  ┌────────────────────────────────────────┐
                                  │           OpenDota REST API            │
                                  │      (High-MMR Public Matches)         │
                                  └───────────────────┬────────────────────┘
                                                      │ Rate-limited (1.2s delay)
                                                      ▼
┌──────────────────────┐         ┌────────────────────────────────────────┐
│     Telegram Bot     │◄────────┤    Automated Collector & Retrainer     │
│ (Telemetry & Queries)│         │       (scripts/orchestrator.py)        │
└──────────┬───────────┘         └───────────────────┬────────────────────┘
           │ Webhook                                 │
           ▼                                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      PostgreSQL Relational Storage                      │
│            (Matches, Patches, Hero Metadata, Training Datasets)         │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      ML Pipeline (ml_pipeline/)                         │
│  - Zero-Leakage Chronological Split (Train: 70%, Val: 15%, Test: 15%)   │
│  - Empirical-Bayes Shrinkage (k=20) & Recency Decay (lambda=0.2)        │
│  - LightGBM Booster + Stacked Logistic Regression Combiner              │
│  - Versioned Artifact Storage (backend/model/vYYYY.MM.DD/)              │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     FastAPI Production Backend (Render)                 │
│  - Thread-Safe LRU Response Cache (app/cache.py)                        │
│  - 127-Hero Tactical Knowledge Engine (app/hero_knowledge.py)           │
│  - Strict Pydantic v2 Schema Validation (app/schemas.py)                │
│  - Dual Input Contract (Valve Numeric IDs & Localized Names)            │
│  - Prometheus Metrics (/metrics) & Health Freshness (/health)           │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ JSON REST API
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       React 18 + Vite Frontend (Vercel)                 │
│  - Interactive 127-Hero Selection Grid & Dedicated Ban Dock             │
│  - Categorized Role Tabs (All, Carry, Mid, Offlane, Soft Supp, Hard Supp)│
│  - 10 Picks Per Category with Confidence Badges & Tactical Breakdowns   │
│  - Mobile Responsive Layout with Floating Action Bar                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Full Technology Stack & Technical Justifications

### 3.1 Frontend Tier
- **React 18 (SPA)**: Provides declarative UI state synchronization across 10 drafted hero slots, active bans, selected roles, and dynamic recommendation cards.
- **Vite 5**: Chosen over Create React App / Webpack for ultra-fast Hot Module Replacement (HMR) during development and optimized tree-shaken production ES bundles (~71 kB gzip).
- **Tailwind CSS**: Utility-first CSS framework delivering responsive design tokens, high-contrast dark gaming aesthetics (`#0c1015` canvas, gold/crimson/emerald accents), and zero CSS bloat.
- **Lucide React**: Lightweight vector icon suite providing contextual visual glyphs for roles, armor, stuns, mobility, and confidence ratings.
- **Vercel**: Serverless edge hosting providing instant global CDN distribution, automatic preview deployments on PRs, and seamless Git-integrated CI/CD.

### 3.2 Backend & API Tier
- **Python 3.11**: Offers significant performance gains (Specializing Adaptive Interpreter) over older Python runtimes, reducing JSON serialization latency and matrix manipulation overhead.
- **FastAPI 0.111+**: High-performance ASGI framework built on Starlette and Pydantic. Delivers native async request handling, automated OpenAPI/Swagger documentation, and sub-millisecond route dispatching.
- **Pydantic v2 (Rust-backed core)**: Handles strict payload validation, data normalization (e.g. canonicalizing `soft_support` vs `support`), intra-list deduplication, and cross-team disjoint constraints.
- **Uvicorn**: Lightning-fast ASGI production server worker implementation using `uvloop` and `httptools`.
- **SlowAPI**: Redis/in-memory rate limiter protecting public endpoints from automated scraping and denial-of-service attempts.
- **Prometheus Client**: Exports standard latency histograms, request counters, and active model version gauges on `/metrics`.

### 3.3 Machine Learning & Mathematical Computing
- **NumPy & SciPy**: Vectorized pairwise matrix operations for fast shrinkage calculation, recency decay weighting, and probability calibration.
- **LightGBM 4.3**: Highly efficient Gradient Boosted Decision Tree (GBDT) framework. Uses histogram-based binning and leaf-wise tree growth to model high-order nonlinear hero interactions and team compositions with minimal memory footprint.
- **Scikit-Learn**: Used for fitting the Logistic Regression stacking combiner, evaluating Brier loss, computing ROC-AUC curves, and isotonic calibration.

### 3.4 Data Ingestion & Storage
- **PostgreSQL 15+**: Relational match database storing 100,000+ validated 5v5 matches, patch histories, and training metadata with ACID guarantees.
- **OpenDota API**: Primary ingestion stream for high-MMR public match IDs, radiant/dire team compositions, match timestamps, and patch designations.
- **PyTelegramBotAPI (telebot)**: Enables two-way Telegram bot communication, webhook handling on cloud environments, and on-demand model telemetry reporting.

---

## 4. Mathematical Modeling & Machine Learning Methodology

### 4.1 The Zero Data Leakage Principle
A fundamental principle of this project is strict temporal ordering:
$$\mathcal{D}_{\text{train}} \prec \mathcal{D}_{\text{val}} \prec \mathcal{D}_{\text{test}}$$

- Matches are strictly sorted by `match_id` / `start_time`.
- **Training Set (70%)**: All global hero win rates, pairwise matchup advantage matrices, synergy matrices, and LightGBM trees are computed strictly on this chronological slice.
- **Validation Set (15%)**: Used solely to fit stacking combiner coefficients and tune shrinkage hyperparameter $k$.
- **Test Set (15%)**: Completely unseen future matches used exclusively for final out-of-sample benchmark evaluation.

### 4.2 Empirical-Bayes Shrinkage ($k=20.0$)
Raw win rates in pairwise hero matchups are noisy when sample sizes are small. For instance, if Hero $A$ played against Hero $B$ only twice and won both, the raw win rate is $100\%$ ($+50\%$ advantage). Recommending Hero $A$ based on this is spurious.

We apply Empirical-Bayes Beta-prior shrinkage:
$$\hat{P}_{ij} = \frac{n_{ij} \cdot w_{ij} + k \cdot \bar{P}_{i}}{n_{ij} + k}$$

Where:
- $n_{ij}$ = total matches played between Hero $i$ and Hero $j$.
- $w_{ij}$ = observed win rate of Hero $i$ against Hero $j$.
- $\bar{P}_{i}$ = baseline prior win rate of Hero $i$.
- $k = 20.0$ = empirical shrinkage strength constant.

When $n_{ij} \to 0$, $\hat{P}_{ij} \to \bar{P}_{i}$ (reverts to baseline). Only when $n_{ij} \gg 20$ does the observed matchup dominate.

### 4.3 Exponential Patch Recency Weighting
Dota 2 balance shifts across game patches. Matches from earlier patches are down-weighted using exponential decay:
$$\omega(m) = \exp\left(-\lambda \cdot \Delta_{\text{patch}}(m)\right)$$
Where $\lambda = 0.2$ and $\Delta_{\text{patch}}(m)$ is the patch distance from the active version.

### 4.4 Learned Stacking Combiner
Rather than guessing arbitrary weights, we combine our four core predictive signals using a Logistic Regression meta-model fitted on the validation slice:

$$z = \beta_0 + \beta_M \cdot S_{\text{matchup}} + \beta_S \cdot S_{\text{synergy}} + \beta_W \cdot S_{\text{winrate}} + \beta_{\text{tree}} \cdot \hat{P}_{\text{LGBM}}$$
$$\hat{P}(\text{Win}) = \frac{1}{1 + e^{-z}}$$

Learned validation coefficients:
- $\beta_M = 1.5644$ (Matchup Advantage)
- $\beta_S = 1.5201$ (Team Synergy)
- $\beta_W = 0.9665$ (Baseline Hero Win Rate)
- $\beta_{\text{tree}} = 2.1890$ (LightGBM Draft Vector Probability)
- $\beta_0 = 0.1045$ (Radiant Side Bias Adjustment)

### 4.5 Honest Metric Reporting & Theoretical Ceiling
In competitive Dota 2, draft sets initial win conditions, but in-game execution (laning, vision, smoke ganks, item timings, buybacks) dictates final outcomes. The theoretical ceiling for draft-only prediction in high-MMR matches is **55%–58%**.

**Leakage-Free Test Benchmark (2,237 strictly future matches):**
| Model Configuration | Test Accuracy | ROC-AUC | Log-Loss | Brier Score | Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Radiant Base Prior** | 54.09% | 0.5000 | 0.6922 | 0.2483 | Constant prediction of Radiant win frequency |
| **Hero Win Rate Sum** | 54.81% | 0.5519 | 0.6908 | 0.2481 | Sum of individual hero baseline win rates |
| **Matchup-Only Score** | 52.79% | 0.5484 | 0.6917 | 0.2486 | Pairwise counter scores without nonlinear model |
| **Standalone LightGBM** | 55.48% | 0.5694 | 0.6872 | 0.2468 | GBDT on 127-hero one-hot draft vectors |
| **Full Learned Combiner**| **55.52%** | **0.5757** | **0.6865** | **0.2467** | **Stacked Combiner with Shrinkage (Optimal)** |

---

## 5. Role-Aware Tactical Engine & Kit Breakdown System

A common flaw in earlier drafting tools was treating all heroes identically regardless of position. Recommending a hard support hero for an offlane pick or suggesting a carry when the team already has three cores leads to unplayable team compositions.

### 5.1 Canonical Role Definitions
The engine classifies all 127 Dota 2 heroes into canonical competitive roles derived from high-MMR meta patterns:
1. **Carry (Position 1)**: Primary late-game physical/magical cores that require gold priority (e.g. Anti-Mage, Faceless Void, Phantom Assassin, Slark).
2. **Midlane (Position 2)**: Solo laners requiring rapid level scaling and active tempo control (e.g. Storm Spirit, Puck, Ember Spirit, Invoker, Queen of Pain).
3. **Offlane (Position 3)**: Frontline initiators, aura carriers, and space creators (e.g. Centaur Warrunner, Mars, Tidehunter, Slardar, Axe).
4. **Soft Support (Position 4)**: Roaming playmakers, secondary initiators, and utility disablers (e.g. Earthshaker, Tusk, Rubick, Mirana, Clockwerk).
5. **Hard Support (Position 5)**: Lane babysitters, vision controllers, and defensive save providers (e.g. Crystal Maiden, Dazzle, Oracle, Disruptor, Treant Protector).

Supports are strictly quarantined from showing up in core positions (Offlane / Mid), and dedicated midlaners are segregated from general cores.

### 5.2 10 Picks Per Category Architecture
The API outputs **10 ranked suggestions** for every role category simultaneously:
- `categories["all"]`: Top 10 overall counters regardless of role.
- `categories["carry"]`: Top 10 position 1 heroes.
- `categories["mid"]`: Top 10 position 2 heroes.
- `categories["offlane"]`: Top 10 position 3 heroes.
- `categories["soft_support"]`: Top 10 position 4 heroes.
- `categories["hard_support"]`: Top 10 position 5 heroes.

### 5.3 Missing-Role Inference & Kit Breakdown
When a user inputs allied heroes, the engine detects unfulfilled positions:
- If 4 allies are drafted and the missing role is Midlane, recommendations explain:
  - How the candidate hero controls the midlane tempo.
  - Their specific **stuns and disables** to shut down enemy initiations.
  - Their **mobility and movement skills** to rotate and secure runes/ganks.
- Generic fallback boilerplate (e.g. *"Strong synergy with team composition"*) was completely eliminated. The knowledge engine (`backend/app/hero_knowledge.py`) generates distinct tactical breakdowns for all 127 heroes.

---

## 6. Chronological Project Evolution (Phases 0 Through 10)

### Phase 0: System Audit & Baseline Discovery (2026-10-19)
- Audited legacy codebase, discovering severe data leakage in `ml_pipeline/train.py`.
- Found that LightGBM models were trained but bypassed in `/suggest` due to `PREDICTION_ENGINE = "heuristic"`.
- Identified arbitrary 1..121 hero ID mappings disconnected from Valve's official hero IDs.
- Audited dead scripts (`patch.py`, `train_scheduler.py`, `collect_to_psql.py`).

### Phase 1: Leakage Elimination & Chronological Splitting (2026-10-19)
- Replaced random splitting with chronological time splits.
- Enforced zero-leakage guarantee: all feature matrices computed solely on training slice.
- Corrected misleading 70%+ accuracy claims with real test metrics (55.52%).

### Phase 2: Empirical-Bayes Shrinkage & Learned Combiner (2026-10-19)
- Derived and implemented Beta-prior shrinkage ($k=20.0$) with recency decay ($\lambda=0.2$).
- Fitted Logistic Regression stacking combiner on validation data.
- Added confidence ratings (`high`, `medium`, `low`) and sample size transparency.

### Phase 3: Draft Realism, Bans, Roles & Validation (2026-10-20)
- Built automated role inference for missing team positions.
- Implemented ban filtering (guaranteed exclusion of picked/banned heroes).
- Added Pydantic schema validation: max 5 enemies, max 4 allies, disjoint team lists, and dual string/ID contracts.

### Phase 4: Hero Metadata Architecture & Versioning (2026-10-20)
- Built canonical 127-hero metadata repository (`backend/model/heroes_metadata.json`) with CDN image assets and roles.
- Created automated versioned artifact management (`backend/model/<version>/`) with hot reload capabilities (`POST /model/reload`).

### Phase 5: Modular Backend Architecture & React Frontend (2026-10-20)
- Modularized backend into clean domain packages (`app/config.py`, `app/schemas.py`, `app/scoring.py`, `app/routes/`).
- Implemented thread-safe in-memory LRU caching for `/suggest`.
- Rebuilt React frontend with responsive hero picker grid, dedicated ban dock, role filter tabs, and confidence tags.

### Phase 6: Hermetic Test Suite, CI Automation & Repo Hygiene (2026-10-20)
- Generated hermetic 1,500-match offline fixture dataset (`tests/fixtures/matches_fixture.csv`).
- Authored 20+ unit and integration tests covering shrinkage formulas, zero-leakage splits, bounds, and API contracts.
- Configured GitHub Actions CI workflow running Ruff linting, Mypy type-checking, pytest, frontend Vite build, and Docker builds.

### Phase 7: Methodology Documentation & Open-Source Release (2026-10-20)
- Authored comprehensive `Readme.md`, `CHANGELOG.md`, `AUDIT.md`, and mathematical `docs/METHOD.md`.
- Released under MIT License.

### Phase 8: 100k Match Scale, Patch 7.35f & Telegram Telemetry (2026-10-21)
- Upgraded data collector to track patch 7.35f and handle OpenDota API exhaustion automatically.
- Scaled training dataset to 100,000 matches.
- Added Telegram bot commands (`/status`, `/freshness`, `/model`, `/matches`) for live model telemetry.

### Phase 9: 10 Picks Per Role, Tactical One-Liners & Movement Analysis (2026-10-23)
- Expanded suggestions to 10 picks across each role tab.
- Synthesized tactical one-liners explaining role performance, disables/stuns, and mobility for all 127 heroes.
- Added missing-role context when 4 allies are picked.
- Enforced canonical role sets to eliminate support contamination in core positions.

### Phase 10: Backward-Compatible Role Schema & CI Hardening (2026-10-24)
- Diagnosed and resolved HTTP 422 error when selecting `soft_support` on deployed frontends.
- Mapped sub-roles in `frontend/src/Dota2Drafter.jsx` to maintain 100% backward compatibility with deployed backends.
- Updated backend validation schemas in `models.py` and `app/schemas.py`.
- Formatted imports to comply with Ruff CI rules, verified all checks green, and merged PR #4 into `main`.

---

## 7. Major Problems Encountered & Engineering Solutions

### Problem 1: Severe Target Data Leakage in Initial ML Pipeline
- **Symptom**: Model benchmarks claimed 69–72% accuracy, yet in real-world matches the recommendations performed poorly.
- **Root Cause**: Pairwise matchup and synergy matrices were computed over the entire CSV before random train/test splitting. Test matches were leaking directly into the lookup tables.
- **Solution**: Implemented strict chronological splitting in `ml_pipeline/prepare_data.py` and `ml_pipeline/evaluate.py`. Verified with an automated test (`tests/test_leakage.py`) that test/validation matches never influence training feature matrices.

### Problem 2: Small-Sample Noise & Wild Recommendation Swings
- **Symptom**: Rare hero matchups (e.g. Meepo vs Chen with 1 recorded game) were scored as 100% hard counters, crowding out proven competitive picks.
- **Root Cause**: Maximum Likelihood Estimation without Bayesian regularization overfits heavily on small $N$.
- **Solution**: Derived and implemented Empirical-Bayes Beta-prior shrinkage ($k=20.0$). Unseen or low-sample matchups shrink automatically toward the hero's baseline win rate. Added explicit confidence ratings (`high`, `medium`, `low`) and sample sizes to API responses.

### Problem 3: Disconnected Production Architecture (Model Bypassed)
- **Symptom**: The LightGBM model was trained and saved to disk, but the API was hardcoded to `PREDICTION_ENGINE = "heuristic"`.
- **Root Cause**: Scoring logic had no unified interface to combine continuous probability predictions from tree models with discrete matchup advantage matrices.
- **Solution**: Engineered a learned Stacking Combiner using Logistic Regression fitted on validation data. Set default `PREDICTION_ENGINE = "combined"`, utilizing both tree model draft vectors and shrunk pairwise advantages.

### Problem 4: Telegram Bot HTTP 409 Conflict Errors on Cloud Restarts
- **Symptom**: Deploying or restarting the backend container on Render caused the Telegram bot to crash in a loop with `telegram.error.ConflictError: 409 Conflict: terminated by other getUpdates request`.
- **Root Cause**: Render spins up a new container before terminating the old one (zero-downtime rolling deploys). Both instances attempted concurrent long-polling via `getUpdates`.
- **Solution**: Implemented automatic Telegram webhook registration when running on Render (`RENDER_EXTERNAL_URL`), with graceful fallback backoff and an `ENABLE_EMBEDDED_BOT` environment variable flag.

### Problem 5: OpenDota Rate Limits & API Key Exhaustion
- **Symptom**: Automated data collection scripts crashed after several hundred calls due to HTTP 429 Too Many Requests and API key quota exhaustion.
- **Root Cause**: Unthrottled asynchronous requests exceeded the free tier limit of 60 calls/minute.
- **Solution**: Built `scripts/patch_aware_collector.py` with strict rate-limiting (1.2-second sleep between calls), exponential backoff on HTTP 429/5xx errors, and automatic fallback across multiple API endpoints.

### Problem 6: CI Pipeline Failures on Modern Node & Missing Fixtures
- **Symptom**: GitHub Actions failed during frontend Vite build and pytest execution.
- **Root Cause**: Node 18 was incompatible with Vite 5's modern chunking; tests failed because the large production `matches.csv` was rightly gitignored.
- **Solution**: Upgraded CI workflow to Node 20. Created a committed hermetic 1,500-match fixture (`tests/fixtures/matches_fixture.csv`) and added synthetic test fallbacks so CI runs offline with zero external dependencies.

### Problem 7: Cross-Role Contamination & Missing Context in Drafting
- **Symptom**: Supports like Crystal Maiden and Shadow Shaman were recommended for the Offlane; recommendations lacked explanations of how to play the hero against the enemy lineup.
- **Root Cause**: The recommendation algorithm scored heroes purely on win rate differential without role filters or tactical ability knowledge.
- **Solution**: Established canonical competitive role sets. Expanded suggestions to 10 picks per role. Authored a 127-hero tactical knowledge base (`backend/app/hero_knowledge.py`) providing situational breakdowns of stuns, disables, mobility, and lane execution.

### Problem 8: The `soft_support` HTTP 422 Validation Error on Cloud Deploys
- **Symptom**: Clicking "SOFT SUPP (POS 4)" on the deployed Vercel frontend returned HTTP 422: `Invalid role 'soft_support'. Valid roles are: carry, mid, offlane, support`.
- **Root Cause**: The frontend sent `roles_needed: ["soft_support"]`, but the live Render backend validator only accepted `support`.
- **Solution**: 
  1. Frontend: mapped `soft_support` and `hard_support` to `'support'` in outgoing `roles_needed` query parameters while preserving client-side role tab rendering.
  2. Backend: expanded `valid_roles` in `backend/models.py` and `backend/app/schemas.py` to natively accept `soft_support` and `hard_support`.
  3. CI: Fixed import sorting in `backend/scoring.py` to pass Ruff checks, verified green CI, and merged PR #4.

---

## 8. API Contracts, Telemetry & Telegram Bot Integration

### 8.1 Primary API Endpoints

#### `POST /suggest`
Calculates optimal hero recommendations based on draft context.
- **Request Body (`DraftRequest`)**:
  ```json
  {
    "enemy": ["Anti-Mage", "Huskar"],
    "team": ["Crystal Maiden", "Centaur Warrunner"],
    "bans": ["Meepo"],
    "roles_needed": ["mid"],
    "role_aware": true,
    "bracket": "all"
  }
  ```
- **Response Body (`SuggestResponse`)**:
  - `picks`: Top 10 overall recommendations.
  - `categories`: Role-specific suggestions (`carry`, `mid`, `offlane`, `soft_support`, `hard_support`), each containing 10 heroes.
  - `roles_needed`: List of active target roles.
  - `bracket_note`: Explanatory note if falling back from a specific bracket.

#### `GET /heroes`
Returns full canonical metadata for all 127 heroes:
```json
[
  {
    "id": 1,
    "name": "Anti-Mage",
    "short_name": "antimage",
    "roles": ["carry"],
    "primary_attr": "agi",
    "img_url": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/antimage.png"
  }
]
```

#### `GET /health`
Surfaces system status, active model version, and data freshness metrics:
```json
{
  "status": "ok",
  "heroes": 127,
  "model_version": "v2026.10.23",
  "data_freshness": {
    "latest_match_id": 9057394991,
    "latest_patch": "7.35f",
    "match_count": 99889,
    "training_matches": 69922,
    "validation_matches": 14983,
    "test_matches": 14984,
    "latest_match_timestamp": "2026-10-23T02:42:09.931048"
  }
}
```

### 8.2 Telegram Bot Telemetry
The integrated Telegram Bot provides mobile telemetry and drafting queries:
- `/start` or `/help`: Display available bot commands.
- `/status` or `/freshness`: Inspect live match count, training sample splits, and model version.
- `/model`: Display active model hyperparameters, shrinkage constant ($k=20$), and stacking weights.
- `/suggest <enemy_hero>`: Get quick mobile counter recommendations against specific enemy picks.

---

## 9. Operational Guides: Setup, Testing, Training & Deployment

### 9.1 Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/ZainSyed1678/Dota-drafter.git
cd Dota-drafter

# 2. Set up Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Set up Frontend dependencies
cd frontend
npm install
cd ..

# 4. Run local backend server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# 5. Run local frontend server
cd frontend
npm run dev
```

### 9.2 Running the Test Suite & Linters

```bash
# Run full pytest suite (23 tests passing)
pytest tests/ -v

# Run Ruff linter across all packages
ruff check backend ml_pipeline tests scripts

# Type check with mypy
mypy backend/app ml_pipeline --ignore-missing-imports
```

### 9.3 Retraining Pipeline

```bash
# 1. Prepare raw match data into clean 5v5 chronological dataset
python ml_pipeline/prepare_data.py --input data/matches.csv --output data/clean_matches.csv

# 2. Run zero-leakage training with shrinkage & stacking
python ml_pipeline/train.py --data data/clean_matches.csv --version v$(date +%Y.%m.%d)

# 3. Evaluate out-of-sample benchmarks on test slice
python ml_pipeline/evaluate.py --data data/clean_matches.csv
```

### 9.4 Docker Compose Deployment

```bash
# Start complete stack (FastAPI, React, Postgres, Prometheus)
docker compose up --build -d

# Check service logs
docker compose logs -f backend

# Tear down stack
docker compose down
```

---

*Authored by Antigravity AI Engineering Team on behalf of Zain Syed.*  
*Dota 2 is a registered trademark of Valve Corporation. This project is an independent open-source research and educational tool.*
