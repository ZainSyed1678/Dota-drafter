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
