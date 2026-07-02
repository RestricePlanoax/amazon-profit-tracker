from __future__ import annotations

import unittest

from app.core.config import Settings


def build_settings(**overrides) -> Settings:
    payload = {
        "app_name": "Test API",
        "database_url": None,
        "postgres_host": None,
        "postgres_port": None,
        "postgres_user": None,
        "postgres_password": None,
        "postgres_database": None,
        "postgres_url_non_pooling": None,
        "postgres_url": None,
        "postgres_prisma_url": None,
        "jwt_secret": "test-secret",
        "access_token_expire_minutes": 60,
        "upload_dir": ".",
        "cors_origins": "http://localhost:3000",
        "debug_admin_token": None,
    }
    payload.update(overrides)
    return Settings.model_construct(**payload)


class DatabaseConfigResolutionTest(unittest.TestCase):
    def test_prefers_database_url_over_other_candidates(self) -> None:
        settings = build_settings(
            database_url="postgres://user:pass@primary.example.com:5432/app_db",
            postgres_url_non_pooling="postgres://user:pass@secondary.example.com:5432/other_db",
        )

        resolved = settings.resolved_database_config

        self.assertEqual(resolved.source, "DATABASE_URL")
        self.assertEqual(
            resolved.url,
            "postgresql+psycopg://user:pass@primary.example.com:5432/app_db",
        )
        self.assertEqual(resolved.host, "primary.example.com")
        self.assertEqual(resolved.database, "app_db")

    def test_prefers_non_pooling_url_when_database_url_missing(self) -> None:
        settings = build_settings(
            postgres_url_non_pooling="postgresql://user:pass@nonpool.example.com:5432/profit_db?sslmode=require",
            postgres_url="postgresql://user:pass@pool.example.com:6543/profit_db?sslmode=require",
        )

        resolved = settings.resolved_database_config

        self.assertEqual(resolved.source, "POSTGRES_URL_NON_POOLING")
        self.assertEqual(resolved.host, "nonpool.example.com")
        self.assertEqual(resolved.database, "profit_db")
        self.assertEqual(resolved.sslmode, "require")

    def test_builds_url_from_split_env_vars_and_encodes_password(self) -> None:
        settings = build_settings(
            postgres_host="db.example.supabase.co",
            postgres_port=5432,
            postgres_user="postgres",
            postgres_password="sp ace:@!",
            postgres_database="postgres",
        )

        resolved = settings.resolved_database_config

        self.assertEqual(
            resolved.source,
            "POSTGRES_HOST/POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DATABASE[/POSTGRES_PORT]",
        )
        self.assertIn("sp%20ace%3A%40%21", resolved.url)
        self.assertEqual(resolved.host, "db.example.supabase.co")
        self.assertEqual(resolved.database, "postgres")
        self.assertEqual(resolved.sslmode, "require")


if __name__ == "__main__":
    unittest.main()
