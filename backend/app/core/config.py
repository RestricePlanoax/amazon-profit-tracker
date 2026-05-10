from __future__ import annotations

from functools import cached_property
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Amazon Seller Profit Tracker API"
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/amazon_profit_tracker"
    )
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


settings = Settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
