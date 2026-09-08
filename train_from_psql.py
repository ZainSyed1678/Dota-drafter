import os
import psycopg2
import pandas as pd
import subprocess
import sys
from pathlib import Path

def main():
    print("Grog start train process!")
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Ugh! No DATABASE_URL!")
        return
        
    print("Grog download matches from PSQL...")
    conn = psycopg2.connect(db_url)
    df = pd.read_sql("SELECT * FROM matches", conn)
    conn.close()
    
    if len(df) < 500:
        print(f"Ugh! Only {len(df)} matches. Not enough for rock to learn. Need at least 500 (Notebook filter).")
        return
        
    # Notebook expects matches.csv in the same directory it runs
    csv_path = Path("notebooks") / "matches.csv"
    df.to_csv(csv_path, index=False)
    print(f"Grog save {len(df)} matches to {csv_path}")
    print(f"Grog save {len(df)} matches to {csv_path}")
    
    notebook_path = Path("notebooks") / "second.ipynb"
    print("Grog run notebook to train model...")
    cmd = [
        sys.executable, "-m", "jupyter", "nbconvert",
        "--to", "script",
        "--execute",
        str(notebook_path),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Ugh! Train failed!")
        print(result.stderr)
    else:
        print("Train SUCCESS! Rock learned!")
        # Print the last 20 lines of stdout to see accuracy/logloss
        print("\n".join(result.stdout.split("\n")[-20:]))
        
if __name__ == "__main__":
    main()
