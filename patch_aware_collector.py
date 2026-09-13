import requests
import time
import os
import argparse
import psycopg2
from psycopg2.extras import execute_values
import lifecycle_manager

BATCH_SIZE = 100
API_DELAY = 1.0

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
        response = requests.get(url, params=params)
        if response.status_code == 429:
            print("Rate limit. Sleep 60s...")
            time.sleep(60)
            return fetch_public_matches(last_match_id)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching matches: {e}")
        return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--patch", type=str, required=True, help="Current Dota 2 Patch (e.g., 7.35d)")
    parser.add_argument("--target", type=int, default=100, help="Number of valid matches to collect")
    args = parser.parse_args()

    print(f"Starting collector for patch {args.patch}...")
    lifecycle_manager.init_lifecycle_db()
    
    db_url = os.environ.get("DATABASE_URL", "postgresql://dotauser:dotapassword@localhost:5432/dotadb")
    conn = psycopg2.connect(db_url)
    init_tables(conn)

    lifecycle_manager.detect_patch(args.patch)
    lifecycle_manager.transition_state(args.patch, "COLLECTION_ACTIVE")

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO collection_runs (patch_version, status) 
            VALUES (%s, %s) RETURNING id
        """, (args.patch, "RUNNING"))
        run_id = cur.fetchone()[0]
    conn.commit()
    print(f"Collection run {run_id} started for patch {args.patch}")
    conn.close()

if __name__ == "__main__":
    main()
