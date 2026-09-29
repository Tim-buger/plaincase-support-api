from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Plaincase Support API"
    app_env: str = "development"
    log_level: str = "INFO"
    default_provider: str = "mock"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    request_timeout_seconds: float = Field(default=20, gt=0, le=120)
    max_retries: int = Field(default=2, ge=0, le=5)
    database_path: Path = Path("data/audit.db")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
