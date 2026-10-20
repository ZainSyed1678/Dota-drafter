from fastapi import APIRouter, HTTPException, Request, Response

import app.scoring as scoring
from app.cache import draft_cache
from app.config import settings
from app.hero_knowledge import get_hero_difficulty, get_hero_overview
from app.logger import get_logger
from app.model_loader import store
from app.schemas import DraftRequest, HeroSuggestion, SuggestResponse

router = APIRouter(tags=["draft"])
log = get_logger("dota-api.draft")


@router.post("/suggest", response_model=SuggestResponse)
def suggest(request: Request, req: DraftRequest, response: Response):
    if not store.hero_map:
        raise HTTPException(status_code=503, detail="Model not loaded yet — pkl files missing")

    enemy_ids = scoring.resolve_or_raise(req.enemy, "enemy")
    ally_ids = scoring.resolve_or_raise(req.team, "team")
    ban_ids = scoring.resolve_or_raise(req.bans, "bans")
    selected = set(enemy_ids + ally_ids + ban_ids)

    # Determine role-aware mode and target roles
    is_role_aware = req.role_aware or bool(req.roles_needed)
    if req.roles_needed:
        target_roles = [r.lower().strip() for r in req.roles_needed]
    elif req.role_aware:
        target_roles = scoring.infer_missing_roles(ally_ids)
    else:
        target_roles = []

    # Bracket handling
    bracket = req.bracket or "all"
    bracket_note = None
    bracket_fallback = False
    if bracket.lower() != "all":
        bracket_fallback = True
        bracket_note = f"Rank bracket '{bracket}' requested, but separate bracket data is unavailable. Falling back to global matrices."

    # Cache lookup
    cache_key = (
        tuple(sorted(enemy_ids)),
        tuple(sorted(ally_ids)),
        tuple(sorted(ban_ids)),
        tuple(sorted(target_roles)),
        is_role_aware,
        bracket.lower()
    )

    cached_res = draft_cache.get(cache_key)
    if cached_res is not None:
        response.headers["X-Cache"] = "HIT"
        return cached_res

    response.headers["X-Cache"] = "MISS"

    scored = []
    engine = settings.PREDICTION_ENGINE

    for hero_id in store.hero_map:
        if hero_id in selected:
            continue

        score = scoring.predict(hero_id, enemy_ids, ally_ids, engine=engine)
        h_roles = set(scoring.get_roles(hero_id))
        matches_role = bool(h_roles & set(target_roles)) if is_role_aware else True
        scored.append((hero_id, score, matches_role))

    if is_role_aware and target_roles:
        role_candidates = [x for x in scored if x[2]]
        role_candidates.sort(key=lambda x: x[1], reverse=True)
        selected_picks = role_candidates[:9]
        if len(selected_picks) < 9:
            other_candidates = [x for x in scored if not x[2]]
            other_candidates.sort(key=lambda x: x[1], reverse=True)
            selected_picks.extend(other_candidates[: 9 - len(selected_picks)])
    else:
        scored.sort(key=lambda x: x[1], reverse=True)
        selected_picks = scored[:9]

    picks = []
    enemy_names = [store.id_to_name.get(e, str(e)) for e in enemy_ids]
    ally_names = [store.id_to_name.get(a, str(a)) for a in ally_ids]

    for item in selected_picks:
        hero_id, score = item[0], item[1]
        hero_name = store.id_to_name[hero_id]
        reasons, reason_details, hero_conf, hero_samples = scoring.build_reasons_and_details(
            hero_id, enemy_ids, enemy_names, ally_ids, ally_names
        )
        picks.append(HeroSuggestion(
            id=hero_id,
            name=hero_name,
            score=round(score, 4),
            confidence=hero_conf,
            sample_size=hero_samples,
            reasons=reasons,
            reason_details=reason_details,
            roles=scoring.get_roles(hero_id),
            difficulty=get_hero_difficulty(hero_name),
            overview=get_hero_overview(hero_name),
        ))

    result = SuggestResponse(
        picks=picks,
        roles_needed=target_roles,
        role_aware=is_role_aware,
        bracket=bracket,
        bracket_fallback=bracket_fallback,
        bracket_note=bracket_note
    )

    # Store in LRU cache
    draft_cache.put(cache_key, result)
    return result
