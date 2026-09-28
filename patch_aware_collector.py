import requests
import time
import os
import argparse
import psycopg2
from psycopg2.extras import execute_values
from prometheus_client import start_http_server, Counter
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import lifecycle_manager

BATCH_SIZE = 100
API_DELAY = 1.0
MIN_MMR = 4500

# Prometheus Metrics
MATCHES_COLLECTED = Counter('dota_matches_collected_total', 'Total matches collected', ['patch'])
API_REQUESTS = Counter('dota_api_requests_total', 'Total API requests made')
API_ERRORS = Counter('dota_api_errors_total', 'Total API errors encountered')
RATE_LIMITS = Counter('dota_rate_limits_total', 'Total rate limits hit')
VALIDATION_FAILURES = Counter('dota_validation_failures_total', 'Total matches rejected due to bad data')

def init_tables(conn):
    with conn.cursor() as cur:
        # Add patch_version to existing matches table
        cur.execute("""
            ALTER TABLE matches ADD COLUMN IF NOT EXISTS patch_version VARCHAR(50);
        """)
        # Create collection_runs table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS collection_runs (
                id SERIAL PRIMARY KEY,
                patch_version VARCHAR(50) REFERENCES patches(patch_version),
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                matches_fetched INT DEFAULT 0,
                matches_inserted INT DEFAULT 0,
                status VARCHAR(50)
            )
        """)
    conn.commit()

def fetch_public_matches(last_match_id=None):
    url = "https://api.opendota.com/api/publicMatches"
    params = {'mmr_ascending': 0, 'min_rank': 50}
    if last_match_id:
        params['less_than_match_id'] = last_match_id

    try:
        API_REQUESTS.inc()
        response = requests.get(url, params=params)
        if response.status_code == 429:
            RATE_LIMITS.inc()
            print("Rate limit. Sleep 60s...")
            time.sleep(60)
            return fetch_public_matches(last_match_id)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        API_ERRORS.inc()
        print(f"Error fetching matches: {e}")
        return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--patch", type=str, required=True, help="Current Dota 2 Patch (e.g., 7.35d)")
    parser.add_argument("--target", type=int, default=100, help="Number of valid matches to collect")
    parser.add_argument("--metrics-port", type=int, default=8002)
    args = parser.parse_args()

    print(f"Grog start smarter collector for patch {args.patch}...")
    try:
        start_http_server(args.metrics_port)
    except Exception as e:
        print(f"Could not start metrics on {args.metrics_port}, maybe already running? {e}")

    # Ensure DB is set up for lifecycle and collector
    lifecycle_manager.init_lifecycle_db()
    
    db_url = os.environ.get("DATABASE_URL", "postgresql://dotauser:dotapassword@localhost:5432/dotadb")
    conn = psycopg2.connect(db_url)
    init_tables(conn)

    # 1. Patch Association & Lifecycle Update
    lifecycle_manager.detect_patch(args.patch)
    lifecycle_manager.transition_state(args.patch, "COLLECTION_ACTIVE")

    # 2. Collection Run tracking
    run_id = None
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO collection_runs (patch_version, status) 
            VALUES (%s, %s) RETURNING id
        """, (args.patch, "RUNNING"))
        run_id = cur.fetchone()[0]
    conn.commit()

    matches_collected = 0
    total_fetched = 0
    last_id = None

    try:
        while matches_collected < args.target:
            batch = fetch_public_matches(last_match_id=last_id)
            if not batch:
                print("No matches returned, waiting...")
                time.sleep(10)
                continue

            total_fetched += len(batch)
            processed_batch = []

            for match in batch:
                # 3. Validation
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
                    args.patch
                ))

            if processed_batch:
                with conn.cursor() as cur:
                    execute_values(
                        cur,
                        "INSERT INTO matches (match_id, radiant_win, radiant_team, dire_team, patch_version) VALUES %s ON CONFLICT (match_id) DO NOTHING",
                        processed_batch
                    )
                conn.commit()

                added = len(processed_batch)
                MATCHES_COLLECTED.labels(patch=args.patch).inc(added)
                matches_collected += added
                
                # Update run stats
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE collection_runs 
                        SET matches_fetched = %s, matches_inserted = %s 
                        WHERE id = %s
                    """, (total_fetched, matches_collected, run_id))
                conn.commit()

            last_id = batch[-1]['match_id']
            print(f"Grog save {matches_collected}/{args.target} for patch {args.patch} | Last ID: {last_id}")
            time.sleep(API_DELAY)

        # Success!
        with conn.cursor() as cur:
            cur.execute("UPDATE collection_runs SET status = 'SUCCESS', end_time = CURRENT_TIMESTAMP WHERE id = %s", (run_id,))
        conn.commit()

        # 4. Readiness Metrics & State Transition
        print(f"Target reached for {args.patch}! Transitioning to DATA_READINESS_CHECK.")
        lifecycle_manager.transition_state(args.patch, "DATA_READINESS_CHECK")
        
        # Check total matches for this patch
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM matches WHERE patch_version = %s", (args.patch,))
            total_patch_matches = cur.fetchone()[0]
        
        is_ready = total_patch_matches >= args.target
        lifecycle_manager.register_dataset(args.patch, "v1", total_patch_matches, is_ready=is_ready)
        
    except Exception as e:
        # 5. Failure Tracking
        print(f"CRITICAL ERROR: {e}")
        with conn.cursor() as cur:
            cur.execute("UPDATE collection_runs SET status = 'FAILED', end_time = CURRENT_TIMESTAMP WHERE id = %s", (run_id,))
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
