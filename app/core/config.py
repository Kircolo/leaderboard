from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LEADERBOARD_", env_file=".env", extra="ignore")

    app_name: str = "Global Gaming Leaderboard"
    environment: str = "local"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/leaderboard"
    redis_url: str = "redis://localhost:6379/0"
    default_leaderboard_limit: int = Field(default=10, ge=1, le=100)
    max_leaderboard_limit: int = Field(default=100, ge=1, le=500)
    default_context_window: int = Field(default=2, ge=1, le=10)
    max_context_window: int = Field(default=10, ge=1, le=50)
    request_timeout_seconds: int = Field(default=5, ge=1, le=60)
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()

