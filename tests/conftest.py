"""Shared pytest fixtures and configuration."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# ---------------------------------------------------------------------------
# Ensure a valid DATABASE_URL is available for unit tests so that Settings
# can be instantiated.  Integration tests may override this with a real URL.
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://toolbridge:toolbridge@localhost:5433/toolbridge_test",
)


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Set required environment variables for every test.

    Uses monkeypatch so values are restored after each test.  Also clears
    the lru_cache on get_settings() / get_engine() so each test gets a
    fresh settings object derived from the patched environment.
    """
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    # Clear caches so tests are isolated
    from toolbridge.config.settings import get_settings
    from toolbridge.db.engine import get_engine

    get_settings.cache_clear()
    get_engine.cache_clear()

    yield

    # Re-clear after the test so subsequent tests start clean
    get_settings.cache_clear()
    get_engine.cache_clear()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Return an httpx AsyncClient pointed at the FastAPI app.

    Uses ASGITransport so no real HTTP server is required.
    """
    from toolbridge.server.app import create_app

    _app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=_app),
        base_url="http://test",
    ) as client:
        yield client
