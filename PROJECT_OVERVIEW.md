# Project Overview: Dota 2 Drafter

A full-stack, machine learning-driven counter-picking and drafting recommendation system for Dota 2, featuring an automated data collection and retraining lifecycle, vector-search retrieval-augmented generation (RAG) for patch notes, telemetry monitoring, and remote supervision via Telegram.

---

## 1. Project Summary

**Dota 2 Drafter** is an end-to-end decision-support and drafting tool for competitive Dota 2 players, captains, and analysts. 

In Dota 2, matches are won or lost during the draft phase before the game even begins. Players must select 5 heroes while anticipating and countering the enemy team's 5 heroes. Simple winrate tables are misleading because globally strong heroes look good against everyone, and complex 5-on-5 synergies are ignored.

This platform solves that problem by:
1. **Intelligent Draft Recommendations**: Analyzing enemy heroes and existing allied picks to suggest the top 9 counter-picks, complete with quantitative scores and human-readable counter/synergy explanations.
2. **Dual-Engine Scoring**: Offering both normalized matrix-based heuristic calculations and deep XGBoost machine learning probability inference.
3. **Patch-Aware Data Lifecycle**: Scraping high-MMR public match data from the OpenDota API, isolating matches by Dota patch version, enforcing reproducible dataset snapshots, and automating retraining.
4. **Patch-Aware Semantic RAG**: Indexing official Dota 2 patch notes into a Qdrant vector database so players and supervisors can query why a hero is strong in the current meta.
5. **Production Telemetry & Remote Control**: Providing live Prometheus metrics, pre-provisioned Grafana dashboards, and a Telegram bot for remote management and health monitoring.

---

## 2. Tech Stack

| Layer / Domain | Technology | Purpose & Rationale |
| :--- | :--- | :--- |
| **Backend Framework** | **Python 3.11 + FastAPI** | High-performance, asynchronous REST API with automatic OpenAPI validation and modern typing. |
| **ASGI Server** | **Uvicorn** | Production ASGI server running multiple worker processes for concurrent request handling. |
| **Data Validation** | **Pydantic v2 + Pydantic Settings** | Strict request/response validation, draft constraints enforcement, and environment variable loading. |
| **Rate Limiting** | **SlowAPI (Limits)** | Token-bucket client IP rate limiting on public prediction endpoints to prevent abuse. |
| **Machine Learning** | **XGBoost, Scikit-Learn, LightGBM** | Gradient-boosted decision trees (`XGBClassifier`) for 124-dimensional draft win probability prediction. |
| **Numerical Processing**| **NumPy & Pandas** | Vectorized matrix transformations, synergy calculations, and tabular match data manipulation. |
| **Database (Relational)**| **PostgreSQL 15 (Alpine)** | Persistent relational storage for matches, patch lifecycle states, dataset versions, and collection runs. |
| **Database (Vector)** | **Qdrant** | Vector database for cosine similarity search over chunked and embedded Dota patch notes. |
| **Embeddings** | **FastEmbed (BAAI/bge-small-en-v1.5)** | Fast, lightweight local ONNX-based embedding generation without heavy PyTorch dependencies. |
| **Frontend UI** | **React 18/19, Vite, Tailwind/Custom CSS** | Dark-themed Dota 2 UI with responsive hero picker grid, role badges, and Steam CDN asset loading. |
| **Web Server / Proxy** | **Nginx (Alpine)** | Reverse proxy serving the built React bundle and forwarding `/api` traffic. |
| **Metrics & Monitoring**| **Prometheus** | Time-series scraper pulling request counters, latency histograms, and engine state from `/metrics`. |
| **Dashboards** | **Grafana 10** | Provisioned dashboards visualizing API throughput, error rates, p50/p95 latency, and system pulse. |
| **Remote Supervision** | **pyTelegramBotAPI (TeleBot)** | Remote supervisor bot providing operational slash commands (`/stats`, `/health`, `/deploy`, `/hero`). |
| **Containerization** | **Docker & Docker Compose** | Multi-container orchestration managing backend, frontend, postgres, qdrant, prometheus, grafana, and bot. |

---

## 3. Architecture Overview

The system is structured as a decoupled, multi-service architecture running inside an isolated Docker bridge network (`dota_net`):

