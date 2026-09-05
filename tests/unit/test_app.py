"""Unit tests for the FastAPI application layer (toolbridge.server.app)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Tests for GET /health — application + DB health check."""

    async def test_health_returns_200(self, async_client: AsyncClient) -> None:
        """Health endpoint must return HTTP 200."""
        response = await async_client.get("/health")
        assert response.status_code == 200

    async def test_health_returns_status_ok(self, async_client: AsyncClient) -> None:
        """Response body must contain ``{"status": "ok"}``."""
        response = await async_client.get("/health")
        body = response.json()
        assert body["status"] == "ok"

    async def test_health_returns_db_field(self, async_client: AsyncClient) -> None:
        """Response body must include a ``db`` field."""
        response = await async_client.get("/health")
        body = response.json()
        assert "db" in body

    async def test_health_db_field_valid_values(self, async_client: AsyncClient) -> None:
        """``db`` field must be either ``"ok"`` or ``"degraded"``."""
        response = await async_client.get("/health")
        body = response.json()
        assert body["db"] in ("ok", "degraded")

    async def test_health_content_type_json(self, async_client: AsyncClient) -> None:
        """Health endpoint must return JSON content type."""
        response = await async_client.get("/health")
        assert "application/json" in response.headers.get("content-type", "")


class TestAppCreation:
    """Tests for the application factory."""

    def test_create_app_returns_fastapi_instance(self) -> None:
        """create_app() must return a FastAPI instance without raising."""
        from fastapi import FastAPI

        from toolbridge.server.app import create_app

        _app = create_app()
        assert isinstance(_app, FastAPI)

    def test_app_title(self) -> None:
        """Application title must be 'ToolBridge'."""
        from toolbridge.server.app import create_app

        _app = create_app()
        assert _app.title == "ToolBridge"
