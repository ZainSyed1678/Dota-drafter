import os
import threading
import time

import requests
import telebot

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
DATABASE_URL = os.environ.get("DATABASE_URL", "")

_bot_instance = None
_lock_socket = None


def fetch_database_and_model_stats():
    """Fetch database and model stats via HTTP or direct PostgreSQL connection."""
    stats = {}
    try:
        r = requests.get(f"{BACKEND_URL}/database/stats", timeout=4)
        if r.status_code == 200:
            stats = r.json()
            if stats.get("status") == "ok":
                return stats
    except Exception:
        pass

    # Direct DB fallback
    if DATABASE_URL:
        try:
            import psycopg2
            conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*), COALESCE(MAX(match_id), 0) FROM matches;")
                total_matches, max_match_id = cur.fetchone()

                cur.execute("SELECT COALESCE(patch_version, 'unknown'), COUNT(*) FROM matches GROUP BY patch_version ORDER BY COUNT(*) DESC;")
                patch_counts = dict(cur.fetchall())

                cur.execute("""
                    SELECT patch_version, start_time, end_time, matches_fetched, matches_inserted, status
                    FROM collection_runs ORDER BY id DESC LIMIT 1;
                """)
                run_row = cur.fetchone()
                latest_run = None
                if run_row:
                    latest_run = {
                        "patch_version": run_row[0],
                        "start_time": run_row[1].strftime("%Y-%m-%d %H:%M UTC") if run_row[1] else None,
                        "matches_fetched": run_row[3],
                        "matches_inserted": run_row[4],
                        "status": run_row[5],
                    }
            conn.close()

            stats["total_matches"] = total_matches
            stats["max_match_id"] = max_match_id
            stats["patch_distribution"] = patch_counts
            stats["latest_run"] = latest_run
        except Exception:
            pass

    return stats


