import requests
import pandas as pd
import time
import os

# --- Configuration ---
TARGET_MATCHES = 500000
BATCH_SIZE = 100  # API limit per call
API_DELAY = 1.0   # OpenDota allows ~60 calls/min. 1.0s is safe.
MIN_MMR = 4500    # Approximate MMR for 'High Rank' (Ancient/Divine+)
FILENAME = 'matches.csv'

def get_hero_map():
    """Fetches Hero ID to Name mapping."""
    try:
        resp = requests.get("https://api.opendota.com/api/heroes")
        return {h['id']: h['localized_name'] for h in resp.json()}
    except:
        return {}

def fetch_public_matches(last_match_id=None):
    """
    Fetches a batch of 100 public matches.
    Uses 'less_than_match_id' to paginate backwards in time.
    """
    url = "https://api.opendota.com/api/publicMatches"
    params = {
        'mmr_ascending': 0, # Try to get higher MMR if API respects it
        'min_rank': 50      # ~Divine/Immortal rank filter (optional)
    }
    if last_match_id:
        params['less_than_match_id'] = last_match_id

    try:
        response = requests.get(url, params=params)
        if response.status_code == 429:
            print("\nRate limit hit. Pausing for 60 seconds...")
            time.sleep(60)
            return fetch_public_matches(last_match_id)
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"\nError: {e}")
        return []

def main():
    hero_map = get_hero_map()
    print(f"Hero map loaded ({len(hero_map)} heroes).")
    
    # Check if file exists to resume or start new
    file_exists = os.path.isfile(FILENAME)
    if file_exists:
        print(f"Resuming from {FILENAME}...")
        # Read the last match_id from the file to resume correctly
        existing_df = pd.read_csv(FILENAME)
        matches_collected = len(existing_df)
        last_id = existing_df['match_id'].min() # We are going backwards, so min is the last one
    else:
        matches_collected = 0
        last_id = None
        # Create CSV with headers
        pd.DataFrame(columns=['match_id', 'radiant_win', 'radiant_team', 'dire_team']).to_csv(FILENAME, index=False)

    print(f"Target: {TARGET_MATCHES} matches. Starting collection...")

    while matches_collected < TARGET_MATCHES:
        batch = fetch_public_matches(last_match_id=last_id)
        
        if not batch:
            print("\nNo more matches returned or API error. Stopping.")
            break

        processed_batch = []
        for match in batch:
            # Filter for high ranked if API didn't perfectly filter
            # (avg_mmr is sometimes missing, so we be lenient)
            if match.get('avg_mmr') and match['avg_mmr'] < MIN_MMR:
                continue

            # Format teams: "Anti-Mage,Zeus,..." (String is better for CSV storage than list)
            # Radiant Team string
            r_team = match['radiant_team'] # This is usually a string "1,2,3..." from this endpoint
            if isinstance(r_team, str):
                r_team_ids = [int(x) for x in r_team.split(',')]
            else:
                r_team_ids = r_team # Already list
            
            d_team = match['dire_team']
            if isinstance(d_team, str):
                d_team_ids = [int(x) for x in d_team.split(',')]
            else:
                d_team_ids = d_team

            # Map IDs to Names
            r_names = [hero_map.get(hid, str(hid)) for hid in r_team_ids]
            d_names = [hero_map.get(hid, str(hid)) for hid in d_team_ids]

            processed_batch.append({
                'match_id': match['match_id'],
                'radiant_win': 1 if match['radiant_win'] else 0,
                'radiant_team': ",".join(r_names),
                'dire_team': ",".join(d_names)
            })

        if processed_batch:
            # Append to CSV immediately
            df_batch = pd.DataFrame(processed_batch)
            df_batch.to_csv(FILENAME, mode='a', header=False, index=False)
            
            matches_collected += len(processed_batch)
            last_id = batch[-1]['match_id'] # Update cursor for next batch
            
            print(f"Collected: {matches_collected}/{TARGET_MATCHES} | Last ID: {last_id}", end='\r')
        
        time.sleep(API_DELAY)

    print(f"\n\nDone! {matches_collected} matches saved to {FILENAME}")

if __name__ == "__main__":
    main()