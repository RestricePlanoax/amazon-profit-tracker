from __future__ import annotations

from functools import cached_property
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://postgres:postgres@localhost:5432/amazon_profit_tracker"
)


def _normalize_database_url(value: str) -> str:
    raw_value = value.strip()
    if not raw_value:
        return raw_value

    if raw_value.startswith("postgresql+psycopg://"):
        return raw_value

    parts = urlsplit(raw_value)
    if parts.scheme in {"postgres", "postgresql"}:
        return urlunsplit(("postgresql+psycopg", parts.netloc, parts.path, parts.query, parts.fragment))

    return raw_value


class Settings(BaseSettings):
    app_name: str = "Amazon Seller Profit Tracker API"
    database_url: str | None = None
    postgres_url_non_pooling: str | None = None
    postgres_url: str | None = None
    postgres_prisma_url: str | None = None
    jwt_secret: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24
    upload_dir: Path = BACKEND_DIR / "storage" / "uploads"
    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @cached_property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @cached_property
    def resolved_database_url(self) -> str:
        candidates = [
            self.database_url,
            self.postgres_url_non_pooling,
            self.postgres_url,
            self.postgres_prisma_url,
            DEFAULT_DATABASE_URL,
        ]
        for candidate in candidates:
            if candidate and candidate.strip():
                return _normalize_database_url(candidate)

        return DEFAULT_DATABASE_URL


settings = Settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
