import os
import subprocess
import sys
import lifecycle_manager

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

def run_training(patch: str, dataset_version: str = "v1") -> bool:
    print(f"Orchestrator telling Grog to train for Patch {patch}, Dataset {dataset_version}...")
    
    cmd = [
        sys.executable, "train_from_psql.py",
        "--patch", patch,
        "--dataset", dataset_version
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Ugh! Training failed for {patch}!")
        print(result.stderr)
        return False
        
    print(f"Training success for {patch}!")
    return True

def main():
    print("Grog Orchestrator waking up!")
    
    # Check for patches ready to train
    ready_patches = lifecycle_manager.get_patches_in_state("DATA_READINESS_CHECK")
    
    if not ready_patches:
        print("No patches ready for training. Grog go back to sleep.")
        return
        
    for patch in ready_patches:
        print(f"\n--- Processing Patch {patch} ---")
        
        # 1. Train
        lifecycle_manager.transition_state(patch, "TRAINING")
        success = run_training(patch)
        
        if not success:
            lifecycle_manager.transition_state(patch, "TRAINING_FAILED")
            continue

if __name__ == "__main__":
    main()
