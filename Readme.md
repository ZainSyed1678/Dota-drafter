<div align="center">

<img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/global/dota2_logo_symbol.png" width="80" alt="Dota 2 Logo"/>

# Dota 2 Drafter

**A mathematically calibrated, leakage-free machine learning counter-pick engine for Dota 2**

Pick your enemies, allies, and bans → get the strongest counters ranked with empirical-Bayes shrinkage, role-aware inference, and learned model stacking.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![LightGBM](https://img.shields.io/badge/LightGBM-4.3-orange?style=flat-square)](https://lightgbm.readthedocs.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docs.docker.com/compose)
[![Tests](https://img.shields.io/badge/Pytest-20%20Passed-brightgreen?style=flat-square)](tests/)

</div>

---

## 1. Overview & Architectural Transformation

Dota 2 Drafter analyzes high-MMR public matches (4500+ MMR) to recommend optimal hero picks. Previously, draft prediction tools suffered from severe statistical flaws: random data splits leaking future match statistics into training sets, noisy sample averages recommending heroes based on 1 lucky game, and arbitrary hardcoded score weights.

This repository transforms the pipeline into a research-grade, production-ready system:
1. **Zero Data Leakage**: Evaluated on strict chronological splits ($D_{\text{train}} \to D_{\text{val}} \to D_{\text{test}}$). Feature matrices are computed strictly on training data.
2. **Empirical-Bayes Shrinkage ($k=20.0$)**: Low-sample matchups shrink toward baseline prior win rates, eliminating spurious counters.
3. **Learned Stacking Combiner**: Combines matchup advantages, synergy scores, win rate differentials, and LightGBM tree predictions using Logistic Regression fitted on validation data.
4. **Role-Aware Suggestions**: Automatically infers missing team roles (Carry, Mid, Offlane, Support) from existing allies to draft balanced team compositions.
5. **Numeric Valve Hero IDs**: All backend API contracts use official Valve hero IDs, decoupling display names from computation.

---

## 2. Model Performance & Evaluation

> [!IMPORTANT]
> **Honest Metric Reporting**: Draft-only prediction has an inherent theoretical ceiling in high-level Dota 2 (~55–58%). Drafts set initial win conditions, but laning execution, warding, item timing, buyback management, and teamfight execution dictate match outcomes. Previous claims of 70%+ accuracy in earlier iterations were artifacts of data leakage (evaluating on matches already included in matchup matrix calculations).

The table below reports test set performance on **2,237 strictly future matches** with zero data leakage:

| Model / Baseline | Test Accuracy | ROC-AUC | Log-Loss | Brier Score | Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **(a) Radiant Base Rate Prior** | 54.09% | 0.5000 | 0.6922 | 0.2483 | Constant prediction of Radiant win frequency |
| **(b) Hero Win Rate Sum** | 54.81% | 0.5519 | 0.6908 | 0.2481 | Sum of individual hero baseline win rates |
| **(c) Matchup-Only Score** | 52.79% | 0.5484 | 0.6917 | 0.2486 | Pairwise counter scores without nonlinear model |
| **(d) Standalone LightGBM** | 55.48% | 0.5694 | 0.6872 | 0.2468 | Gradient boosted tree on draft hero vectors |
| **(e) Full Learned Combiner** | **55.52%** | **0.5757** | **0.6865** | **0.2467** | **Stacked Logistic Regression combining (b)+(c)+(d) + shrinkage** |

*Full metrics and calibration artifacts: [`ml_pipeline/reports/metrics.json`](ml_pipeline/reports/metrics.json) and [`ml_pipeline/reports/calibration_curve.png`](ml_pipeline/reports/calibration_curve.png).*

### Ablation Study Summary ([`ml_pipeline/reports/ablation.md`](ml_pipeline/reports/ablation.md))
- **Baseline LightGBM**: ROC-AUC 0.5694
- **+ Empirical-Bayes Shrinkage ($k=20.0$)**: Prevents overfitting to rare matchups; stabilizes score distribution.
- **+ Learned Stacking Combiner**: Lifts ROC-AUC to **0.5757** and drops Log-Loss to **0.6865** (the strongest configuration tested).

---

## 3. Repository Structure

```
Dota-drafter/
├── backend/
│   ├── app/
│   │   ├── config.py           # Pydantic BaseSettings (CORS, cache size, ports)
│   │   ├── logger.py           # Structured JSON logging
│   │   ├── schemas.py          # Request/response validation schemas
│   │   ├── model_loader.py     # Versioned model artifact manager & hot reload
│   │   ├── scoring.py          # Shrinkage math, ranking, & role inference
│   │   ├── hero_knowledge.py   # Tactical counter & synergy explanation generation
│   │   ├── cache.py            # Thread-safe LRU response caching
│   │   └── routes/             # Modular routes: /suggest, /heroes, /health
│   ├── model/                  # Versioned model artifacts (v2.2.0/)
│   └── Dockerfile              # Production FastAPI container
├── frontend/                   # React 18 + Vite frontend
│   ├── src/
│   │   ├── Dota2Drafter.jsx    # UI: hero picker, ban dock, role filters, confidence
│   │   └── App.jsx
│   └── Dockerfile              # Nginx production frontend container
├── ml_pipeline/
│   ├── prepare_data.py         # 5v5 validation, clean CSV creation
│   ├── train.py                # Leakage-free training with shrinkage & stacking
│   ├── evaluate.py             # Strict temporal evaluation & baseline benchmarking
│   ├── training_config.json    # Hyperparameters, decay rates, shrinkage priors
│   └── reports/                # metrics.json, ablation.md, calibration_curve.png
├── scripts/                    # Operational automation
│   ├── patch_aware_collector.py# Rate-limited OpenDota match ingest daemon
│   ├── orchestrator.py         # Automated retraining and hot reload coordinator
│   └── lifecycle_manager.py    # Postgres patch metadata state tracking
├── notebooks/
│   └── exploration.ipynb       # Interactive pipeline demonstration notebook
├── tests/
│   ├── fixtures/               # Hermetic 1,500 match offline dataset
│   ├── test_scoring.py         # Unit tests (shrinkage math, recency, bounds)
│   ├── test_leakage.py         # Formal no-leakage temporal split tests
│   └── test_api.py             # API integration, validation & role-aware tests
├── Makefile                    # Unified developer task runner
├── pyproject.toml              # Ruff & Mypy configurations
├── pytest.ini                  # Pytest runner settings
└── docker-compose.yml          # Multi-container local production stack
```

---

## 4. Quickstart Guide

### Option A: Docker Compose (Recommended)
Launch the entire system (FastAPI backend, React frontend, PostgreSQL, Prometheus, Grafana):

```bash
docker compose up --build
```
- Frontend UI: `http://localhost:3000`
- Backend API Docs: `http://localhost:8000/docs`
- Health & Freshness: `http://localhost:8000/health`

### Option B: Local Development
```bash
# 1. Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 2. Run unit & integration test suite (20 tests)
make test

# 3. Start backend locally
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Start frontend
cd frontend && npm run dev
```

---

## 5. Development Makefile Targets

| Target | Description |
| :--- | :--- |
| `make test` | Runs the full 20-test Pytest test suite offline using fixture data |
| `make lint` | Runs Ruff linter across `backend`, `ml_pipeline`, `tests`, `scripts` |
| `make data` | Prepares raw match records into clean 5v5 dataset via `ml_pipeline/prepare_data.py` |
| `make train`| Trains LightGBM model, shrinks matrices, and fits stacking combiner |
| `make eval` | Runs strict time-based evaluation and writes `metrics.json` |
| `make up`   | Starts full stack in Docker Compose |
| `make down` | Gracefully shuts down Docker Compose containers |

---

## 6. API Reference

### `GET /heroes`
Returns the canonical roster of 127 heroes with numeric IDs, attributes, roles, and image assets.
```json
[
  {
    "id": 1,
    "name": "Anti-Mage",
    "attribute": "agi",
    "roles": ["carry", "escape", "nuker"],
    "image_url": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/antimage.png"
  }
]
```

### `POST /suggest`
Recommends optimal counter-picks with confidence, sample size, and tactical explanations.
```json
// Request
{
  "enemy": [14, 47, 35],      // Pudge, Viper, Sniper (or localized names)
  "team": [5],                // Crystal Maiden
  "bans": [74],               // Invoker
  "role_aware": true
}

// Response
{
  "picks": [
    {
      "id": 1,
      "name": "Anti-Mage",
      "score": 0.5842,
      "confidence": "high",
      "sample_size": 182,
      "roles": ["carry"],
      "reasons": [
        "Counters Viper (+3.4% matchup edge over 68 games)",
        "Synergizes with Crystal Maiden (+2.1% win advantage)"
      ],
      "reason_details": [
        {
          "enemy": "Viper",
          "how": "Anti-Mage drains Viper's mana pool, neutering Poison Attack.",
          "tip": "Engage after Viper uses Nethertoxin; burn his mana pool quickly.",
          "sample_size": 68
        }
      ]
    }
  ],
  "roles_needed": ["carry", "offlane"],
  "role_aware": true
}
```

---

## 7. How to Retrain Models

1. **Collect fresh match data**:
   ```bash
   python scripts/patch_aware_collector.py --patch 7.35d --max-calls 100 --target 10000
   ```
2. **Train and version new model**:
   ```bash
   python ml_pipeline/train.py --input_csv data/clean_matches.csv --version v2.3.0
   ```
3. **Hot-reload running backend without downtime**:
   ```bash
   curl -X POST "http://localhost:8000/model/reload?version=v2.3.0"
   ```

---

## 8. License & Valve Notice

- Code released under the [MIT License](LICENSE).
- **Dota 2** and all related assets, hero names, and iconography are registered trademarks of **Valve Corporation**. This project is an independent educational/research analysis tool.
