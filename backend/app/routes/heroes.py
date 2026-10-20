from fastapi import APIRouter

from app.model_loader import store

router = APIRouter(tags=["heroes"])


@router.get("/heroes")
def get_heroes():
    """Return canonical list of Dota 2 heroes with numeric IDs and metadata."""
    if store.heroes_list:
        return store.heroes_list
    return [
        {"id": hid, "name": hname, "roles": store.hero_roles.get(hid, ["offlane"]), "attribute": "all"}
        for hid, hname in sorted(store.hero_map.items())
    ]
