import os
import psycopg2
import pandas as pd
import subprocess
import sys
import argparse
from pathlib import Path
import lifecycle_manager

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--patch", type=str, required=True, help="Patch version (e.g. 7.35d)")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset version (e.g. v1)")
    parser.add_argument("--feature", type=str, default="v1", help="Feature version (e.g. v1)")
    args = parser.parse_args()

    print(f"Grog start train process for Patch {args.patch}, Dataset {args.dataset}, Feature {args.feature}!")
    
    db_url = os.environ.get("DATABASE_URL", "postgresql://dotauser:dotapassword@localhost:5432/dotadb")
    
    # Init lifecycle just in case
    lifecycle_manager.init_lifecycle_db()

    # Verify dataset exists and get boundary
    ds_info = lifecycle_manager.get_dataset_info(args.patch, args.dataset)
    if not ds_info:
        print(f"Ugh! Grog cannot find dataset {args.dataset} for patch {args.patch}!")
        return

    if not ds_info['is_ready']:
        print(f"Ugh! Dataset {args.dataset} is NOT ready!")
        return

    limit = ds_info['match_count']
    ds_id = ds_info['id']

    # Register feature version
    lifecycle_manager.register_feature(ds_id, args.feature)
        
    print(f"Grog downloading exactly {limit} matches from PSQL for boundary...")
    conn = psycopg2.connect(db_url)
    
    # Reproducible query!
    query = f"""
        SELECT * FROM matches 
        WHERE patch_version = '{args.patch}' 
        ORDER BY match_id ASC 
        LIMIT {limit}
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    if len(df) < limit:
        print(f"Warning: Only found {len(df)} matches, but expected {limit}!")
        
    # Notebook expects matches.csv in the same directory it runs
    # To keep notebook working without rewrite, we still save it as matches.csv
    # But we can ALSO save a backup copy with the versioned name for tracking.
    csv_dir = Path("notebooks")
    versioned_csv = csv_dir / f"matches_{args.patch}_{args.dataset}.csv"
    active_csv = csv_dir / "matches.csv"
    
    df.to_csv(versioned_csv, index=False)
    
    # Overwrite the active one for the notebook
    import shutil
    shutil.copy(versioned_csv, active_csv)
    
    print(f"Grog save reproducible dataset to {versioned_csv} and symlinked to {active_csv}")
    
    # Call production pipeline script
    print("Grog run production Python script to train model...")
    cmd = [
        sys.executable, "ml_pipeline/train.py",
        "--input_csv", str(versioned_csv)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
    
    if result.returncode != 0:
        print("Ugh! Train failed!")
        print(result.stderr)
    else:
        print(f"Train SUCCESS! Rock learned on {args.patch} {args.dataset}!")
        print("Model output:")
        print("\n".join(result.stdout.split("\n")[-10:]))
        
if __name__ == "__main__":
    main()
