"""
Application settings — loaded once at startup via Pydantic Settings.
All values come from environment variables or the .env file.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file: backend/src/api/config.py → root/.env
_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM
    groq_api_key: str

    # Literature search (both keys are optional — missing key = lower rate limit)
    semantic_scholar_api_key: str = ""
    ncbi_api_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_scientist"

    # Cache
    redis_url: str = "redis://localhost:6379"

    # App
    app_env: str = "development"          # "development" | "production"
    log_level: str = "INFO"
    cors_origins: list[str] = ["*"]       # tighten for production


@lru_cache
def get_settings() -> Settings:
    return Settings()
