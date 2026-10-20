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
