"""Application configuration loaded from environment variables / .env file."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Eventora AI"
    environment: str = "development"
    version: str = "1.0.0"

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Empty -> use local SQLite file. Set to a Postgres URL for production.
    database_url: str = ""

    ai_provider: str = "none"  # openai | anthropic | none
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-latest"
    ai_base_url: str = "https://api.openai.com/v1"
    ai_timeout_seconds: int = 60

    ml_model_dir: str = "ml_artifacts"

    @property
    def model_dir(self) -> Path:
        path = Path(self.ml_model_dir)
        if not path.is_absolute():
            path = BACKEND_DIR / path
        return path

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return origins or ["http://localhost:3000"]

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            # Render and several other hosts provide postgres:// URLs. Use
            # Psycopg 3 explicitly so PostgreSQL works without psycopg2.
            if self.database_url.startswith("postgres://"):
                return self.database_url.replace(
                    "postgres://", "postgresql+psycopg://", 1
                )
            if self.database_url.startswith("postgresql://"):
                return self.database_url.replace(
                    "postgresql://", "postgresql+psycopg://", 1
                )
            return self.database_url
        return f"sqlite:///{(BACKEND_DIR / 'eventora.db').as_posix()}"

    @property
    def ai_available(self) -> bool:
        if self.ai_provider == "openai":
            return bool(self.openai_api_key)
        if self.ai_provider == "anthropic":
            return bool(self.anthropic_api_key)
        return False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
