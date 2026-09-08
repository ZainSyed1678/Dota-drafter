import requests
import time
import os
import argparse
import psycopg2
from psycopg2.extras import execute_values
from prometheus_client import start_http_server, Counter

BATCH_SIZE = 100
API_DELAY = 1.0
MIN_MMR = 4500

# Prometheus Metrics
MATCHES_COLLECTED = Counter('dota_matches_collected_total', 'Total matches collected')
API_REQUESTS = Counter('dota_api_requests_total', 'Total API requests made')
API_ERRORS = Counter('dota_api_errors_total', 'Total API errors encountered')
RATE_LIMITS = Counter('dota_rate_limits_total', 'Total rate limits hit')

def get_hero_map():
    try:
        API_REQUESTS.inc()
        resp = requests.get("https://api.opendota.com/api/heroes")
        return {h['id']: h['localized_name'] for h in resp.json()}
    except Exception as e:
        API_ERRORS.inc()
        return {}

def init_db(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                match_id BIGINT PRIMARY KEY,
                radiant_win BOOLEAN,
                radiant_team TEXT,
                dire_team TEXT
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
        print(f"Error: {e}")
        return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=5000)
    parser.add_argument("--metrics-port", type=int, default=8001)
    args = parser.parse_args()

    # Start Prometheus metrics server
    print(f"Grog start metrics server on port {args.metrics_port}...")
    start_http_server(args.metrics_port)

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Ugh! No DATABASE_URL! Cannot talk to PSQL.")
        # We loop here so Prometheus stays up even if it fails, allowing monitoring of failure?
        # Better to exit if no DB, but this is a script.
        return

    conn = psycopg2.connect(db_url)
    init_db(conn)

    hero_map = get_hero_map()
    print("Grog load hero map.")

    matches_collected = 0
    last_id = None

    while matches_collected < args.target:
        batch = fetch_public_matches(last_match_id=last_id)
        if not batch:
            break

        processed_batch = []
        for match in batch:
            if match.get('avg_mmr') and match['avg_mmr'] < MIN_MMR:
                continue

            r_team = match['radiant_team']
            r_team_ids = [int(x) for x in r_team.split(',')] if isinstance(r_team, str) else r_team
            d_team = match['dire_team']
            d_team_ids = [int(x) for x in d_team.split(',')] if isinstance(d_team, str) else d_team

            processed_batch.append((
                match['match_id'],
                bool(match['radiant_win']),
                ",".join(map(str, r_team_ids)),
                ",".join(map(str, d_team_ids))
            ))

        if processed_batch:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    "INSERT INTO matches (match_id, radiant_win, radiant_team, dire_team) VALUES %s ON CONFLICT (match_id) DO NOTHING",
                    processed_batch
                )
            conn.commit()

            MATCHES_COLLECTED.inc(len(processed_batch))
            matches_collected += len(processed_batch)
            last_id = batch[-1]['match_id']
            print(f"Grog save {matches_collected}/{args.target} | Last ID: {last_id}", end='\r')

        time.sleep(API_DELAY)

    print(f"\nDone! Grog save matches to PSQL.")
    # Keep alive for Prometheus scraping if needed
    print("Grog sleep for 60 seconds so Prometheus can scrape final stats...")
    time.sleep(60)
    conn.close()

if __name__ == "__main__":
    main()
