# Dota 2 Match Data Management

This directory holds match data for training and evaluating the counter-pick ML models. Large raw match files are excluded from git tracking via `.gitignore`. For offline testing and CI workflows, a small verified fixture is stored under `tests/fixtures/matches_fixture.csv`.

---

## 1. Collecting Live Matches from OpenDota

We fetch high-skill public matches via the OpenDota API (`/api/publicMatches`) using our rate-limited collection scripts.

### Requirements & Configuration
Set your PostgreSQL database connection string in `.env` (or provide via environment variable):
```env
DATABASE_URL=postgresql://dotauser:dotapassword@localhost:5432/dotadb
```

### Running the Patch-Aware Collector
To collect 5,000 matches for patch `7.35d` with rate limiting:
```bash
python scripts/patch_aware_collector.py --patch 7.35d --max-calls 100 --target 5000
```
Key features:
- **Rate-limit protection**: 1.2-second sleep per API call (~50 requests/min, safely below OpenDota's 60 req/min threshold).
- **Quality filter**: Only matches with MMR > 4500 (Divine / Immortal rank bracket).
- **Validation**: Enforces complete 5v5 team drafts, rejecting incomplete or abandoned games.
- **Prometheus instrumentation**: Tracks `dota_matches_collected_total`, `dota_api_requests_total`, and `dota_api_errors_total`.

---

## 2. Preparing and Cleaning Raw Datasets

Once raw matches are collected (or exported from Postgres), run `ml_pipeline/prepare_data.py` to produce a cleaned dataset:

```bash
python ml_pipeline/prepare_data.py --input data/raw_matches.csv --output data/clean_matches.csv
```

The cleaning step performs:
1. Parsing team hero IDs from string or JSON arrays.
2. Filtering out games that do not have exactly 5 Radiant heroes and 5 Dire heroes.
3. Filtering out duplicates within each team and cross-team duplicates.
4. Chronological sorting by `match_id` ascending to prepare for time-based train/val/test splits without temporal leakage.

---

## 3. Offline Testing & CI Fixtures

For local test runs without external API dependencies or database setups:
- `tests/fixtures/matches_fixture.csv`: Contains 1,500 real Valve match records (84.5 KB) spanning complete 5v5 team compositions.
- Used automatically by `pytest tests/` and GitHub Actions CI.
