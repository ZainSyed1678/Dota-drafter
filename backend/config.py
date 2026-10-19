from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    MODEL_DIR: str = os.path.join(os.path.dirname(__file__), "model")
    DATABASE_URL: Optional[str] = None
    PREDICTION_ENGINE: str = "combined"  # "combined", "ml", or "heuristic"
    TELEGRAM_TOKEN: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
