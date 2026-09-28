from pydantic import BaseModel, field_validator, model_validator

class DraftRequest(BaseModel):
    enemy: list[str] = []
    team:  list[str] = []

    @field_validator("enemy", "team")
    @classmethod
    def validate_team_size_and_clean(cls, v: list[str], info) -> list[str]:
        field_name = info.field_name
        if len(v) > 5:
            raise ValueError(f"Too many heroes for {field_name}. Maximum allowed is 5 heroes.")
        
        cleaned = [name.strip() for name in v if name and isinstance(name, str) and name.strip()]
        
        # Check for duplicates within the team
        seen = set()
        duplicates = []
        for name in cleaned:
            low = name.lower()
            if low in seen:
                duplicates.append(name)
            seen.add(low)
            
        if duplicates:
            raise ValueError(f"Duplicate heroes detected in {field_name}: {', '.join(duplicates)}")
            
        return cleaned

    @model_validator(mode="after")
    def validate_no_cross_team_duplicates(self):
        team_set = {h.lower() for h in self.team}
        enemy_set = {h.lower() for h in self.enemy}
        overlap = team_set & enemy_set
        if overlap:
            raise ValueError(f"A hero cannot be picked on both teams simultaneously: {', '.join(overlap)}")
        return self

class HeroSuggestion(BaseModel):
    id:      int
    name:    str
    score:   float
    reasons: list[str]
    roles:   list[str]

class SuggestResponse(BaseModel):
    picks: list[HeroSuggestion]
