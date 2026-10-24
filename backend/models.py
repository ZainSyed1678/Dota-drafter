from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class DraftRequest(BaseModel):
    enemy: List[Union[str, int]] = Field(default_factory=list, description="Enemy team heroes (IDs or names, max 5)")
    team: List[Union[str, int]] = Field(default_factory=list, description="Allied team heroes (IDs or names, max 4)")
    bans: List[Union[str, int]] = Field(default_factory=list, description="Banned heroes (IDs or names)")
    roles_needed: Optional[List[str]] = Field(default=None, description="Explicit roles to fill (carry, mid, offlane, support)")
    role_aware: bool = Field(default=False, description="Enable role-aware suggestion mode")
    bracket: Optional[str] = Field(default="all", description="Rank bracket filter (e.g. divine_plus, legend_ancient, all)")

    @field_validator("enemy")
    @classmethod
    def validate_enemy_size(cls, v: list) -> list:
        if len(v) > 5:
            raise ValueError("Too many enemy heroes. Maximum allowed is 5 heroes.")
        return v

    @field_validator("team")
    @classmethod
    def validate_team_size(cls, v: list) -> list:
        if len(v) > 4:
            raise ValueError("Too many allied heroes. Maximum allowed is 4 heroes (you are picking the 5th).")
        return v

    @field_validator("roles_needed")
    @classmethod
    def validate_roles(cls, v: Optional[list]) -> Optional[list]:
        if v is None:
            return v
        valid_roles = {"carry", "mid", "offlane", "support", "soft_support", "hard_support"}
        cleaned = []
        for r in v:
            r_clean = str(r).strip().lower().replace(" ", "_")
            if r_clean not in valid_roles:
                raise ValueError(f"Invalid role '{r}'. Valid roles are: {', '.join(sorted(valid_roles))}")
            cleaned.append(r_clean)
        return cleaned

    @model_validator(mode="after")
    def validate_heroes_and_overlaps(self):
        import scoring

        # 1. Resolve and validate hero existence (raises ValueError on unknown heroes)
        enemy_ids = scoring.resolve_or_raise(self.enemy, "enemy")
        team_ids = scoring.resolve_or_raise(self.team, "team")
        ban_ids = scoring.resolve_or_raise(self.bans, "bans")

        # 2. Check intra-list duplicates
        for lst_name, id_list, raw_list in [("enemy", enemy_ids, self.enemy), ("team", team_ids, self.team), ("bans", ban_ids, self.bans)]:
            if len(id_list) != len(set(id_list)):
                seen = set()
                dups = []
                for hid, raw in zip(id_list, raw_list):
                    if hid in seen:
                        dups.append(str(raw))
                    seen.add(hid)
                raise ValueError(f"Duplicate heroes detected in {lst_name} list: {', '.join(dups)}")

        # 3. Check cross-team overlap
        enemy_set = set(enemy_ids)
        team_set = set(team_ids)
        overlap_teams = enemy_set & team_set
        if overlap_teams:
            names = [scoring.id_to_name.get(h, str(h)) for h in overlap_teams]
            raise ValueError(f"A hero cannot be picked on both teams simultaneously: {', '.join(names)}")

        # 4. Check ban overlap
        ban_set = set(ban_ids)
        overlap_bans_enemy = ban_set & enemy_set
        if overlap_bans_enemy:
            names = [scoring.id_to_name.get(h, str(h)) for h in overlap_bans_enemy]
            raise ValueError(f"A hero cannot be both banned and picked on enemy team: {', '.join(names)}")

        overlap_bans_team = ban_set & team_set
        if overlap_bans_team:
            names = [scoring.id_to_name.get(h, str(h)) for h in overlap_bans_team]
            raise ValueError(f"A hero cannot be both banned and picked on your team: {', '.join(names)}")

        return self


class ReasonDetail(BaseModel):
    summary: str
    target_hero: str = ""
    reason_type: str = "counter"  # counter | synergy | meta
    how_and_why: str = ""
    key_abilities: list[str] = []
    beginner_tip: str = ""
    sample_size: int = 0
    confidence: str = "medium"  # low | medium | high


class HeroSuggestion(BaseModel):
    id:             int
    name:           str
    score:          float
    confidence:     str = "medium"  # low | medium | high
    sample_size:    int = 0
    reasons:        list[str] = []
    reason_details: list[ReasonDetail] = []
    roles:          list[str] = []
    difficulty:     str = "Easy"
    overview:       str = ""


class SuggestResponse(BaseModel):
    picks: list[HeroSuggestion]
    roles_needed: list[str] = []
    role_aware: bool = False
    bracket: str = "all"
    bracket_fallback: bool = False
    bracket_note: Optional[str] = None