```
                        +-----------------------------------------+
                        |           Steam / OpenDota API          |
                        +-----------------------------------------+
                                      |              |
           Live Matches (MMR > 4500)  |              | Patch Notes
                                      v              v
                     +---------------------+   +---------------------+
                     | patch_aware_        |   | bot/ingest_patch.py |
                     | collector.py        |   +---------------------+
                     +---------------------+              |
                                |                         | Embedded Vectors
                                v                         v
                     +---------------------+   +---------------------+
                     | PostgreSQL (dotadb) |   | Qdrant Vector DB    |
                     | - matches           |   | - patch_notes       |
                     | - patch_lifecycle   |   +---------------------+
                     | - dataset_metadata  |              ^
                     +---------------------+              |
                                |                         | Semantic Search
                                v                         |
                     +---------------------+              |
                     | orchestrator.py     |              |
                     | -> train_from_psql  |              |
                     | -> ml_pipeline/train|              |
                     +---------------------+              |
                                |                         |
                         Generates .pkl files             |
                                |                         |
                                v                         |
+------------------+     +---------------------+          |
| React Frontend   |---->| FastAPI Backend     |          |
| (Port 3000)      |     | (Port 8000)         |          |
+------------------+     | - /suggest          |          |
                         | - /model/reload     |          |
                         | - /metrics          |          |
                         +---------------------+          |
                                |         ^               |
                        Telemetry         | Control       |
                                v         |               |
                         +------------+   |        +---------------+
                         | Prometheus |   +--------| Telegram Bot  |
                         | (Port 9090)|<-----------| (Supervisor)  |
                         +------------+            +---------------+
                                |                         ^
                                v                         |
                         +------------+                   |
                         | Grafana    |            Remote User
                         | (Port 3001)|            (Phone / App)
                         +------------+
```

### Request and Data Flow:
1. **Data Ingestion**: `patch_aware_collector.py` queries OpenDota public matches, filters for valid 5v5 lineups, tags them with the Dota patch, and streams them into PostgreSQL.
2. **Readiness & Retraining**: Upon hitting collection thresholds, the state switches to `DATA_READINESS_CHECK`. `orchestrator.py` slices a deterministic boundary dataset (`matches_<patch>_<version>.csv`), trains the models via `ml_pipeline/train.py`, and triggers an atomic hot-reload.
3. **Draft Prediction Request**: The user selects heroes in the React UI or calls `POST /suggest`. The request passes SlowAPI rate limiting, Pydantic input validation, and scoring algorithms (either Heuristic normalized counter matrices or XGBoost ML probabilities).
4. **Patch Ingestion & RAG**: `bot/ingest_patch.py` fetches live hero balance changes, embeds them into 384-dimensional vectors with `fastembed`, and saves them to Qdrant. The Telegram bot responds to `/hero <name>` by running cosine vector similarity search.
5. **Observability**: FastAPI middleware records request duration and status into Prometheus histograms and counters. Prometheus scrapes the backend and Qdrant, feeding auto-provisioned Grafana dashboards and Telegram `/stats` commands.

---

## 4. Folder & File Structure

