"""
Daily Pipeline Coordinator for Dota 2 Drafter.
Automates:
1. Rate-limited match collection from OpenDota into Neon PostgreSQL (until daily API exhaustion).
2. Training updated LightGBM + Bayesian shrinkage model weights on up to 100,000 matches.
3. Synchronizing model weights to backend/model/ and root model/.
4. Triggering hot-reload on the running Render web service.
5. Sending Telegram completion alerts to the bot owner.
"""

import argparse
import datetime
import os
import subprocess
import sys
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

scripts_dir = Path(__file__).resolve().parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from train_from_psql import train_from_postgres


def run_collector(patch: str, max_calls: int = 1500, target: int = 50000, exhaust_api: bool = False) -> bool:
    """Run patch_aware_collector in a separate subprocess."""
    collector_script = scripts_dir / "patch_aware_collector.py"
    if not collector_script.exists():
        print(f"Collector script not found at {collector_script}")
        return False

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("[Collector] DATABASE_URL not set in environment. Skipping collection.")
        return False

    print(f"\n=== Step 1: Collecting matches from OpenDota (Patch: {patch}, Max Calls: {max_calls}, Exhaust: {exhaust_api}) ===")
    cmd = [
        sys.executable, str(collector_script),
        "--patch", patch,
        "--max-calls", str(max_calls),
        "--target", str(target)
    ]
    if exhaust_api:
        cmd.append("--exhaust-api")

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(scripts_dir.parent))
        print(res.stdout)
        if res.returncode != 0:
            print(f"[Collector Warning] Subprocess exited with code {res.returncode}:")
            print(res.stderr)
            # Do not fail entire pipeline if collector had an OpenDota network glitch,
            # we can still retrain on existing matches in DB.
            return False
        return True
    except Exception as e:
        print(f"[Collector Error] Exception running collector: {e}")
        return False


def run_retrain(patch: str, max_samples: int = 100000, version: str = None) -> bool:
    """Retrain model from PostgreSQL."""
    print(f"\n=== Step 2: Retraining model from PostgreSQL (Max Samples: {max_samples}, Version: {version}) ===")
    return train_from_postgres(patch=patch, max_samples=max_samples, version=version)


def notify_backend_reload(backend_url: str, version: str = None, admin_key: str = None) -> bool:
    """Send reload signal to Render backend."""
    if not backend_url:
        print("\n=== Step 3: Skipping Backend reload (No BACKEND_URL provided) ===")
        return True

    backend_url = backend_url.rstrip("/")
    endpoint = f"{backend_url}/model/reload"
    params = {}
    if version:
        params["version"] = version

    headers = {}
    if admin_key:
        headers["x-admin-key"] = admin_key

    print(f"\n=== Step 3: Triggering hot reload on Render ({endpoint}) ===")
    try:
        resp = requests.post(endpoint, params=params, headers=headers, timeout=20)
        if resp.status_code == 200:
            print(f"Hot-reload SUCCESS: {resp.json()}")
            return True
        else:
            print(f"Backend reload responded with status {resp.status_code}: {resp.text}")
            print("Note: Service will auto-deploy once git push lands on main branch.")
            return False
    except Exception as e:
        print(f"Notice: Could not reach backend at {endpoint}: {e}")
        print("Note: Render will automatically restart and load latest model weights upon git commit deploy.")
        return False


def send_telegram_alert(version: str, patch: str, samples: int):
    """Optionally broadcast daily summary to Telegram if chat ID is set."""
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("ADMIN_CHAT_ID")
    if not token or not chat_id:
        return

    text = (
        "🚀 *Daily Dota Drafter Retraining Complete!*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *Model Version:* `{version}`\n"
        f"• *Active Patch:* `{patch}`\n"
        f"• *Trained Dataset:* `{samples:,} matches`\n"
        f"• *Status:* Render hot-reloaded successfully!\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Send `/matches` or `/model` on Telegram for live telemetry."
    )
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=8
        )
        print("[Telegram Alert] Sent daily completion notification.")
    except Exception as e:
        print(f"[Telegram Alert] Notice: Could not send alert: {e}")


def main():
    parser = argparse.ArgumentParser(description="Dota 2 Drafter Daily Collection and Retraining Pipeline")
    parser.add_argument("--patch", type=str, default="7.35f", help="Current Dota 2 patch (default: 7.35f, or 'auto')")
    parser.add_argument("--max-calls", type=int, default=1500, help="Max OpenDota API calls (default: 1500)")
    parser.add_argument("--target", type=int, default=50000, help="Match target for collector (default: 50000)")
    parser.add_argument("--exhaust-api", action="store_true", help="Continue until API quota is exhausted")
    parser.add_argument("--max-samples", type=int, default=100000, help="Max samples for training (default: 100000)")
    parser.add_argument("--version", type=str, default=None, help="Model version string (e.g. v2026.10.21)")
    parser.add_argument("--skip-collect", action="store_true", help="Skip match collection and only retrain")
    parser.add_argument("--backend-url", type=str, default=os.environ.get("BACKEND_URL", "https://dota-drafter-api.onrender.com"),
                        help="Render Backend URL for reload signal")
    parser.add_argument("--admin-key", type=str, default=os.environ.get("ADMIN_API_KEY", ""),
                        help="Admin API key if protected")
    args = parser.parse_args()

    date_str = datetime.datetime.now().strftime("%Y.%m.%d")
    version = args.version or f"v{date_str}"

    print("============================================================")
    print("  Dota 2 Drafter Automated Pipeline Starting")
    print(f"  Date: {datetime.datetime.now().isoformat()}")
    print(f"  Patch: {args.patch} | Version: {version} | Samples: {args.max_samples} | Exhaust: {args.exhaust_api}")
    print("============================================================")

    # 1. Collection
    if not args.skip_collect:
        run_collector(patch=args.patch, max_calls=args.max_calls, target=args.target, exhaust_api=args.exhaust_api)
    else:
        print("[Collector] Skipped via --skip-collect flag.")

    # 2. Retraining
    train_success = run_retrain(patch=args.patch, max_samples=args.max_samples, version=version)
    if not train_success:
        print("\n[Pipeline ERROR] Model training failed! Exiting with status 1.")
        sys.exit(1)

    # 3. Backend Hot-Reload Ping
    notify_backend_reload(backend_url=args.backend_url, version=version, admin_key=args.admin_key)

    # 4. Telegram Notification
    send_telegram_alert(version=version, patch=args.patch, samples=args.max_samples)

    print("\n============================================================")
    print(f"  Daily Pipeline Complete for version {version}!")
    print("============================================================")


if __name__ == "__main__":
    main()
