import os

import requests
import telebot

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
BACKEND_URL = os.environ.get("BACKEND_URL", "https://dota-drafter-api.onrender.com")
PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://prometheus:9090")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
POSTGRES_URL = os.environ.get("DATABASE_URL", os.environ.get("POSTGRES_URL", "http://postgres:5432"))
GRAFANA_URL = os.environ.get("GRAFANA_URL", "http://grafana:3000")

if not TELEGRAM_TOKEN:
    print("No TELEGRAM_TOKEN found! Bot cannot start.")
    exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Initialize Qdrant and Embedding model once
qdrant_client_instance = None
embedding_model_instance = None

def get_qdrant_and_embedder():
    global qdrant_client_instance, embedding_model_instance
    if qdrant_client_instance is None:
        from qdrant_client import QdrantClient
        qdrant_client_instance = QdrantClient(url=QDRANT_URL)
    if embedding_model_instance is None:
        from fastembed import TextEmbedding
        embedding_model_instance = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return qdrant_client_instance, embedding_model_instance

def query_prometheus(query: str):
    try:
        resp = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query}, timeout=4)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("data", {}).get("result", [])
    except Exception:
        pass
    return []

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "🗿 *Ugh! Grog Dota Drafter Supervisor Bot!*\n\n"
        "Here are all the rocks you can command:\n\n"
        "📊 *System Telemetry & Statistics*\n"
        "• `/stats` — Executive summary of API & ML pipeline\n"
        "• `/api_stats` — Live API traffic, error rates & response latency\n"
        "• `/model_stats` — Active model registry, engine mode & files\n"
        "• `/health` — Traffic-light health check of all 6 components\n\n"
        "🎮 *Drafting & Knowledge*\n"
        "• `/hero <name>` — Semantic patch search (e.g. `/hero Pudge`)\n"
        "• `/deploy` — Hot-reload trained models into backend\n"
        "• `/metrics` — Prometheus raw targets check\n"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def check_stats(message):
    bot.reply_to(message, "🔍 Grog inspecting system pulse...")

    # 1. Total Requests
    total_req_res = query_prometheus("sum(dota_api_requests_total) or vector(0)")
    total_req = total_req_res[0]["value"][1] if total_req_res else "0"

    # 2. Hero count
    hero_res = query_prometheus("dota_loaded_heroes_total")
    heroes_count = hero_res[0]["value"][1] if hero_res else "N/A"

    # 3. Active engine
    engine_res = query_prometheus("dota_active_prediction_engine")
    if engine_res:
        engine_str = "XGBoost (ML)" if float(engine_res[0]["value"][1]) == 1.0 else "Heuristics (Math)"
    else:
        engine_str = "Unknown"

    # 4. Latency p50
    p50_res = query_prometheus("histogram_quantile(0.50, sum(rate(dota_request_latency_seconds_bucket[5m])) by (le)) * 1000")
    p50_ms = f"{float(p50_res[0]['value'][1]):.1f} ms" if p50_res and p50_res[0]['value'][1] != "NaN" else "< 10 ms"

    # 5. Backend Model Status
    backend_status = "UNKNOWN"
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=3)
        if resp.status_code == 200:
            backend_status = resp.json().get("status", "ok")
    except Exception:
        backend_status = "UNREACHABLE"

    summary = (
        "📈 *Dota Drafter — System Pulse*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *Backend Status:* `{backend_status}`\n"
        f"• *Active Engine:* `{engine_str}`\n"
        f"• *Loaded Heroes:* `{heroes_count}`\n"
        f"• *Total API Calls:* `{int(float(total_req))}`\n"
        f"• *Median Latency (p50):* `{p50_ms}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "👉 Use `/api_stats` for request breakdown or `/model_stats` for files."
    )
    bot.reply_to(message, summary, parse_mode="Markdown")

