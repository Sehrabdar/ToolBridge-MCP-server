"""Centralized application settings.

All configuration is read from environment variables (or a ``.env`` file in
development).  Never scatter ``os.getenv(...)`` calls throughout the
codebase — import ``get_settings()`` instead.
"""

from __future__ import annotations

import functools
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from environment variables.

    Phase 1 fields only.  Future phases will add:
      - GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET  (Phase 6 — OAuth)
      - JWT_SECRET                                (Phase 6 — auth)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Silently ignore unknown env vars — safe for forward-compat
    )

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    app_env: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    database_url: str  # Required — e.g. postgresql+asyncpg://user:pass@host/db

    # ------------------------------------------------------------------ #
    # Validators
    # ------------------------------------------------------------------ #
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure DATABASE_URL uses an async-compatible driver."""
        if not v.startswith(("postgresql+asyncpg://", "postgresql://", "postgres://")):
            raise ValueError(
                "DATABASE_URL must be a PostgreSQL connection string "
                "(e.g. postgresql+asyncpg://user:pass@host/db)"
            )
        return v

    @property
    def is_production(self) -> bool:
        """Return True when running in production."""
        return self.app_env == "production"

    @property
    def async_database_url(self) -> str:
        """Return DATABASE_URL normalised to use the asyncpg driver."""
        url = self.database_url
        if url.startswith("postgresql://") or url.startswith("postgres://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1).replace(
                "postgres://", "postgresql+asyncpg://", 1
            )
        return url


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton.

    Uses ``lru_cache`` so that the environment is only read once per process.
    In tests, call ``get_settings.cache_clear()`` before monkeypatching env vars.
    """
    return Settings()  # type: ignore[call-arg]  # pydantic-settings reads from environment
