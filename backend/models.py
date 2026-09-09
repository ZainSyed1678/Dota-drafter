from pydantic import BaseModel

class DraftRequest(BaseModel):
    enemy: list[str]
    team:  list[str]

class HeroSuggestion(BaseModel):
    id:      int
    name:    str
    score:   float
    reasons: list[str]
    roles:   list[str]

class SuggestResponse(BaseModel):
    picks: list[HeroSuggestion]
