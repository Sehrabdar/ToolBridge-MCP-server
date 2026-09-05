"""Database health check.

Provides a lightweight connectivity probe that can be called from the
``/health`` endpoint or at application startup.
"""

from __future__ import annotations

from sqlalchemy import text

from toolbridge.db.engine import get_engine
from toolbridge.logging import get_logger

logger = get_logger(__name__)


async def check_db_health() -> bool:
    """Execute a trivial query to verify database connectivity.

    Returns:
        True if the database is reachable, False otherwise.
    """
    engine = get_engine()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.debug("db.health.ok")
        return True
    except Exception:
        logger.exception("db.health.failed")
        return False
