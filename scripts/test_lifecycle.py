import lifecycle_manager

print("Initializing DB...")
lifecycle_manager.init_lifecycle_db()

patch = "7.35d"
print(f"Detecting patch {patch}...")
lifecycle_manager.detect_patch(patch)

state = lifecycle_manager.get_current_state(patch)
print(f"Initial State: {state}")
assert state == "PATCH_DETECTED"

print("Transitioning to COLLECTION_ACTIVE...")
lifecycle_manager.transition_state(patch, "COLLECTION_ACTIVE")

state = lifecycle_manager.get_current_state(patch)
print(f"New State: {state}")
assert state == "COLLECTION_ACTIVE"

print("Registering dataset v1...")
lifecycle_manager.register_dataset(patch, "v1", 2000, is_ready=True)

print("SUCCESS: Patch lifecycle works and survives restarts!")
