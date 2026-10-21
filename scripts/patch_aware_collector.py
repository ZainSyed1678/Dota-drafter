import argparse
import os
import sys
import time
from pathlib import Path

import psycopg2
import requests
from prometheus_client import Counter, start_http_server
from psycopg2.extras import execute_values

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

scripts_dir = Path(__file__).resolve().parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))
import lifecycle_manager

BATCH_SIZE = 100
API_DELAY = 1.1  # 1.1s delay ensures ~54 req/min, safely below OpenDota 60 req/min limit
MIN_MMR = 4500

# Prometheus Metrics
MATCHES_COLLECTED = Counter('dota_matches_collected_total', 'Total matches collected', ['patch'])
API_REQUESTS = Counter('dota_api_requests_total', 'Total API requests made')
API_ERRORS = Counter('dota_api_errors_total', 'Total API errors encountered')
RATE_LIMITS = Counter('dota_rate_limits_total', 'Total rate limits hit')
VALIDATION_FAILURES = Counter('dota_validation_failures_total', 'Total matches rejected due to bad data')


def init_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            ALTER TABLE matches ADD COLUMN IF NOT EXISTS patch_version VARCHAR(50);
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS collection_runs (
                id SERIAL PRIMARY KEY,
                patch_version VARCHAR(50) REFERENCES patches(patch_version),
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                matches_fetched INT DEFAULT 0,
                matches_inserted INT DEFAULT 0,
                status VARCHAR(50)
            );
        """)
    conn.commit()


def resolve_current_patch(patch_arg: str = "7.35f") -> str:
    """Resolve patch version, auto-detecting latest from OpenDota constants if requested."""
    if patch_arg and patch_arg.lower() != "auto":
        return patch_arg

    try:
        resp = requests.get("https://api.opendota.com/api/constants/patch", timeout=6)
        if resp.status_code == 200:
            patches = resp.json()
            if patches:
                latest = patches[-1].get("name")
                if latest:
                    print(f"Auto-detected latest Dota 2 patch from OpenDota: {latest}")
                    return latest
    except Exception as e:
        print(f"Could not auto-detect patch ({e}), defaulting to 7.35f")

    return "7.35f"


def fetch_public_matches(last_match_id=None, api_key=None, retry_count=0):
    """
    Fetch public matches from OpenDota.
    Returns:
        list of matches,
        or None if API quota is exhausted (HTTP 429 after retries).
    """
    url = "https://api.opendota.com/api/publicMatches"
    params = {'mmr_ascending': 0, 'min_rank': 50}
    if last_match_id:
        params['less_than_match_id'] = last_match_id
    if api_key:
        params['api_key'] = api_key

    try:
        API_REQUESTS.inc()
        response = requests.get(url, params=params, timeout=12)
        if response.status_code == 429:
            RATE_LIMITS.inc()
            if retry_count < 2:
                print("Rate limit encountered. Waiting 30s before retry...")
                time.sleep(30)
                return fetch_public_matches(last_match_id, api_key=api_key, retry_count=retry_count + 1)
            else:
                print("OpenDota API daily/monthly quota exhausted (HTTP 429).")
                return None  # Signal quota exhaustion
        response.raise_for_status()
        return response.json()
    except Exception as e:
        API_ERRORS.inc()
        print(f"Error fetching matches: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description="Patch-Aware Match Collector for Dota 2")
    parser.add_argument("--patch", type=str, default="7.35f", help="Current Dota 2 Patch (default: 7.35f, or 'auto')")
    parser.add_argument("--target", type=int, default=50000, help="Number of valid matches to collect")
    parser.add_argument("--max-calls", type=int, default=1500, help="Maximum API calls per collection run")
    parser.add_argument("--exhaust-api", action="store_true", help="Continue collecting until daily API quota is exhausted")
    parser.add_argument("--metrics-port", type=int, default=8002)
    args = parser.parse_args()

    patch = resolve_current_patch(args.patch)
    api_key = os.environ.get("OPENDOTA_API_KEY")

    print(f"Starting collector for patch {patch} (target={args.target}, max_calls={args.max_calls}, exhaust={args.exhaust_api})...")
    try:
        start_http_server(args.metrics_port)
    except Exception as e:
        print(f"Could not start metrics on {args.metrics_port} ({e})")

    lifecycle_manager.init_lifecycle_db()

    db_url = os.environ.get("DATABASE_URL", "postgresql://dotauser:dotapassword@localhost:5432/dotadb")
    conn = psycopg2.connect(db_url, connect_timeout=15)
    init_tables(conn)

    # 1. Patch Association & Lifecycle Update
    lifecycle_manager.detect_patch(patch)
    lifecycle_manager.transition_state(patch, "COLLECTION_ACTIVE")

    # 2. Collection Run tracking
    run_id = None
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO collection_runs (patch_version, status)
            VALUES (%s, %s) RETURNING id
        """, (patch, "RUNNING"))
        run_id = cur.fetchone()[0]
    conn.commit()

    matches_collected = 0
    total_fetched = 0
    calls_made = 0
    last_id = None
    api_exhausted = False
    consecutive_empty = 0

    try:
        while calls_made < args.max_calls:
            if not args.exhaust_api and matches_collected >= args.target:
                print(f"Target match count ({args.target}) reached.")
                break

            calls_made += 1
            batch = fetch_public_matches(last_match_id=last_id, api_key=api_key)

            if batch is None:
                # Quota exhausted
                api_exhausted = True
                print("OpenDota daily/monthly API quota reached. Concluding collection cleanly.")
                break

            if not batch:
                consecutive_empty += 1
                if consecutive_empty >= 5:
                    print("Received 5 consecutive empty batches from OpenDota. Ending collection run.")
                    break
                print("Empty batch returned, pausing 5s...")
                time.sleep(5)
                continue

            consecutive_empty = 0
            total_fetched += len(batch)
            processed_batch = []

            for match in batch:
                if match.get('avg_mmr') and match['avg_mmr'] < MIN_MMR:
                    continue

                r_team = match['radiant_team']
                d_team = match['dire_team']

                # Must be 5v5
                r_team_ids = [int(x) for x in r_team.split(',')] if isinstance(r_team, str) else r_team
                d_team_ids = [int(x) for x in d_team.split(',')] if isinstance(d_team, str) else d_team

                if len(r_team_ids) != 5 or len(d_team_ids) != 5:
                    VALIDATION_FAILURES.inc()
                    continue

                processed_batch.append((
                    match['match_id'],
                    bool(match['radiant_win']),
                    ",".join(map(str, r_team_ids)),
                    ",".join(map(str, d_team_ids)),
                    patch
                ))

            if processed_batch:
                with conn.cursor() as cur:
                    execute_values(
                        cur,
                        "INSERT INTO matches (match_id, radiant_win, radiant_team, dire_team, patch_version) VALUES %s ON CONFLICT (match_id) DO NOTHING",
                        processed_batch
                    )
                    inserted_now = cur.rowcount

                conn.commit()

                MATCHES_COLLECTED.labels(patch=patch).inc(inserted_now)
                matches_collected += inserted_now

                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE collection_runs
                        SET matches_fetched = %s, matches_inserted = %s
                        WHERE id = %s
                    """, (total_fetched, matches_collected, run_id))
                conn.commit()

            last_id = batch[-1]['match_id']
            if calls_made % 10 == 0 or calls_made == 1:
                print(f"Call {calls_made}/{args.max_calls} | Saved {matches_collected} new matches for patch {patch} | Total fetched: {total_fetched} | Last ID: {last_id}")

            time.sleep(API_DELAY)

        # Finalize run status
        final_status = "EXHAUSTED" if api_exhausted else "SUCCESS"
        with conn.cursor() as cur:
            cur.execute("UPDATE collection_runs SET status = %s, end_time = CURRENT_TIMESTAMP WHERE id = %s", (final_status, run_id))
        conn.commit()

        print(f"Collection complete ({final_status})! Fetched {total_fetched} raw matches across {calls_made} calls. Inserted {matches_collected} new matches for patch {patch}.")

        # 4. Lifecycle state update
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM matches WHERE patch_version = %s", (patch,))
            total_patch_matches = cur.fetchone()[0]

        is_ready = total_patch_matches >= 1000
        lifecycle_manager.register_dataset(patch, "v1", total_patch_matches, is_ready=is_ready)
        if is_ready:
            lifecycle_manager.transition_state(patch, "DATA_READINESS_CHECK")

    except Exception as e:
        print(f"CRITICAL ERROR during collection: {e}")
        with conn.cursor() as cur:
            cur.execute("UPDATE collection_runs SET status = 'FAILED', end_time = CURRENT_TIMESTAMP WHERE id = %s", (run_id,))
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
