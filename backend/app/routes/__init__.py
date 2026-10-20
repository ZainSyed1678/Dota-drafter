from app.routes.draft import router as draft_router
from app.routes.health import router as health_router
from app.routes.heroes import router as heroes_router

__all__ = ["draft_router", "heroes_router", "health_router"]