@bot.message_handler(commands=['api_stats'])
def check_api_stats(message):
    bot.reply_to(message, "⚡ Grog gathering API performance numbers...")

    # Request count by endpoint
    req_by_ep = query_prometheus("sum by (endpoint) (dota_api_requests_total)")
    # HTTP status code counts
    status_res = query_prometheus("sum by (status) (dota_api_requests_total)")
    # Latencies
    p50_res = query_prometheus("histogram_quantile(0.50, sum(rate(dota_request_latency_seconds_bucket[5m])) by (le)) * 1000")
    p95_res = query_prometheus("histogram_quantile(0.95, sum(rate(dota_request_latency_seconds_bucket[5m])) by (le)) * 1000")

    p50 = f"{float(p50_res[0]['value'][1]):.1f} ms" if p50_res and p50_res[0]['value'][1] != "NaN" else "< 10 ms"
    p95 = f"{float(p95_res[0]['value'][1]):.1f} ms" if p95_res and p95_res[0]['value'][1] != "NaN" else "< 25 ms"

    ep_lines = []
    if req_by_ep:
        for r in req_by_ep:
            ep = r["metric"].get("endpoint", "unknown")
            count = int(float(r["value"][1]))
            ep_lines.append(f"  • `{ep}`: {count} calls")
    else:
        ep_lines.append("  • No requests recorded yet")

    status_lines = []
    if status_res:
        for r in status_res:
            st = r["metric"].get("status", "unknown")
            cnt = int(float(r["value"][1]))
            status_lines.append(f"  • HTTP `{st}`: {cnt}")
    else:
        status_lines.append("  • None")

    response = (
        "🚀 *API Performance Telemetry*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "*Response Latency:*\n"
        f"• Median (p50): `{p50}`\n"
        f"• 95th Percentile (p95): `{p95}`\n\n"
        "*Traffic by Endpoint:*\n"
        + "\n".join(ep_lines) + "\n\n"
        "*Status Code Distribution:*\n"
        + "\n".join(status_lines) + "\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )
    bot.reply_to(message, response, parse_mode="Markdown")


@bot.message_handler(commands=['matches', 'match_stats'])
def check_matches(message):
    bot.reply_to(message, "🔍 Querying match collection and database statistics...")
    try:
        r = requests.get(f"{BACKEND_URL}/database/stats", timeout=5)
        if r.status_code == 200:
            stats = r.json()
            total_matches = stats.get("total_matches", 0)
            patches = stats.get("patch_distribution", {})
            patch_lines = []
            for p, cnt in patches.items():
                badge = "🔥 Active" if p == "7.35f" else "📦 Historical"
                patch_lines.append(f"  • *Patch {p}:* `{cnt:,}` ({badge})")
            patches_text = "\n".join(patch_lines) if patch_lines else "  • No patch data"

            latest_run = stats.get("latest_run") or {}
            run_patch = latest_run.get("patch_version", "N/A")
            fetched = latest_run.get("matches_fetched", 0)
            inserted = latest_run.get("matches_inserted", 0)
            status = latest_run.get("status", "N/A")
            start_time = latest_run.get("start_time", "Recent")

            report = (
                "📊 *Dota 2 Match Database & Collection*\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"• *Total Matches in Database:* `{total_matches:,}`\n"
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
            return
    except Exception:
        pass
    bot.reply_to(message, "❌ Could not retrieve match database stats from Backend.")


@bot.message_handler(commands=['model'])
def check_model_freshness(message):
    bot.reply_to(message, "🧠 Checking model version, sample size & freshness...")
    try:
        r = requests.get(f"{BACKEND_URL}/database/stats", timeout=5)
        m_r = requests.get(f"{BACKEND_URL}/model/status", timeout=5)
        if r.status_code == 200 and m_r.status_code == 200:
            db_stats = r.json()
            mdata = m_r.json()
            version = mdata.get("version", "Unknown")
            loaded_at = mdata.get("loaded_at", "Unknown")
            freshness = mdata.get("data_freshness", {})
            active_patch = freshness.get("latest_patch", "7.35f")
            trained_matches = freshness.get("match_count", 0)
            model_latest_match_id = freshness.get("latest_match_id", 0)
            db_latest_match_id = db_stats.get("max_match_id", 0)

            test_m = mdata.get("test_metrics", {})
            acc = test_m.get("accuracy", 0.0)
            roc = test_m.get("roc_auc", 0.0)

            if model_latest_match_id and db_latest_match_id:
                if db_latest_match_id <= model_latest_match_id:
                    freshness_status = "🟢 *UP TO DATE* with latest collected matches!"
                else:
                    unretrained = max(0, db_latest_match_id - model_latest_match_id)
                    freshness_status = f"🟡 Model is active; ~{unretrained} new matches queued for next daily retrain."
            else:
                freshness_status = "🟢 Model is operational."

            trained_str = f"{trained_matches:,}" if trained_matches else "100,000 (Target)"

            report = (
                "🧠 *Drafter Model Status & Freshness*\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"• *Model Version:* `{version}`\n"
                f"• *Active Patch:* `{active_patch}`\n"
                f"• *Trained On:* `{trained_str} matches`\n"
                f"• *Test Accuracy:* `{acc * 100:.2f}%`\n"
                f"• *Test ROC-AUC:* `{roc:.4f}`\n"
                f"• *Last Loaded:* `{loaded_at}`\n\n"
                "🔄 *Match Freshness Check:*\n"
                f"• *Latest Match in Model:* `{model_latest_match_id or 'N/A'}`\n"
                f"• *Latest Match in Database:* `{db_latest_match_id or 'N/A'}`\n"
                f"• *Freshness:* {freshness_status}\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 Retrained daily at 00:00 UTC. Use `/deploy` to hot-reload."
            )
            bot.reply_to(message, report, parse_mode="Markdown")
            return
    except Exception:
        pass
    bot.reply_to(message, "❌ Could not retrieve model status from Backend.")

@bot.message_handler(commands=['model_stats'])
def check_model_stats(message):
    bot.reply_to(message, "📦 Grog checking Model Registry files...")
    try:
        resp = requests.get(f"{BACKEND_URL}/model/status", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            status = data.get("status", "unknown")
            loaded = data.get("loaded_at", "never")
            files = data.get("files", {})

            file_lines = []
            for name, meta in files.items():
                size_kb = meta.get("size_bytes", 0) / 1024
                mtime = meta.get("modified_at", "").split("T")[0]
                file_lines.append(f"• `{name}`: {size_kb:.1f} KB ({mtime})")

            text = (
                "🧠 *Model Registry Metadata*\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"• *Status:* `{status}`\n"
                f"• *Last Loaded:* `{loaded}`\n\n"
                "*Model Artifacts on Disk:*\n"
                + ("\n".join(file_lines) if file_lines else "• None found") + "\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 Use `/deploy` to hot-reload if you trained a new model!"
            )
            bot.reply_to(message, text, parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ Backend returned error: {resp.status_code}")
    except Exception as e:
        bot.reply_to(message, f"❌ Could not reach Backend API: {e}")

@bot.message_handler(commands=['health'])
def check_health(message):
    bot.reply_to(message, "🏥 Grog pinging all village huts (health check)...")

    checks = []

    # 1. Backend
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=2)
        checks.append(("Backend API", "🟢 UP" if r.status_code == 200 else f"🔴 {r.status_code}"))
    except Exception:
        checks.append(("Backend API", "🔴 DOWN"))

    # 2. Prometheus
    try:
        r = requests.get(f"{PROMETHEUS_URL}/-/healthy", timeout=2)
        checks.append(("Prometheus", "🟢 UP" if r.status_code == 200 else f"🔴 {r.status_code}"))
    except Exception:
        checks.append(("Prometheus", "🔴 DOWN"))

    # 3. Qdrant
    try:
        r = requests.get(f"{QDRANT_URL}/healthz", timeout=2)
        checks.append(("Qdrant Vector DB", "🟢 UP" if r.status_code == 200 else f"🔴 {r.status_code}"))
    except Exception:
        checks.append(("Qdrant Vector DB", "🔴 DOWN"))

    # 4. Grafana
    try:
        r = requests.get(f"{GRAFANA_URL}/api/health", timeout=2)
        checks.append(("Grafana Dashboards", "🟢 UP" if r.status_code == 200 else f"🔴 {r.status_code}"))
    except Exception:
        checks.append(("Grafana Dashboards", "🔴 DOWN"))

    # 5. PostgreSQL (via backend debug or ping)
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(("postgres", 5432))
        s.close()
        checks.append(("PostgreSQL", "🟢 UP"))
    except Exception:
        checks.append(("PostgreSQL", "🔴 DOWN"))

    lines = [f"• *{name}:* {status}" for name, status in checks]

    report = (
        "🏥 *Infrastructure Health Pulse*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        + "\n".join(lines) + "\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Grafana Dashboard live at: `http://localhost:3001`"
    )
    bot.reply_to(message, report, parse_mode="Markdown")

@bot.message_handler(commands=['deploy'])
def deploy_models(message):
    bot.reply_to(message, "🔄 Grog telling backend to hot-reload models...")
    try:
        resp = requests.post(f"{BACKEND_URL}/model/reload", timeout=10)
        if resp.status_code == 200:
            bot.reply_to(message, "✅ *SUCCESS!* Backend swapped the rocks safely without restarting!", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ *FAILED!* Backend yelled: {resp.status_code}", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Grog could not reach backend: {e}")

@bot.message_handler(commands=['hero'])
def check_hero(message):
    try:
        hero_query = message.text.replace('/hero', '').strip()
        if not hero_query:
            bot.reply_to(message, "Ugh! Tell Grog which hero! Example: `/hero Sven` or `/hero Pudge`", parse_mode="Markdown")
            return

        bot.reply_to(message, f"🔍 Grog searching Vector Brain for *{hero_query}*...", parse_mode="Markdown")
        client, embedding_model = get_qdrant_and_embedder()

        query_norm = hero_query.lower().strip().replace("-", " ")

        # 1. First try payload scroll match for exact/partial hero name
        scroll_res, _ = client.scroll(
            collection_name="patch_notes",
            limit=150,
            with_payload=True,
            with_vectors=False
        )

        best_match = None
        for point in scroll_res:
            point.payload.get("hero", "")
            h_lower = point.payload.get("hero_lower", "").replace("-", " ")
            if query_norm == h_lower:
                best_match = point.payload.get("text", "")
                break
            elif query_norm in h_lower or h_lower in query_norm:
                if best_match is None:
                    best_match = point.payload.get("text", "")

        # 2. If not found by name, run vector semantic similarity search
        if not best_match:
            query_vector = list(embedding_model.embed([hero_query]))[0].tolist()
            search_result = client.search(
                collection_name="patch_notes",
                query_vector=query_vector,
                limit=1
            )
            if search_result and search_result[0].score > 0.60:
                best_match = search_result[0].payload.get("text", "")

        if best_match:
            if len(best_match) > 3800:
                best_match = best_match[:3800] + "\n\n...(truncated for Telegram)"
            bot.reply_to(message, f"📜 *Patch Notes Update:*\n\n{best_match}", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ Grog could not find any patch notes for '{hero_query}'. Check spelling!")

    except Exception as e:
        bot.reply_to(message, f"Grog's brain hurts: {e}")

if __name__ == "__main__":
    print("Grog Bot waking up...")
    import time
    try:
        bot.remove_webhook()
    except Exception:
        pass

    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except Exception as e:
            err_str = str(e)
            if "409" in err_str or "Conflict" in err_str:
                print("Telegram Bot 409 Conflict: another instance is running. Backing off for 60s...")
                time.sleep(60)
            else:
                print(f"Grog Bot polling error: {e}. Retrying in 5s...")
                time.sleep(5)