```
Dota-drafter/
├── .env.example                     # Sample environment file (TELEGRAM_TOKEN, DATABASE_URL)
├── .gitignore                       # Git ignore rules (excluding venvs, .pkl models, cache)
├── docker-compose.yml               # Production multi-service orchestration (7 services)
├── Makefile                         # Legacy developer task runner
├── Readme.md                        # Original project documentation and roadmap
├── prometheus.yml                   # Prometheus scrape configurations (backend, qdrant, self)
├── requirements.txt                 # Root Python requirements (collector & training tools)
│
├── backend/                         # Core FastAPI Web API
│   ├── Dockerfile                   # Python 3.11-slim container definition
│   ├── requirements.txt             # Backend dependencies (fastapi, uvicorn, slowapi, xgboost, etc.)
│   ├── config.py                    # Pydantic Settings class (MODEL_DIR, PREDICTION_ENGINE)
│   ├── logger.py                    # Standardized logging setup
│   ├── main.py                      # FastAPI app, middleware, routes, exception handlers
│   ├── models.py                    # Pydantic draft request/response schemas & validators
│   ├── scoring.py                   # Model registry, pickle loading, prediction algorithms
│   ├── model/                       # Serialized model directory (.pkl artifacts)
│   └── tests/                       # Pytest test suite
│       ├── test_api.py              # API endpoint functional tests
│       ├── test_scoring.py          # Scoring logic and helper unit tests
│       └── test_hardening.py        # Input validation, duplicate checks, security headers
│
├── frontend/                        # React Single Page Application (SPA)
│   ├── Dockerfile                   # Multi-stage build (Node 20 -> Nginx Alpine)
│   ├── nginx.conf                   # Nginx reverse proxy configuration
│   ├── package.json                 # NPM dependencies (React 19, Vite, TanStack Query)
│   └── src/
│       ├── App.jsx                  # Root React application component
│       ├── Dota2Drafter.jsx         # Main drafting workbench, hero grid, and pick recommendations
│       └── main.jsx                 # React DOM entrypoint
│
├── bot/                             # Telegram Supervisor Bot & RAG Service
│   ├── Dockerfile                   # Bot container definition
│   ├── requirements.txt             # Bot dependencies (pyTelegramBotAPI, qdrant-client, fastembed)
│   ├── bot.py                       # Telegram bot implementation with stats, health, and hero commands
│   ├── ingest_patch.py              # OpenDota patch notes fetcher, vectorizer, and Qdrant uploader
│   └── patch_notes.md               # Exported markdown copy of indexed hero patch changes
│
├── ml_pipeline/                     # Production Machine Learning Pipeline
│   ├── train.py                     # Standalone Python script extracted from training notebooks
│   └── compare.py                   # Side-by-side prediction audit (Heuristic vs XGBoost)
│
├── grafana/                         # Grafana Auto-Provisioning Configuration
│   └── provisioning/
│       ├── datasources/
│       │   └── prometheus.yml       # Auto-provisioned Prometheus datasource
│       └── dashboards/
│           ├── dashboards.yml       # Dashboard provider configuration
│           └── json/
│               └── dota_drafter_dashboard.json  # Pre-built monitoring dashboard
│
├── notebooks/                       # Exploratory Research & Legacy Notebooks
│   ├── first.ipynb                  # Initial EDA and data exploration
│   ├── second.ipynb                 # Prototype training notebook (matrix and XGBoost generation)
│   └── matches.csv                  # Working dataset symlink/copy for notebook reference
│
├── core/                            # Shared Utilities (Legacy)
│   └── utils.py                     # Original role scoring and predict helpers
│
├── lifecycle_manager.py             # Database state manager for patches and dataset versions
├── patch_aware_collector.py         # 5v5 validated match scraper tagged by patch version
├── train_from_psql.py               # Boundary-enforced dataset exporter and training trigger
├── orchestrator.py                  # End-to-end automation daemon (Detect -> Train -> Deploy)
├── collect_to_psql.py               # Legacy unversioned match scraper
├── train_scheduler.py               # Legacy date-based training scheduler
└── test_lifecycle.py                # Standalone verification script for lifecycle tables
```

---

## 5. Core Modules

### 1. `backend/scoring.py`
* **Purpose**: Core inference engine and artifact registry.
* **Key Functions**:
  * `load_models()`: Safely loads `.pkl` files with fallback defaults if files are missing; tracks file sizes and timestamps in `model_metadata`.
  * `resolve(names)`: Maps localized hero strings to Dota internal integer IDs.
  * `norm_matchup(hero_id, enemy_ids)`: Computes normalized advantage above a hero's baseline against enemy picks.
  * `synergy_score(hero_id, ally_ids)`: Calculates allied pair winrate deviation from 0.5.
  * `predict(hero_id, enemy_ids, ally_ids, engine)`: Abstract prediction router executing either fast heuristic math or 124-dimensional feature vector XGBoost inference.
* **Depended on by**: `backend/main.py`, `ml_pipeline/compare.py`.

### 2. `backend/models.py`
* **Purpose**: Pydantic schema validation and business rule enforcement.
* **Key Schemas**:
  * `DraftRequest`: Accepts `team` and `enemy` hero name lists. Enforces $\le 5$ heroes per team, trims whitespace, rejects duplicates within a team, and forbids cross-team overlaps.
  * `HeroSuggestion`: Output schema for ranked picks, scores, reasons, and role classifications.
  * `SuggestResponse`: Response wrapper containing `picks: list[HeroSuggestion]`.
* **Depended on by**: `backend/main.py`.

