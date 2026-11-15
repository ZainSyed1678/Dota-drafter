"""
Dota 2 Drafter - Read-Only Parquet Snapshot Export & Filter Pipeline
Exports matches from Neon PostgreSQL to local Parquet snapshots (data/snapshots/)
and logs match quality filtering metrics.
"""

import argparse
import ast
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
import psycopg2
import pyarrow as pa
import pyarrow.parquet as pq
from dotenv import load_dotenv

# Ensure scripts dir in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def clean_team(x):
    """Parse team representation into list of ints."""
    try:
        while isinstance(x, str):
            try:
                x = ast.literal_eval(x)
            except Exception:
                break
        if isinstance(x, str):
            x = x.replace('[', '').replace(']', '')
            x = [int(i.strip()) for i in x.split(',') if i.strip().isdigit()]
        return [int(h) for h in x if int(h) > 0]
    except Exception:
        return []


def export_raw_parquet(db_url: str, output_path: Path, batch_size: int = 100000):
    """Stream raw matches from Neon DB using server-side cursor to Parquet."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Connecting to database (READ-ONLY) to export raw snapshot...")
    conn = psycopg2.connect(db_url)
    conn.set_session(readonly=True)

    cursor_name = "raw_matches_export_cursor"
    writer = None
    total_rows = 0
    t0 = time.time()

    try:
        with conn.cursor(name=cursor_name) as cur:
            cur.itersize = batch_size
            cur.execute("""
                SELECT match_id, radiant_win, radiant_team, dire_team, patch_version
                FROM matches
                ORDER BY match_id ASC;
            """)

            schema = pa.schema([
                ('match_id', pa.int64()),
                ('radiant_win', pa.bool_()),
                ('radiant_team', pa.string()),
                ('dire_team', pa.string()),
                ('patch_version', pa.string()),
            ])

            while True:
                rows = cur.fetchmany(batch_size)
                if not rows:
                    break

                df_batch = pd.DataFrame(rows, columns=['match_id', 'radiant_win', 'radiant_team', 'dire_team', 'patch_version'])
                table = pa.Table.from_pandas(df_batch, schema=schema, preserve_index=False)

                if writer is None:
                    writer = pq.ParquetWriter(output_path, schema, compression='zstd')
                writer.write_table(table)

                total_rows += len(rows)
                print(f"Exported {total_rows:,} rows ({time.time() - t0:.1f}s)...")

    finally:
        if writer is not None:
            writer.close()
        conn.close()

    elapsed = time.time() - t0
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Raw export complete: {total_rows:,} rows written to {output_path} ({file_size_mb:.2f} MB in {elapsed:.1f}s)")
    return total_rows


def apply_quality_filters(raw_path: Path, clean_path: Path, filter_log_path: Path):
    """Apply quality and deduplication filters, logging row counts for each step."""
    print(f"Loading raw snapshot from {raw_path}...")
    df = pd.read_parquet(raw_path)
    initial_count = len(df)
    print(f"Initial raw rows: {initial_count:,}")

    filter_stats = {
        "initial_raw_count": initial_count,
        "filters_applied": {}
    }

    # Filter 1: Deduplicate match_id
    deduped_df = df.drop_duplicates(subset=['match_id'], keep='last')
    dupes_removed = initial_count - len(deduped_df)
    filter_stats["filters_applied"]["deduplicate_match_id"] = {
        "removed": int(dupes_removed),
        "remaining": int(len(deduped_df)),
        "description": "Drop duplicate match IDs, keeping latest occurrence"
    }
    print(f"1. Deduplication: removed {dupes_removed:,} duplicates (remaining: {len(deduped_df):,})")

    # Filter 2: Parse teams and check valid hero lists
    deduped_df['radiant_team_clean'] = deduped_df['radiant_team'].apply(clean_team)
    deduped_df['dire_team_clean'] = deduped_df['dire_team'].apply(clean_team)

    valid_team_size_mask = (
        deduped_df['radiant_team_clean'].apply(lambda t: len(t) == 5 and len(set(t)) == 5) &
        deduped_df['dire_team_clean'].apply(lambda t: len(t) == 5 and len(set(t)) == 5)
    )
    invalid_team_size_count = int((~valid_team_size_mask).sum())
    df_valid_teams = deduped_df[valid_team_size_mask].copy()
    filter_stats["filters_applied"]["valid_5v5_distinct_heroes"] = {
        "removed": invalid_team_size_count,
        "remaining": int(len(df_valid_teams)),
        "description": "Requires exactly 5 distinct non-zero hero IDs per team (filters leavers/incomplete drafts)"
    }
    print(f"2. Valid 5v5 distinct heroes: removed {invalid_team_size_count:,} (remaining: {len(df_valid_teams):,})")

    # Filter 3: Disjoint teams (no hero drafted on both Radiant and Dire)
    disjoint_mask = df_valid_teams.apply(
        lambda r: len(set(r['radiant_team_clean']) & set(r['dire_team_clean'])) == 0, axis=1
    )
    overlap_count = int((~disjoint_mask).sum())
    df_disjoint = df_valid_teams[disjoint_mask].copy()
    filter_stats["filters_applied"]["cross_team_overlap"] = {
        "removed": overlap_count,
        "remaining": int(len(df_disjoint)),
        "description": "Requires 0 overlapping heroes between Radiant and Dire"
    }
    print(f"3. Cross-team overlap: removed {overlap_count:,} (remaining: {len(df_disjoint):,})")

    # Filter 4: Valid patch version and radiant_win not null
    clean_mask = df_disjoint['patch_version'].notna() & df_disjoint['radiant_win'].notna()
    null_count = int((~clean_mask).sum())
    df_clean = df_disjoint[clean_mask].copy()
    filter_stats["filters_applied"]["null_metadata_check"] = {
        "removed": null_count,
        "remaining": int(len(df_clean)),
        "description": "Requires non-null patch version and non-null winner boolean"
    }
    print(f"4. Null checks: removed {null_count:,} (remaining: {len(df_clean):,})")

    # Prepare final clean dataframe
    df_clean['radiant_team'] = df_clean['radiant_team_clean']
    df_clean['dire_team'] = df_clean['dire_team_clean']
    df_clean = df_clean.drop(columns=['radiant_team_clean', 'dire_team_clean'])
    df_clean = df_clean.sort_values('match_id').reset_index(drop=True)

    filter_stats["final_clean_count"] = int(len(df_clean))
    filter_stats["total_rows_removed"] = int(initial_count - len(df_clean))
    filter_stats["retention_rate_pct"] = round(len(df_clean) / initial_count * 100, 2)

    # Patch breakdown
    patch_counts = df_clean['patch_version'].value_counts().to_dict()
    filter_stats["patch_distribution"] = {str(k): int(v) for k, v in patch_counts.items()}

    # Save cleaned Parquet
    clean_path.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_parquet(clean_path, compression='zstd', index=False)
    clean_size_mb = clean_path.stat().st_size / (1024 * 1024)
    print(f"Clean snapshot saved to {clean_path} ({clean_size_mb:.2f} MB, {len(df_clean):,} matches)")

    # Save filter log
    filter_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(filter_log_path, 'w') as f:
        json.dump(filter_stats, f, indent=2)
    print(f"Filter stats saved to {filter_log_path}")

    return filter_stats


def main():
    parser = argparse.ArgumentParser(description="Export Neon DB matches to Parquet snapshot")
    parser.add_argument("--raw-only", action="store_true", help="Export raw parquet only")
    parser.add_argument("--filter-only", action="store_true", help="Apply filters to existing raw parquet only")
    args = parser.parse_args()

    snapshots_dir = PROJECT_ROOT / "data" / "snapshots"
    raw_parquet = snapshots_dir / "matches_raw.parquet"
    clean_parquet = snapshots_dir / "matches_clean.parquet"
    filter_log = PROJECT_ROOT / "reports" / "data_filter_log.json"

    db_url = os.environ.get("DATABASE_URL")
    if not args.filter_only and not db_url:
        print("Error: DATABASE_URL not found in environment.")
        sys.exit(1)

    if not args.filter_only:
        export_raw_parquet(db_url, raw_parquet)

    if not args.raw_only:
        apply_quality_filters(raw_parquet, clean_parquet, filter_log)


if __name__ == "__main__":
    main()
