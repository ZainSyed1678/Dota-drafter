import os
import sys
import lifecycle_manager

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

def main():
    print("Grog Orchestrator waking up!")
    
    # Check for patches ready to train
    ready_patches = lifecycle_manager.get_patches_in_state("DATA_READINESS_CHECK")
    
    if not ready_patches:
        print("No patches ready for training. Grog go back to sleep.")
        return
        
    for patch in ready_patches:
        print(f"\n--- Processing Patch {patch} ---")

if __name__ == "__main__":
    main()