### 3. `lifecycle_manager.py`
* **Purpose**: Manages the PostgreSQL state machine governing Dota patches and datasets.
* **Key Functions**:
  * `init_lifecycle_db()`: Creates relational schema (`patches`, `patch_lifecycle`, `dataset_metadata`, `feature_metadata`).
  * `detect_patch(version)`: Registers new patches in state `PATCH_DETECTED`.
  * `transition_state(version, new_state)`: Updates lifecycle state (`DATA_COLLECTION`, `DATA_READINESS_CHECK`, `TRAINING`, `DEPLOYED`).
  * `register_dataset(version, dataset_version, match_count, is_ready)`: Freezes dataset boundary record.
  * `get_patches_in_state(state)`: Queries patches ready for retraining.
* **Depended on by**: `patch_aware_collector.py`, `train_from_psql.py`, `orchestrator.py`.

### 4. `patch_aware_collector.py`
* **Purpose**: Robust match data collector consuming the OpenDota API.
* **Key Functions**:
  * `fetch_public_matches(last_match_id)`: Fetches batches with backoff on HTTP 429 rate limits.
  * `validate_team(team)`: Ensures exactly 5 non-zero hero IDs per team.
  * Main collection loop: Inserts validated matches into PostgreSQL, updates Prometheus counters, and transitions patch state to `DATA_READINESS_CHECK` upon reaching target match thresholds.
* **Depended on by**: External pipelines / scheduled collection jobs.

### 5. `orchestrator.py`
* **Purpose**: Master automation orchestrator linking collection, training, and deployment.
* **Key Functions**:
  * `run_training(patch, dataset_version)`: Executes `train_from_psql.py` as a subprocess.
  * `deploy_models(patch)`: Calls `POST http://backend:8000/model/reload` to hot-swap models without downtime.
  * `main()`: Inspects database for `DATA_READINESS_CHECK` patches and drives them to `DEPLOYED`.

### 6. `bot/bot.py`
* **Purpose**: Remote Telegram management bot and RAG client.
* **Key Handlers**:
  * `/stats`: Queries Prometheus for total calls, latency, active engine, and loaded heroes.
  * `/api_stats`: Detailed endpoint breakdown, HTTP status distribution, and latency percentiles.
  * `/model_stats`: Inspects loaded `.pkl` files and disk sizes from backend.
  * `/health`: Pings Backend, Postgres, Qdrant, Prometheus, and Grafana.
  * `/hero <name>`: Performs semantic similarity search in Qdrant over Dota 2 patch notes.
  * `/deploy`: Triggers backend hot-reload remotely.

---

## 6. APIs & Endpoints

All backend endpoints are hosted on port `8000`. No external authentication is currently required; endpoints are secured via SlowAPI rate limiting and strict CORS.

| Method | Endpoint | Description | Input Parameters | Output Format | Rate Limit |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | Liveness & readiness check | None | `{"status": "ok", "heroes": 127}` | Default (120/m) |
| `GET` | `/metrics` | Prometheus metrics scrape target | None | Standard Prometheus text format | Exempt |
| `GET` | `/model/status` | Active model registry metadata | None | JSON object with loaded files, timestamps, and sizes | Default (120/m) |
| `POST` | `/model/reload` | Atomically reloads `.pkl` files from disk | None | `{"status": "success", "metadata": {...}}` | Default (120/m) |
| `GET` | `/heroes` | Complete dictionary of hero ID $\to$ localized name | None | `{"1": "Anti-Mage", "2": "Axe", ...}` | Default (120/m) |
| `GET` | `/debug` | Sample matchups, matrices, and hero counts | None | Diagnostic JSON dictionary | Default (120/m) |
| `POST` | `/suggest` | Primary drafting recommendation endpoint | `DraftRequest` JSON: `{"enemy": [...], "team": [...]}` | `SuggestResponse` JSON: Top 9 ranked picks with reasons | **60 / minute** |

---

## 7. Data Model

### Relational Schema (PostgreSQL `dotadb`)

#### 1. `matches`
* `match_id` (`BIGINT PRIMARY KEY`): Unique match identifier from Valve / OpenDota.
* `radiant_win` (`BOOLEAN`): True if Radiant won, False if Dire won.
* `radiant_team` (`TEXT`): Serialized array of 5 hero IDs.
* `dire_team` (`TEXT`): Serialized array of 5 hero IDs.
* `patch_version` (`VARCHAR(50)`): Associated Dota patch (e.g. `7.35d`).

