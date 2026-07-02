from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://postgres:postgres@localhost:5432/amazon_profit_tracker"
)


@dataclass(frozen=True)
class DatabaseRuntimeConfig:
    source: str
    url: str
    host: str | None
    database: str | None
    scheme: str
    sslmode: str | None


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


def _build_split_database_url(
    *,
    host: str,
    user: str,
    password: str,
    database: str,
    port: int | None,
) -> str:
    encoded_user = quote(user, safe="")
    encoded_password = quote(password, safe="")
    resolved_port = port or 5432
    return (
        f"postgresql+psycopg://{encoded_user}:{encoded_password}"
        f"@{host}:{resolved_port}/{database}?sslmode=require"
    )


def _build_runtime_config(source: str, url: str) -> DatabaseRuntimeConfig:
    normalized_url = _normalize_database_url(url)
    parsed = urlsplit(normalized_url)
    query = parse_qs(parsed.query)
    database_name = parsed.path.lstrip("/") or None
    sslmode = query.get("sslmode", [None])[0]
    return DatabaseRuntimeConfig(
        source=source,
        url=normalized_url,
        host=parsed.hostname,
        database=database_name,
        scheme=parsed.scheme,
        sslmode=sslmode,
    )


class Settings(BaseSettings):
    app_name: str = "Amazon Seller Profit Tracker API"
    database_url: str | None = None
    postgres_host: str | None = None
    postgres_port: int | None = None
    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_database: str | None = None
    postgres_url_non_pooling: str | None = None
    postgres_url: str | None = None
    postgres_prisma_url: str | None = None
    jwt_secret: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24
    upload_dir: Path = BACKEND_DIR / "storage" / "uploads"
    cors_origins: str = "http://localhost:3000"
    debug_admin_token: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @cached_property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @cached_property
    def resolved_database_config(self) -> DatabaseRuntimeConfig:
        constructed_postgres_url = None
        if all(
            [
                self.postgres_host,
                self.postgres_user,
                self.postgres_password,
                self.postgres_database,
            ]
        ):
            constructed_postgres_url = _build_split_database_url(
                host=self.postgres_host,
                user=self.postgres_user,
                password=self.postgres_password,
                database=self.postgres_database,
                port=self.postgres_port,
            )

        candidates = [
            ("DATABASE_URL", self.database_url),
            ("POSTGRES_URL_NON_POOLING", self.postgres_url_non_pooling),
            (
                "POSTGRES_HOST/POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DATABASE[/POSTGRES_PORT]",
                constructed_postgres_url,
            ),
            ("POSTGRES_URL", self.postgres_url),
            ("POSTGRES_PRISMA_URL", self.postgres_prisma_url),
            ("DEFAULT_DATABASE_URL", DEFAULT_DATABASE_URL),
        ]
        for source, candidate in candidates:
            if candidate and candidate.strip():
                return _build_runtime_config(source, candidate)

        return _build_runtime_config("DEFAULT_DATABASE_URL", DEFAULT_DATABASE_URL)

    @cached_property
    def resolved_database_url(self) -> str:
        return self.resolved_database_config.url

    @cached_property
    def database_log_context(self) -> dict[str, str]:
        config = self.resolved_database_config
        return {
            "source": config.source,
            "host": config.host or "unknown",
            "database": config.database or "unknown",
            "scheme": config.scheme,
            "sslmode": config.sslmode or "default",
        }


settings = Settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
