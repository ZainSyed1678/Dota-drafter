import argparse
import datetime
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import psycopg2

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

scripts_dir = Path(__file__).resolve().parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))


def train_from_postgres(patch: str = "7.35f", max_samples: int = 100000, version: str = None) -> bool:
    if not version:
        date_str = datetime.datetime.now().strftime("%Y.%m.%d")
        version = f"v{date_str}"

    print(f"Starting PostgreSQL training extraction for Patch {patch} (Max: {max_samples}, Version: {version})...")

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL environment variable is not set. Cannot pull from PostgreSQL.")
        return False

    try:
        conn = psycopg2.connect(db_url, connect_timeout=15)
    except Exception as e:
        print(f"Could not connect to PostgreSQL: {e}")
        return False

    # Check match counts for patch and total in DB
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM matches WHERE patch_version = %s;", (patch,))
        patch_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM matches;")
        total_matches = cur.fetchone()[0]

    print(f"PostgreSQL match pool: {total_matches} total matches in DB ({patch_count} on active patch '{patch}').")

    query_limit = min(total_matches, max_samples)
    if query_limit == 0:
        print("No matches found in database. Please run collection first.")
        conn.close()
        return False

    print(f"Extracting {query_limit} most recent matches (prioritizing '{patch}', with recency decay on previous patches)...")
    query = f"""
        SELECT match_id, radiant_win, radiant_team, dire_team, patch_version
        FROM (
            SELECT match_id, radiant_win, radiant_team, dire_team, patch_version
            FROM matches
            ORDER BY match_id DESC
            LIMIT {query_limit}
        ) recent_matches
        ORDER BY match_id ASC;
    """
    df = pd.read_sql(query, conn)
    conn.close()

    # Fill any null patch_version with default
    df['patch_version'] = df['patch_version'].fillna(patch)

    print(f"Extracted {len(df)} matches successfully. Patches represented in batch:")
    print(df['patch_version'].value_counts().to_dict())

    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    temp_csv = data_dir / f"matches_{patch}_{version}.csv"
    df.to_csv(temp_csv, index=False)

    print(f"Executing ML pipeline training (version={version})...")
    backend_model_dir = Path("backend") / "model"
    cmd = [
        sys.executable, "ml_pipeline/train.py",
        "--input_csv", str(temp_csv),
        "--output_dir", str(backend_model_dir),
        "--version", version
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")

    if result.returncode != 0:
        print("ML Pipeline training failed!")
        print(result.stderr)
        return False

    print(f"Model training SUCCESS for version {version}!")
    print("\n".join(result.stdout.split("\n")[-10:]))

    # Sync to root model directory for Docker Compose mounts
    root_model_dir = Path("model")
    if root_model_dir.exists():
        version_dir = backend_model_dir / version
        if version_dir.exists():
            shutil.copytree(version_dir, root_model_dir / version, dirs_exist_ok=True)
        for fname in ["model.pkl", "matchup.pkl", "synergy.pkl", "roles.pkl", "hero_winrate.pkl",
                      "hero_avg_matchup.pkl", "combiner_weights.pkl", "matchup_samples.pkl",
                      "synergy_samples.pkl", "metadata.json"]:
            src = backend_model_dir / fname
            if src.exists():
                shutil.copy2(src, root_model_dir / fname)

    # Clean up temporary query CSV to preserve space
    try:
        temp_csv.unlink()
    except Exception:
        pass

    return True


def main():
    parser = argparse.ArgumentParser(description="Train Dota 2 Drafter model from PostgreSQL")
    parser.add_argument("--patch", type=str, default="7.35f", help="Patch version (default: 7.35f)")
    parser.add_argument("--max-samples", type=int, default=100000, help="Max matches to use for training (default: 100000)")
    parser.add_argument("--version", type=str, default=None, help="Version string for model (e.g. v2.3.0)")
    args = parser.parse_args()

    success = train_from_postgres(patch=args.patch, max_samples=args.max_samples, version=args.version)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
