"""
Dota 2 Drafter - Data Preparation Script
Loads raw match records, validates complete 5v5 drafts without hero duplicates,
orders matches chronologically by match_id, and writes clean versioned CSV.
"""

import argparse
import ast
import os
from pathlib import Path

import pandas as pd


def clean_team(x):
    """Clean team string or list into list of valid integers."""
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


def prepare_dataset(input_csv: str, output_csv: str) -> pd.DataFrame:
    print(f"Loading raw match data from {input_csv}...")
    df = pd.read_csv(input_csv)

    df['radiant_team'] = df['radiant_team'].apply(clean_team)
    df['dire_team'] = df['dire_team'].apply(clean_team)

    # 5v5 validation: exactly 5 distinct heroes per team, no cross-team overlap
    valid_mask = (
        df['radiant_team'].apply(lambda t: len(t) == 5 and len(set(t)) == 5) &
        df['dire_team'].apply(lambda t: len(t) == 5 and len(set(t)) == 5) &
        df.apply(lambda r: len(set(r['radiant_team']) & set(r['dire_team'])) == 0, axis=1)
    )
    clean_df = df[valid_mask].sort_values('match_id').reset_index(drop=True)

    print(f"Raw matches: {len(df)} | Valid 5v5 matches: {len(clean_df)}")

    # Format teams as comma-separated integers for compact storage
    save_df = clean_df.copy()
    save_df['radiant_team'] = save_df['radiant_team'].apply(lambda t: ','.join(map(str, t)))
    save_df['dire_team'] = save_df['dire_team'].apply(lambda t: ','.join(map(str, t)))

    out_path = Path(output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    save_df.to_csv(out_path, index=False)
    print(f"Saved clean dataset to {out_path} ({os.path.getsize(out_path) / 1024:.1f} KB)")
    return clean_df


def main():
    parser = argparse.ArgumentParser(description="Prepare and clean Dota 2 match dataset")
    parser.add_argument("--input", type=str, default="notebooks/matches.csv", help="Input matches CSV")
    parser.add_argument("--output", type=str, default="data/clean_matches.csv", help="Output clean CSV")
    args = parser.parse_args()

    prepare_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
