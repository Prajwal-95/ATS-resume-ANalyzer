"""
Unit tests for database URL normalization in application configuration.

Covers:
- postgres://  -> postgresql+asyncpg://
- postgresql:// -> postgresql+asyncpg://
- postgresql+asyncpg:// -> unchanged (no double-prefix)
- SQLite and other dialects -> unchanged
- Empty string -> empty string
- settings.DATABASE_URL is normalized via the same settings interface
"""
import os

from app.config import _normalize_database_url, settings


class TestDatabaseUrlNormalization:
    def test_postgres_url_normalized(self):
        assert _normalize_database_url("postgres://user:pass@host:5432/db") == (
            "postgresql+asyncpg://user:pass@host:5432/db"
        )

    def test_postgresql_url_normalized(self):
        assert _normalize_database_url("postgresql://user:pass@host:5432/db") == (
            "postgresql+asyncpg://user:pass@host:5432/db"
        )

    def test_postgresql_asyncpg_url_unchanged(self):
        url = "postgresql+asyncpg://user:pass@host:5432/db"
        assert _normalize_database_url(url) == url

    def test_sqlite_url_preserved(self):
        url = "sqlite+aiosqlite:///./test.db"
        assert _normalize_database_url(url) == url

    def test_empty_url_preserved(self):
        assert _normalize_database_url("") == ""

    def test_settings_database_url_is_normalized(self):
        """settings.DATABASE_URL is the normalized form of the env value."""
        raw = os.getenv("DATABASE_URL", "")
        assert settings.DATABASE_URL == _normalize_database_url(raw)