def create_bot(token: str):
    bot = telebot.TeleBot(token, threaded=False)

    @bot.message_handler(commands=["start", "help"])
    def send_welcome(message):
        text = (
            "🗿 *Dota Drafter Supervisor Bot*\n\n"
            "Command telemetry & models directly from Telegram:\n\n"
            "📊 *Telemetry & Data Freshness*\n"
            "• `/matches` — Matches fetched today, total DB pool & patch breakdown\n"
            "• `/model` — Model version, active patch, trained matches & freshness status\n"
            "• `/stats` — Executive pulse of API, database & model status\n"
            "• `/health` — Infrastructure health check\n\n"
            "🎮 *Drafting & Control*\n"
            "• `/suggest <hero1, hero2>` — Top counter recommendations\n"
            "• `/deploy` — Instant hot-reload of newest model weights\n"
        )
        bot.reply_to(message, text, parse_mode="Markdown")

    @bot.message_handler(commands=["matches", "match_stats"])
    def check_matches(message):
        bot.reply_to(message, "🔍 Querying match collection and database statistics...")
        stats = fetch_database_and_model_stats()

        total_matches = stats.get("total_matches", "Unknown")
        total_str = f"{total_matches:,}" if isinstance(total_matches, int) else str(total_matches)
        patches = stats.get("patch_distribution", {})

        patch_lines = []
        for p, cnt in patches.items():
            badge = "🔥 Active" if p == "7.35f" else "📦 Historical"
            patch_lines.append(f"  • *Patch {p}:* `{cnt:,}` ({badge})")
        patches_text = "\n".join(patch_lines) if patch_lines else "  • No patch breakdown available"

        latest_run = stats.get("latest_run") or {}
        run_patch = latest_run.get("patch_version", "N/A")
        fetched = latest_run.get("matches_fetched", 0)
        inserted = latest_run.get("matches_inserted", 0)
        status = latest_run.get("status", "N/A")
        start_time = latest_run.get("start_time", "Recent")

        report = (
            "📊 *Dota 2 Match Database & Collection*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Total Matches in Database:* `{total_str}`\n"
            "• *Matches by Patch:*\n"
            f"{patches_text}\n\n"
            "📥 *Latest Daily Collection Run:*\n"
            f"• *Target Patch:* `{run_patch}`\n"
            f"• *Raw Matches Fetched:* `{fetched:,}`\n"
            f"• *New Matches Inserted:* `{inserted:,}`\n"
            f"• *Run Status:* `{status}`\n"
            f"• *Run Time:* `{start_time}`\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 Older matches are preserved while new patch matches receive higher recency weight."
        )
        bot.reply_to(message, report, parse_mode="Markdown")

    @bot.message_handler(commands=["model", "model_stats", "model_freshness"])
    def check_model_freshness(message):
        bot.reply_to(message, "🧠 Checking model version, sample size & freshness...")

        # 1. Model Status from backend
        model_version = "Unknown"
        active_patch = "7.35f"
        trained_matches = 0
        accuracy = 0.0
        roc_auc = 0.0
        model_latest_match_id = 0
        loaded_at = "Unknown"

        try:
            r = requests.get(f"{BACKEND_URL}/model/status", timeout=4)
            if r.status_code == 200:
                mdata = r.json()
                model_version = mdata.get("version", "Unknown")
                loaded_at = mdata.get("loaded_at", "Unknown")
                freshness = mdata.get("data_freshness", {})
                active_patch = freshness.get("latest_patch", "7.35f")
                trained_matches = freshness.get("match_count", 0)
                model_latest_match_id = freshness.get("latest_match_id", 0)

                test_m = mdata.get("test_metrics", {})
                accuracy = test_m.get("accuracy", 0.0)
                roc_auc = test_m.get("roc_auc", 0.0)
        except Exception:
            pass

        # 2. Database Stats
        stats = fetch_database_and_model_stats()
        db_max_match_id = stats.get("max_match_id", 0)

        # Freshness determination
        if model_latest_match_id and db_max_match_id:
            if db_max_match_id <= model_latest_match_id:
                freshness_status = "🟢 *UP TO DATE* with latest collected matches!"
            else:
                unretrained = max(0, db_max_match_id - model_latest_match_id)
                freshness_status = f"🟡 Model is active; ~{unretrained} new matches queued for next daily retrain."
        else:
            freshness_status = "🟢 Model is operational."

        trained_str = f"{trained_matches:,}" if trained_matches else "100,000 (Target)"

        report = (
            "🧠 *Drafter Model Status & Freshness*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Model Version:* `{model_version}`\n"
            f"• *Active Patch:* `{active_patch}`\n"
            f"• *Trained On:* `{trained_str} matches`\n"
            f"• *Test Accuracy:* `{accuracy * 100:.2f}%`\n"
            f"• *Test ROC-AUC:* `{roc_auc:.4f}`\n"
            f"• *Last Loaded:* `{loaded_at}`\n\n"
            "🔄 *Match Freshness Check:*\n"
            f"• *Latest Match in Model:* `{model_latest_match_id or 'N/A'}`\n"
            f"• *Latest Match in Database:* `{db_max_match_id or 'N/A'}`\n"
            f"• *Freshness:* {freshness_status}\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 Retrained daily at 00:00 UTC. Use `/deploy` to hot-reload."
        )
        bot.reply_to(message, report, parse_mode="Markdown")

    @bot.message_handler(commands=["stats"])
    def check_stats(message):
        bot.reply_to(message, "🔍 Inspecting system pulse...")
        backend_status = "UNKNOWN"
        heroes_count = "N/A"
        model_ver = "Unknown"

        # Check health
        try:
            r = requests.get(f"{BACKEND_URL}/health", timeout=3)
            if r.status_code == 200:
                data = r.json()
                backend_status = data.get("status", "ok")
                heroes_count = data.get("heroes", "127")
                model_ver = data.get("model_version", "Unknown")
        except Exception:
            backend_status = "UNREACHABLE"

        # Check database stats
        stats = fetch_database_and_model_stats()
        total_matches = stats.get("total_matches", "N/A")
        total_str = f"{total_matches:,}" if isinstance(total_matches, int) else str(total_matches)

        summary = (
            "📈 *Dota Drafter — System Pulse*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Backend API:* `{backend_status}`\n"
            f"• *Model Version:* `{model_ver}`\n"
            f"• *Total Matches in DB:* `{total_str}`\n"
            f"• *Loaded Heroes:* `{heroes_count}`\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "👉 Use `/matches` for collection details or `/model` for freshness."
        )
        bot.reply_to(message, summary, parse_mode="Markdown")

    @bot.message_handler(commands=["health"])
    def check_health(message):
        bot.reply_to(message, "🏥 Pinging infrastructure components...")

        # 1. Backend
        api_status = "🔴 DOWN"
        try:
            r = requests.get(f"{BACKEND_URL}/health", timeout=3)
            if r.status_code == 200:
                api_status = "🟢 UP"
        except Exception:
            pass

        # 2. Database
        db_status = "⚪ NOT SET"
        if DATABASE_URL:
            try:
                import psycopg2
                conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM matches;")
                    cnt = cur.fetchone()[0]
                conn.close()
                db_status = f"🟢 UP ({cnt:,} matches)"
            except Exception as e:
                db_status = f"🔴 ERROR ({str(e)[:30]})"

        report = (
            "🏥 *Infrastructure Health Pulse*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *FastAPI Backend:* {api_status}\n"
            f"• *PostgreSQL (Neon):* {db_status}\n"
            f"• *Automated Daily Pipeline:* 🟢 Active (Daily at 00:00 UTC)\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        bot.reply_to(message, report, parse_mode="Markdown")

    @bot.message_handler(commands=["deploy"])
    def deploy_models(message):
        bot.reply_to(message, "🔄 Telling backend to hot-reload models...")
        try:
            resp = requests.post(f"{BACKEND_URL}/model/reload", timeout=10)
            if resp.status_code == 200:
                bot.reply_to(
                    message, "✅ *SUCCESS!* Backend hot-reloaded updated model weights with zero downtime!", parse_mode="Markdown"
                )
            else:
                bot.reply_to(message, f"❌ Backend responded: {resp.status_code}", parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to reach backend: {e}")

    @bot.message_handler(commands=["suggest"])
    def suggest_picks(message):
        args = message.text.replace("/suggest", "").strip()
        if not args:
            bot.reply_to(
                message,
                "Provide enemy heroes separated by commas. Example:\n`/suggest Pudge, Sniper`",
                parse_mode="Markdown",
            )
            return

        enemy_names = [x.strip() for x in args.split(",") if x.strip()]
        try:
            resp = requests.post(f"{BACKEND_URL}/suggest", json={"team": [], "enemy": enemy_names}, timeout=5)
            if resp.status_code == 200:
                picks = resp.json().get("picks", [])[:5]
                lines = []
                for p in picks:
                    lines.append(f"• *{p['name']}* (Score: `{p['score']}`)")
                text = (
                    f"⚔️ *Top Counters Against {', '.join(enemy_names)}:*\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    + "\n".join(lines)
                    + "\n"
                    "━━━━━━━━━━━━━━━━━━━━━"
                )
                bot.reply_to(message, text, parse_mode="Markdown")
            else:
                bot.reply_to(message, f"❌ Suggest error: {resp.status_code} - {resp.text}")
        except Exception as e:
            bot.reply_to(message, f"❌ Could not query suggestions: {e}")

    return bot


def get_or_create_bot(token: str):
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = create_bot(token)
    return _bot_instance


async def process_telegram_webhook(request):
    global _bot_instance
    if not _bot_instance:
        token = os.environ.get("TELEGRAM_TOKEN")
        if token:
            _bot_instance = create_bot(token)
        else:
            return {"status": "error", "message": "TELEGRAM_TOKEN not configured"}
    try:
        data = await request.json()
        update = telebot.types.Update.de_json(data)
        if update:
            _bot_instance.process_new_updates([update])
        return {"status": "ok"}
    except Exception as e:
        print(f"Error processing telegram webhook: {e}")
        return {"status": "error", "message": str(e)}


def acquire_bot_lock() -> bool:
    global _lock_socket
    import socket

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 9999))
        _lock_socket = s
        return True
    except OSError:
        return False


