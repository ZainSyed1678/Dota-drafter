"""
Dota 2 Drafter - Main Entrypoint
Exports FastAPI `app` from modularized `app.main` for uvicorn and Docker.
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
