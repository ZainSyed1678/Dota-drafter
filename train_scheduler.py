import os
import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import sys

MODEL_DIR = Path(__file__).parent / "model"
RETRAIN_MARKER = MODEL_DIR / ".last_train"

def needs_retrain(weeks):
    if not RETRAIN_MARKER.exists():
        return True
    
    with open(RETRAIN_MARKER, 'r') as f:
        last_train_str = f.read().strip()
    
    try:
        last_train = datetime.fromisoformat(last_train_str)
        if datetime.now() - last_train > timedelta(weeks=weeks):
            return True
    except:
        return True
        
    return False

def retrain_model():
    print("Grog start retrain model...")
    # The actual training logic would normally go to the notebook or a train script.
    # We will simulate running the jupyter notebook if it exists.
    notebook_path = Path(__file__).parent / "notebooks" / "Untitled.ipynb"
    if notebook_path.exists():
        cmd = [
            sys.executable, "-m", "jupyter", "nbconvert",
            "--to", "script",
            "--execute",
            str(notebook_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("Grog fail to train model.")
            print(result.stderr)
            return False
        
        print("Grog finish train model!")
    else:
        print("Grog no find training notebook, skip real train.")
        
    # Mark retrain time
    with open(RETRAIN_MARKER, 'w') as f:
        f.write(datetime.now().isoformat())
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weeks", type=float, default=2.0, help="Weeks between retrain")
    args = parser.parse_args()
    
    print(f"Grog check if model need retrain (every {args.weeks} weeks)...")
    
    if needs_retrain(args.weeks):
        print("Model old! Grog make new one.")
        retrain_model()
    else:
        print("Model still fresh. Grog no train.")

if __name__ == "__main__":
    main()
