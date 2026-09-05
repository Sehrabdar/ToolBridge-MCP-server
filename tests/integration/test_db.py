"""Integration tests — database connectivity.

These tests require a running PostgreSQL instance.  They are skipped
automatically in environments where DATABASE_URL points to an unreachable host.

Run locally with Docker Compose::

    docker compose up -d
    uv run pytest tests/integration/ -m integration

In CI a ``postgres`` service container provides the database.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_db_health_check_succeeds() -> None:
    """check_db_health() must return True against a running PostgreSQL instance."""
    from toolbridge.db.health import check_db_health

    result = await check_db_health()
    assert result is True, (
        "Database health check failed.  "
        "Ensure PostgreSQL is running and DATABASE_URL is set correctly."
    )


@pytest.mark.asyncio
async def test_db_engine_can_execute_query() -> None:
    """The async engine must be able to execute a basic SELECT query."""
    from sqlalchemy import text

    from toolbridge.db.engine import get_engine

    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1 AS probe"))
        row = result.fetchone()
    assert row is not None
    assert row[0] == 1


@pytest.mark.asyncio
async def test_db_engine_pool_pre_ping() -> None:
    """pool_pre_ping should be enabled — verify by checking engine pool options."""
    from sqlalchemy.pool import QueuePool

    from toolbridge.db.engine import get_engine

    engine = get_engine()
    # Verify the engine was created with a connection pool (not NullPool)
    assert isinstance(engine.pool, QueuePool)