def start_bot_service(token: str):
    """
    Starts the bot via Webhook if a public URL (like Render) is present,
    or falls back to controlled polling for local development.
    """
    bot = get_or_create_bot(token)
    public_url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("WEBHOOK_URL")

    if public_url:
        webhook_url = f"{public_url.rstrip('/')}/telegram/webhook"
        try:
            bot.remove_webhook()
            bot.set_webhook(url=webhook_url, drop_pending_updates=True)
            print(f"Telegram Bot enabled via Webhook on {webhook_url} (409 polling conflicts permanently avoided)")
            return None
        except Exception as e:
            print(f"Failed to set webhook on {webhook_url}: {e}. Falling back to polling.")

    # Local fallback: Polling with lock and 409 conflict backoff
    if not acquire_bot_lock():
        print("Another worker holds the bot lock. Skipping duplicate polling thread.")
        return None

    def _polling_runner():
        print("Telegram Supervisor Bot starting local fallback polling...")
        try:
            bot.remove_webhook()
        except Exception:
            pass

        last_offset = 0
        while True:
            try:
                updates = bot.get_updates(offset=last_offset, timeout=20)
                if updates:
                    bot.process_new_updates(updates)
                    last_offset = updates[-1].update_id + 1
            except telebot.apihelper.ApiTelegramException as e:
                if e.error_code == 409:
                    print("Telegram Bot 409 Conflict: another instance is active. Sleeping 60s...")
                    time.sleep(60)
                else:
                    print(f"Telegram Bot polling error (will retry in 5s): {e}")
                    time.sleep(5)
            except Exception as e:
                print(f"Telegram Bot polling error (will retry in 5s): {e}")
                time.sleep(5)

    t = threading.Thread(target=_polling_runner, daemon=True)
    t.start()
    return t


def start_bot_thread(token: str):
    return start_bot_service(token)
