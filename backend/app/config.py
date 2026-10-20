import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = "production"  # "development", "staging", "production"
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    MODEL_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model")
    DATABASE_URL: Optional[str] = None
    PREDICTION_ENGINE: str = "combined"  # "combined", "ml", or "heuristic"
    TELEGRAM_TOKEN: Optional[str] = None
    ADMIN_API_KEY: Optional[str] = None

    CORS_ORIGINS: List[str] = ["*"]
    CACHE_SIZE: int = 1024
    RATE_LIMIT_PER_MINUTE: int = 120

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
