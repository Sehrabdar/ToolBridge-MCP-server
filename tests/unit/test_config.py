"""Unit tests for application configuration (toolbridge.config.settings)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from toolbridge.config.settings import Settings, get_settings


class TestSettingsDefaults:
    def test_app_env_defaults_to_development(self) -> None:
        s = Settings(
            database_url="postgresql+asyncpg://u:p@localhost/db",
            github_token="test-token",
        )
        assert s.app_env == "development"

    def test_log_level_defaults_to_info(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        s = Settings(
            database_url="postgresql+asyncpg://u:p@localhost/db",
            github_token="test-token",
        )
        assert s.log_level == "INFO"

    def test_is_production_false_by_default(self) -> None:
        s = Settings(
            database_url="postgresql+asyncpg://u:p@localhost/db",
            github_token="test-token",
        )
        assert s.is_production is False


class TestSettingsValidation:
    """Test that invalid configuration is rejected."""

    def test_missing_database_url_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """DATABASE_URL is required; omitting it must raise ValidationError."""
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(ValidationError, match="database_url"):
            Settings(_env_file=None)  # type: ignore[call-arg]  # reads from environment

    def test_invalid_database_url_raises(self) -> None:
        """Non-PostgreSQL DATABASE_URL must be rejected."""
        with pytest.raises(ValidationError):
            Settings(database_url="sqlite:///local.db", github_token="test-token")

    def test_invalid_app_env_raises(self) -> None:
        """APP_ENV must be one of the allowed literals."""
        with pytest.raises(ValidationError):
            Settings(
                database_url="postgresql+asyncpg://u:p@localhost/db",
                app_env="unknown",  # type: ignore[arg-type]
                github_token="test-token",
            )

    def test_invalid_log_level_raises(self) -> None:
        """LOG_LEVEL must be one of the allowed literals."""
        with pytest.raises(ValidationError):
            Settings(
                database_url="postgresql+asyncpg://u:p@localhost/db",
                log_level="VERBOSE",  # type: ignore[arg-type]
                github_token="test-token",
            )


class TestSettingsValid:
    def test_production_env(self) -> None:
        s = Settings(
            database_url="postgresql+asyncpg://u:p@localhost/db",
            app_env="production",
            github_token="test-token",
        )
        assert s.is_production is True

    def test_staging_env(self) -> None:
        s = Settings(
            database_url="postgresql+asyncpg://u:p@localhost/db",
            app_env="staging",
            github_token="test-token",
        )
        assert s.is_production is False

    def test_async_database_url_normalisation_postgresql(self) -> None:
        s = Settings(
            database_url="postgresql://u:p@localhost/db",
            github_token="test-token",
        )
        assert s.async_database_url.startswith("postgresql+asyncpg://")

    def test_async_database_url_normalisation_postgres(self) -> None:
        s = Settings(
            database_url="postgres://u:p@localhost/db",
            github_token="test-token",
        )
        assert s.async_database_url.startswith("postgresql+asyncpg://")

    def test_async_database_url_already_asyncpg(self) -> None:
        url = "postgresql+asyncpg://u:p@localhost/db"
        s = Settings(database_url=url, github_token="test-token")
        assert s.async_database_url == url


class TestGetSettingsSingleton:
    """Test the get_settings() cached singleton behaviour."""

    def test_get_settings_returns_settings_instance(self) -> None:
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_is_cached(self) -> None:
        """Two calls must return the same object."""
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
