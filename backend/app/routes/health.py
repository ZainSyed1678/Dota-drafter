from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from app.cache import draft_cache
from app.config import settings
from app.model_loader import store

router = APIRouter(tags=["health"])


@router.get("/")
def root():
    return {
        "status": "ok",
        "service": "Dota 2 Drafter API",
        "version": store.metadata.get("version", "2.2.0"),
        "docs": "/docs",
        "health": "/health"
    }


@router.get("/health")
def health():
    ready = store.metadata.get("status") == "ready"
    return {
        "status": "ok" if ready else store.metadata.get("status", "unknown"),
        "heroes": len(store.hero_map),
        "model_version": store.metadata.get("version", "unknown"),
        "data_freshness": store.metadata.get("data_freshness", {}),
    }


@router.get("/model/status")
def model_status():
    return store.metadata


@router.get("/database/stats")
def database_stats():
    freshness = store.metadata.get("data_freshness", {})
    model_latest_match_id = freshness.get("latest_match_id", 0)

    model_freshness_data = {
        "version": store.metadata.get("version"),
        "latest_patch": freshness.get("latest_patch"),
        "model_trained_matches": freshness.get("match_count"),
        "model_latest_match_id": model_latest_match_id,
        "db_latest_match_id": None,
        "is_up_to_date": True,
        "unretrained_match_estimate": 0,
    }

    db_url = settings.DATABASE_URL
    if not db_url:
        return {
            "status": "no_database_url",
            "message": "DATABASE_URL not configured",
            "total_matches": 0,
            "patch_distribution": {},
            "latest_run": None,
            "model_freshness": model_freshness_data,
        }

    try:
        import psycopg2
        conn = psycopg2.connect(db_url, connect_timeout=5)
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
                    "start_time": run_row[1].isoformat() if run_row[1] else None,
                    "end_time": run_row[2].isoformat() if run_row[2] else None,
                    "matches_fetched": run_row[3],
                    "matches_inserted": run_row[4],
                    "status": run_row[5],
                }

        conn.close()

        unretrained = max(0, max_match_id - model_latest_match_id) if (max_match_id and model_latest_match_id) else 0
        model_freshness_data["db_latest_match_id"] = max_match_id
        model_freshness_data["is_up_to_date"] = (max_match_id <= model_latest_match_id) if model_latest_match_id else False
        model_freshness_data["unretrained_match_estimate"] = unretrained

        return {
            "status": "ok",
            "total_matches": total_matches,
            "max_match_id": max_match_id,
            "patch_distribution": patch_counts,
            "latest_run": latest_run,
            "model_freshness": model_freshness_data,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "total_matches": 0,
            "patch_distribution": {},
            "latest_run": None,
            "model_freshness": model_freshness_data,
        }


@router.post("/model/reload")
def model_reload(version: Optional[str] = None, x_admin_key: Optional[str] = Header(None)):
    if settings.ADMIN_API_KEY and x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized: invalid admin key")

    success = store.load(version=version)
    if success:
        draft_cache.clear()
        return {
            "status": "success",
            "version": store.metadata.get("version"),
            "metadata": store.metadata
        }
    raise HTTPException(status_code=500, detail="Failed to reload model files from disk.")


@router.get("/debug")
def debug():
    # Only available in development mode
    if settings.ENV != "development" and not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Debug endpoint disabled in production.")

    return {
        "hero_map_sample": {k: store.hero_map[k] for k in list(store.hero_map)[:20]},
        "avg_matchup_sample": {store.hero_map.get(k, k): round(v, 4)
                               for k, v in list(store.hero_avg_matchup.items())[:10]},
        "total_heroes": len(store.hero_map),
        "total_matchup_pairs": len(store.matchup_matrix),
        "total_synergy_pairs": len(store.synergy_matrix),
        "cache_stats": draft_cache.stats(),
    }