#### 2. `patches`
* `patch_version` (`VARCHAR(50) PRIMARY KEY`): Patch string identifier.
* `detected_at` (`TIMESTAMP DEFAULT NOW()`): Timestamp when first recognized.
* `released_at` (`TIMESTAMP`): Official release date (if known).

#### 3. `patch_lifecycle`
* `id` (`SERIAL PRIMARY KEY`): Surrogate key.
* `patch_version` (`VARCHAR(50) REFERENCES patches`): Foreign key to patch.
* `state` (`VARCHAR(50)`): Current state (`PATCH_DETECTED`, `COLLECTION_ACTIVE`, `DATA_READINESS_CHECK`, `TRAINING`, `DEPLOYED`).
* `updated_at` (`TIMESTAMP DEFAULT NOW()`): Last transition timestamp.

#### 4. `dataset_metadata`
* `id` (`SERIAL PRIMARY KEY`): Unique dataset identifier.
* `patch_version` (`VARCHAR(50) REFERENCES patches`): Associated patch.
* `dataset_version` (`VARCHAR(50)`): Dataset version tag (e.g. `v1`).
* `match_count` (`INT`): Exact row count boundary.
* `created_at` (`TIMESTAMP DEFAULT NOW()`): Record creation time.
* `is_ready` (`BOOLEAN`): True when ready for training.

#### 5. `feature_metadata`
* `id` (`SERIAL PRIMARY KEY`): Unique feature set identifier.
* `dataset_id` (`INT REFERENCES dataset_metadata`): Foreign key.
* `feature_version` (`VARCHAR(50)`): Feature extraction configuration version.
* `created_at` (`TIMESTAMP DEFAULT NOW()`): Creation timestamp.

#### 6. `collection_runs`
* `id` (`SERIAL PRIMARY KEY`): Run identifier.
* `patch_version` (`VARCHAR(50) REFERENCES patches`): Target patch.
* `start_time` (`TIMESTAMP`): Run start time.
* `end_time` (`TIMESTAMP`): Run finish time.
* `matches_fetched` (`INT`): Total matches received from API.
* `matches_inserted` (`INT`): Clean matches inserted.
* `status` (`VARCHAR(50)`): Run status (`COMPLETED`, `FAILED`).

---

### Vector Database Schema (Qdrant)

#### Collection: `patch_notes`
* **Vector Configuration**: 384 dimensions, Cosine distance metric.
* **Payload Fields**:
  * `hero` (`str`): Localized hero name (e.g. `Pudge`, `Sven`).
  * `hero_lower` (`str`): Lowercase name for direct matching.
  * `text` (`str`): Formatted patch note changes, ability updates, and talent adjustments.

---

## 8. Setup & Run Instructions

### Prerequisites
* Docker & Docker Compose installed.
* Python 3.11 (if running local scripts outside Docker).
* Telegram Bot Token (optional, obtained from `@BotFather`).

### 1. Environment Configuration
Copy the sample environment file and insert your Telegram bot token:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
TELEGRAM_TOKEN=123456789:ABCDEFyour_telegram_bot_token_here
DATABASE_URL=postgresql://dotauser:dotapassword@localhost:5432/dotadb
```

### 2. Single-Command Startup
Build and start all 7 services via Docker Compose:
```bash
docker compose up -d --build
```

### 3. Service Ports & Access
* **Frontend Web App**: `http://localhost:3000`
* **FastAPI Backend**: `http://localhost:8000` (Docs: `http://localhost:8000/docs`, Metrics: `http://localhost:8000/metrics`)
* **Grafana Dashboard**: `http://localhost:3001` (Credentials: `admin` / `admin`)
* **Prometheus Targets**: `http://localhost:9090/targets`
* **Qdrant Vector DB**: `http://localhost:6333/dashboard`
* **PostgreSQL**: `localhost:5432` (`dotadb` / `dotauser` / `dotapassword`)

### 4. Running Backend Tests
Execute the test suite directly inside the backend container:
```bash
docker exec -e PYTHONPATH=. dota_backend pytest tests
```

### 5. Ingesting Patch Notes into Vector DB
To populate Qdrant with patch notes for all 127 Dota heroes:
```bash
docker exec dota_supervisor_bot python ingest_patch.py
```

### 6. Executing Pipeline Manually
To scrape matches and train outside Docker:
```bash
python patch_aware_collector.py --target 1000 --patch 7.35d
python orchestrator.py
```

