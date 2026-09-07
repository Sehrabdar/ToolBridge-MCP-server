"""FastAPI application.

Phase 1 scope
-------------
This module defines the minimal FastAPI application.  In Phase 1 the only
route is ``GET /health``.

Future phases will add:
  - MCP Streamable HTTP transport endpoints   (Phase 2)
  - GitHub OAuth callback routes              (Phase 6)

Do NOT add OAuth or MCP routes here until those phases are implemented.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from toolbridge.config import get_settings
from toolbridge.db.health import check_db_health
from toolbridge.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler — startup and shutdown logic."""
    settings = get_settings()
    configure_logging(
        log_level=settings.log_level,
        production=settings.is_production,
    )
    logger.info(
        "toolbridge.starting",
        app_env=settings.app_env,
        log_level=settings.log_level,
    )
    yield
    logger.info("toolbridge.stopped")


def create_app() -> FastAPI:
    """Application factory — returns a configured FastAPI instance.

    Using a factory function (rather than a module-level ``app = FastAPI()``)
    makes the application easier to test and configure per-environment.

    Returns:
        FastAPI: The configured application instance.
    """
    _app = FastAPI(
        title="ToolBridge",
        description=(
            "Secure MCP Server for Authenticated Tool Execution. "
            "Exposes external tools to MCP-compatible clients with "
            "per-user authentication, authorisation, and audit logging."
        ),
        version="0.1.0",
        lifespan=lifespan,
        # Disable docs in production — re-enable when the API surface is stable
        docs_url=None if get_settings().is_production else "/docs",
        redoc_url=None if get_settings().is_production else "/redoc",
    )

    # ------------------------------------------------------------------ #
    # Routes — Phase 1
    # ------------------------------------------------------------------ #

    @_app.get(
        "/health",
        summary="Application health check",
        tags=["observability"],
        response_model=None,
    )
    async def health() -> JSONResponse:
        """Return the health status of the application and its dependencies.

        The ``db`` field reflects whether the database is reachable.
        A degraded database does NOT cause a non-200 response in Phase 1;
        the field is informational for monitoring systems.

        Returns:
            JSON body: ``{"status": "ok", "db": "ok" | "degraded"}``
        """
        db_ok = await check_db_health()
        return JSONResponse(
            content={
                "status": "ok",
                "db": "ok" if db_ok else "degraded",
            }
        )

    return _app


# Module-level app instance used by uvicorn / pytest
app = create_app()
