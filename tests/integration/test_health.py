"""Integration tests — health endpoint against a running application.

Requires PostgreSQL to be running so the ``db`` field can reflect ``"ok"``.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_health_db_ok_when_postgres_running(async_client: AsyncClient) -> None:
    """When PostgreSQL is reachable the health endpoint should report db=ok."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok", (
        "Expected db='ok' but got db='degraded'. "
        "Ensure PostgreSQL is running (docker compose up -d)."
    )
