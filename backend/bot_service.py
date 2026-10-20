import os
import threading
import time

import requests
import telebot

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
DATABASE_URL = os.environ.get("DATABASE_URL", "")

_bot_instance = None
_lock_socket = None


def create_bot(token: str):
    bot = telebot.TeleBot(token, threaded=False)

    @bot.message_handler(commands=["start", "help"])
    def send_welcome(message):
        text = (
            "🗿 *Ugh! Grog Dota Drafter Supervisor Bot!*\n\n"
            "Command rocks from your phone:\n\n"
            "📊 *System Telemetry*\n"
            "• `/stats` — Executive pulse of API & models\n"
            "• `/health` — Health check of API & Database\n"
            "• `/model_stats` — Loaded model versions & engine\n\n"
            "🎮 *Drafting & Control*\n"
            "• `/suggest <hero1, hero2>` — Quick counter recommendations\n"
            "• `/deploy` — Hot-reload newly trained models\n"
        )
        bot.reply_to(message, text, parse_mode="Markdown")

    @bot.message_handler(commands=["stats"])
    def check_stats(message):
        bot.reply_to(message, "🔍 Grog inspecting system pulse...")
        backend_status = "UNKNOWN"
        heroes_count = "N/A"

        # Check health
        try:
            r = requests.get(f"{BACKEND_URL}/health", timeout=3)
            if r.status_code == 200:
                data = r.json()
                backend_status = data.get("status", "ok")
                heroes_count = data.get("heroes", "127")
        except Exception:
            backend_status = "UNREACHABLE"

        # Check model status
        try:
            r = requests.get(f"{BACKEND_URL}/model/status", timeout=3)
            if r.status_code == 200:
                mdata = r.json()
                loaded_at = mdata.get("loaded_at", "never")
        except Exception:
            loaded_at = "unknown"

        # Check metrics for total requests
        total_req = 0
        try:
            r = requests.get(f"{BACKEND_URL}/metrics", timeout=3)
            if r.status_code == 200:
                for line in r.text.splitlines():
                    if line.startswith("dota_api_requests_total{"):
                        val = line.split()[-1]
                        total_req += int(float(val))
        except Exception:
            pass

        summary = (
            "📈 *Dota Drafter — System Pulse*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Backend API:* `{backend_status}`\n"
            f"• *Loaded Heroes:* `{heroes_count}`\n"
            f"• *Total API Requests:* `{total_req}`\n"
            f"• *Models Loaded At:* `{loaded_at}`\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "👉 Use `/model_stats` for files or `/health` for DB status."
        )
        bot.reply_to(message, summary, parse_mode="Markdown")

    @bot.message_handler(commands=["health"])
    def check_health(message):
        bot.reply_to(message, "🏥 Grog pinging all components...")

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

                conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM matches;")
                    cnt = cur.fetchone()[0]
                conn.close()
                db_status = f"🟢 UP ({cnt} matches)"
            except Exception as e:
                db_status = f"🔴 ERROR ({str(e)[:30]})"

        report = (
            "🏥 *Infrastructure Health Pulse*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *FastAPI Backend:* {api_status}\n"
            f"• *PostgreSQL (Neon):* {db_status}\n"
            f"• *Auto Collector:* 🟢 Active (Every 3h via GitHub Cron)\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        bot.reply_to(message, report, parse_mode="Markdown")

    @bot.message_handler(commands=["model_stats"])
    def check_model_stats(message):
        try:
            resp = requests.get(f"{BACKEND_URL}/model/status", timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status", "unknown")
                loaded = data.get("loaded_at", "never")
                files = data.get("files", {})

                file_lines = []
                for name, meta in files.items():
                    size_kb = meta.get("size_bytes", 0) / 1024
                    file_lines.append(f"• `{name}`: {size_kb:.1f} KB")

                text = (
                    "🧠 *Model Registry Metadata*\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    f"• *Status:* `{status}`\n"
                    f"• *Last Loaded:* `{loaded}`\n\n"
                    "*Model Artifacts:*\n"
                    + ("\n".join(file_lines) if file_lines else "• None found")
                    + "\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    "💡 Use `/deploy` to hot-reload models!"
                )
                bot.reply_to(message, text, parse_mode="Markdown")
            else:
                bot.reply_to(message, f"❌ Backend returned: {resp.status_code}")
        except Exception as e:
            bot.reply_to(message, f"❌ Could not reach Backend: {e}")

    @bot.message_handler(commands=["deploy"])
    def deploy_models(message):
        bot.reply_to(message, "🔄 Grog telling backend to hot-reload models...")
        try:
            resp = requests.post(f"{BACKEND_URL}/model/reload", timeout=10)
            if resp.status_code == 200:
                bot.reply_to(
                    message, "✅ *SUCCESS!* Backend swapped rocks safely without downtime!", parse_mode="Markdown"
                )
            else:
                bot.reply_to(message, f"❌ Backend yelled: {resp.status_code}", parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to reach backend: {e}")

    @bot.message_handler(commands=["suggest"])
    def suggest_picks(message):
        args = message.text.replace("/suggest", "").strip()
        if not args:
            bot.reply_to(
                message,
                "Ugh! Tell Grog enemy heroes separated by commas! Example:\n`/suggest Pudge, Sniper`",
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