---

## 9. Key Dependencies

### Backend Dependencies
* `fastapi` & `uvicorn`: High-performance asynchronous API framework and web server.
* `pydantic` & `pydantic-settings`: Data validation, custom validators, and typed configuration management.
* `slowapi`: Rate limiting library backed by `limits` to guard against API flooding.
* `xgboost`: Gradient-boosted decision trees for ML drafting probabilities.
* `scikit-learn` & `lightgbm`: Model training evaluation metrics, log-loss, and tabular utilities.
* `numpy` & `pandas`: Vector math and tabular dataset manipulation.
* `prometheus-client`: Telemetry exporter instrumenting latency histograms and request counters.
* `pytest` & `httpx`: Synchronous and asynchronous test client for automated unit tests.

### Bot & RAG Dependencies
* `pyTelegramBotAPI`: Telegram Bot API wrapper handling long polling and slash command routing.
* `qdrant-client`: Official Python client for vector database collection management and search.
* `fastembed`: Lightweight, ONNX-accelerated local embedding generation using `BAAI/bge-small-en-v1.5`.

### Frontend Dependencies
* `react` & `react-dom`: Declarative UI library.
* `vite`: Fast build tool and development server.
* `@tanstack/react-query`: Asynchronous state and data fetching.
* `framer-motion`: Motion and UI transition animations.

---

## 10. Known Issues, Inconsistencies & Future Work

1. **Obsolete `Makefile` and Workflow References**:
   * Root `Makefile` and `.github/workflows/auto-retrain.yml` reference a `fetch/` directory and scripts (`fetch.py`, `validator.py`, `scheduler.py`) that do not exist. The actual implemented pipeline lives in `patch_aware_collector.py`, `lifecycle_manager.py`, and `orchestrator.py`.
2. **Duplicate Legacy Files in Root**:
   * Root `main.py` is an unhardened, monolithic legacy copy of the API. The actual production API lives inside `backend/main.py`.
   * Root `collect_to_psql.py` is the unversioned precursor to `patch_aware_collector.py`.
   * Root `train_scheduler.py` is a date-based prototype superseded by `orchestrator.py`.
3. **Multi-Worker Hot-Reload Constraint**:
   * `backend/Dockerfile` runs Uvicorn with `--workers 2`. When `/model/reload` is invoked via HTTP, it only updates the specific worker handling that request unless both workers are cycled or the container is restarted.
4. **Notebook MIN_GAMES Hardcoding**:
   * In `notebooks/second.ipynb`, `MIN_GAMES = 10` filters out heroes with fewer than 10 matches. When testing with small datasets (<100 matches), this filter drops all heroes and causes `train_test_split` to fail. `ml_pipeline/train.py` handles this dynamically, but the notebook remains sensitive to small datasets.
5. **No Persistent Collector Daemon in Compose**:
   * `patch_aware_collector.py` is currently run on-demand or triggered via script; it is not yet registered as a continuously running cron service inside `docker-compose.yml`.

---

## 11. Glossary

* **MMR (Match Making Rating)**: Numeric skill ranking in Dota 2. The collector filters for matches $\ge 4500$ MMR (Divine / Immortal rank) to ensure training data reflects competent play.
* **Matchup Matrix**: A precomputed matrix storing pairwise winrates of Hero A playing against Hero B.
* **Synergy Matrix**: A precomputed matrix storing pair winrates when Hero A and Hero B are on the same team.
* **Normalized Matchup Score**: Adjustment that subtracts a hero's global average winrate from their matchup winrate against a specific enemy, preventing globally dominant meta heroes from falsely appearing as universal counters.
* **Dota Patch**: Periodic game update released by Valve (e.g. `7.35d`, `7.41`) that alters hero attributes, ability numbers, and map geometry, invalidating previous draft dynamics.
* **RAG (Retrieval-Augmented Generation)**: Architecture that retrieves relevant factual context (Dota patch notes) from a vector database to ground answers before presenting them to the user.
* **Qdrant**: High-performance open-source vector search engine designed for storing embeddings and filtering payloads.
* **FastEmbed**: Lightweight embedding library from Qdrant that runs optimized ONNX models without requiring heavy PyTorch or CUDA runtimes.
* **Hot-Reload**: The capability to atomically swap in-memory machine learning models on a running web server without restarting the process or dropping client requests.
