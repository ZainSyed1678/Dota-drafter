"""
Dota 2 Drafter - Main Entrypoint
Exports FastAPI `app` from modularized `app.main` for uvicorn, Docker, and Render.
"""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app  # noqa: F401

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
