"""Async SQLAlchemy engine factory.

The engine is the single point of database connectivity for the application.
All database operations should be performed through sessions derived from
this engine.
"""

from __future__ import annotations

import functools

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from toolbridge.config import get_settings


@functools.lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Return the cached async SQLAlchemy engine.

    The engine is created once per process from ``DATABASE_URL``.  Tests that
    need a different database should call ``get_engine.cache_clear()`` and
    ``get_settings.cache_clear()`` before overriding environment variables.

    Returns:
        AsyncEngine: The SQLAlchemy async engine instance.
    """
    settings = get_settings()
    return create_async_engine(
        settings.async_database_url,
        echo=not settings.is_production,  # Log SQL in non-production environments
        pool_pre_ping=True,  # Verify connections before use
        pool_size=5,
        max_overflow=10,
    )
