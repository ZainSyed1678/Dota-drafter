<div align="center">

<img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/global/dota2_logo_symbol.png" width="80" alt="Dota 2 Logo"/>

# Dota 2 Drafter

**A machine-learning powered counter-pick tool for Dota 2**

Pick your enemy heroes → get the 9 strongest counters ranked by real match data

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![LightGBM](https://img.shields.io/badge/LightGBM-4.3-orange?style=flat-square)](https://lightgbm.readthedocs.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docs.docker.com/compose)

</div>

---

## Overview

Dota 2 Drafter analyses **250,000+ real matches** to suggest the best counter-picks for any enemy lineup. Unlike simple win-rate tables, it uses a **normalised matchup scoring system** that removes global hero strength bias — so a hero that wins 54% everywhere doesn't look like it counters everyone.

Select up to 5 enemy heroes, optionally add your own team, hit **Suggest Picks** and get the top 9 counter-picks with explanations showing exactly why each hero is recommended against this specific lineup.

---

## Features

- **Top 9 counter-picks** ranked globally by counter-pick score — no empty role buckets
- **Normalised matchup scoring** — removes bias from globally strong heroes
- **Synergy-aware** — accounts for how suggested heroes work with your existing allies
- **Recency-weighted model** — recent matches count more so suggestions reflect the current meta
- **Per-enemy explanations** — each card shows which specific enemies it counters and by how much
- **Role badges** — carry / mid / offlane / support shown on every suggestion card
- **Hero search** — filter the full roster instantly
- **Attribute grouping** — heroes organised by Agility / Strength / Intelligence / Universal
- **Dota 2 aesthetic** — dark UI with Steam CDN hero portraits

---

## Demo

<div align="center">

| Select Enemy Heroes | Get Counter Picks |
|---|---|
| Click heroes to add them to the enemy team | Hit Suggest Picks for ranked recommendations |

</div>

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Model** | LightGBM | Win prediction from hero features |
| **Data** | 250k matches via OpenDota API | Training data |
| **Backend** | FastAPI + Python 3.11 | REST API serving suggestions |
| **Frontend** | React 18 + Vite | Hero picker UI |
| **Serving** | Nginx | Static files + API proxy |
| **Deployment** | Docker Compose | Single-command startup |

---

## Project Structure

```
drafter/
├── docker-compose.yml          # Start everything with one command
│
├── backend/                    # FastAPI API server
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py                 # /suggest endpoint + scoring logic
│
├── frontend/                   # React application
│   ├── Dockerfile              # Multi-stage: Vite build → Nginx
│   ├── nginx.conf              # SPA routing + /api proxy
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       └── Dota2Drafter.jsx    # Main component
│
├── notebooks/                  # Model training
│   └── Untitled.ipynb          # Run this to generate pkl files
│
├── model/                      # Generated pkl files (not in git)
│   ├── hero_map.pkl
│   ├── matchup.pkl
│   ├── synergy.pkl
│   ├── roles.pkl
│   ├── hero_avg_matchup.pkl
│   └── hero_winrate.pkl
│
├── core/                       # Shared utilities
├── fetch/                      # OpenDota data fetching scripts
├── data/                       # Raw match CSVs
├── .gitignore
├── requirements.txt            # Python deps for notebook environment
└── README.md
```

---

## How It Works

### 1. Data Pipeline
Match data is fetched from the **OpenDota API** and stored as CSVs. Each match records which heroes were on each team and who won.

### 2. Matchup Matrix
For every hero pair `(A vs B)`, we compute the **weighted win rate** of A when facing B. Weights are higher for recent matches so the matrix reflects the current patch.

### 3. Normalisation (key insight)
Raw matchup win rates are biased — a hero like Silencer that wins 54% everywhere looks like it "counters" every hero. We fix this by computing each hero's **global average matchup win rate** and subtracting it:

```
adjusted_advantage = matchup_wr(hero vs enemy) - hero_avg_matchup_wr
```

This means a hero only scores positively for a specific enemy if it wins *more than its baseline* against that enemy.

### 4. Scoring Formula
```
score = 1.50 × normalised_matchup
      + 0.35 × synergy_with_allies
      + 0.06 × meta_winrate_bonus
```

Matchup weight is highest because this is a **counter-pick tool** — the primary purpose is finding heroes that beat the specific enemy lineup.

### 5. LightGBM Model
A gradient boosted model is trained on hero presence vectors + matchup/synergy features to predict match outcomes. The model's win probability contributes an additional signal but the normalised matchup score dominates.

### 6. Output
Top 9 heroes by score are returned with per-enemy counter reasons, synergy notes, and role information.

---

## Getting Started

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Python 3.11+ (for running the training notebook)
- The match dataset CSV (not included in this repo — see Data section)

---

### Option A — Docker Compose (recommended)

**Step 1: Clone the repo**
```bash
git clone https://github.com/ZainSyed1678/Dota-drafter.git
cd Dota-drafter
```

**Step 2: Train the model**

Place your `matches.csv` in the project root, then run the notebook:
```bash
pip install -r requirements.txt
jupyter notebook notebooks/Untitled.ipynb
# Run all cells → generates pkl files in model/
```

**Step 3: Start everything**
```bash
docker compose up --build
```

Open **http://localhost:3000** in your browser.

That's it. The backend runs on port 8000 and the frontend on port 3000.

---

### Option B — Run locally without Docker

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## After Retraining the Model

The `model/` directory is mounted as a volume into the backend container. When you retrain (run the notebook again), you don't need to rebuild — just restart the backend:

```bash
# 1. Run notebook to generate new pkl files in model/
# 2. Restart backend to load them
docker compose restart backend
```

---

## API Reference

The backend exposes three endpoints:

### `GET /health`
Returns whether the model is loaded and ready.
```json
{ "status": "ok", "heroes": 121 }
```

### `GET /debug`
Returns a sample of hero names from `hero_map.pkl`. Use this to verify that hero names in the frontend match the pkl exactly.
```json
{
  "hero_map_sample": { "1": "Anti-Mage", "2": "Axe", ... },
  "total_heroes": 121,
  "total_matchup_pairs": 14641
}
```

### `POST /suggest`
Returns top 9 counter-pick recommendations.

**Request:**
```json
{
  "enemy": ["Juggernaut", "Axe", "Crystal Maiden"],
  "team": ["Lina"]
}
```

**Response:**
```json
{
  "picks": [
    {
      "id": 77,
      "name": "Outworld Destroyer",
      "score": 0.0842,
      "reasons": [
        "Counters Juggernaut (+0.071 WR)",
        "Counters Crystal Maiden (+0.038 WR)",
        "Meta strong (53.1% WR)"
      ],
      "roles": ["mid"]
    },
    ...
  ]
}
```

---

## Model Performance

| Metric | Value |
|---|---|
| Dataset size | ~250,000 matches |
| Features | Hero presence (one-hot) + matchup + synergy + winrate |
| Model | LightGBM (1200 estimators, 127 leaves) |
| Test accuracy | ~69–72% |
| Training time | ~3–5 minutes |

> Note: Win prediction accuracy in Dota 2 is fundamentally limited — individual skill, communication, and in-game decisions account for a large portion of outcomes. The model's purpose is to surface statistically meaningful counter-pick patterns, not to predict individual match outcomes.

---

## Data

Match data is sourced from the **OpenDota API**. The training pipeline:

1. Fetches match records with hero picks and outcomes
2. Filters: 5v5 complete teams, matches ≥ 20 minutes, average MMR ≥ 3000 (Legend+)
3. Applies recency weights: last 30 days = 3.5×, last 90 days = 2×, older = 1×
4. Builds matchup and synergy matrices from the filtered dataset

The raw CSV is not included in this repository due to size. You can fetch your own data using the scripts in `fetch/`.

---

## Docker Commands Reference

```bash
# First time or after code changes
docker compose up --build

# Normal startup (< 5 seconds)
docker compose up

# Stop everything
docker compose down

# After retraining (no rebuild needed)
docker compose restart backend

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Check container status
docker compose ps

# Rebuild only one service
docker compose up --build backend
docker compose up --build frontend
```

---

## Troubleshooting

**Suggestions panel is empty / "No counter picks found"**
Visit `http://localhost:8000/debug` to see the exact hero names in your pkl. The names in `Dota2Drafter.jsx` must match exactly (including capitalisation and apostrophes like `Nature's Prophet`).

**"Model not loaded yet" error**
The pkl files are missing from `model/`. Run the notebook to generate them, then `docker compose restart backend`.

**Frontend shows blank page**
Run `docker compose logs frontend` to see the nginx/build error. Make sure `npm run build` works locally first.

**Port already in use**
Change the ports in `docker-compose.yml`:
```yaml
ports:
  - "3001:80"   # frontend on 3001 instead of 3000
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'feat: add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

This project is for educational purposes. Dota 2 and all related assets are property of Valve Corporation. Hero images are fetched directly from Steam CDN and are not redistributed in this repository.

---

<div align="center">

Built with match data from [OpenDota](https://www.opendota.com/) · Hero images from [Steam CDN](https://cdn.cloudflare.steamstatic.com)

</div>