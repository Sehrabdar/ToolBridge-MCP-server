"""Alembic migration environment.

Configured to:
- Read DATABASE_URL from the ToolBridge settings (environment variable).
- Support async connections via asyncpg.
- Support autogenerate against SQLAlchemy models (target_metadata set to
  Base.metadata once models are introduced in a future phase).

Usage::

    uv run alembic upgrade head
    uv run alembic revision --autogenerate -m "describe your change"
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ---------------------------------------------------------------------------
# Alembic config object — provides access to alembic.ini values
# ---------------------------------------------------------------------------
config = context.config

# Interpret the ini file for stdlib logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Model metadata for autogenerate support
#
# Once SQLAlchemy ORM models are introduced (Phase 3+), import Base here:
#   from toolbridge.db.models import Base
#   target_metadata = Base.metadata
#
# Until then, autogenerate will produce empty migrations.
# ---------------------------------------------------------------------------
target_metadata = None

# ---------------------------------------------------------------------------
# Override sqlalchemy.url with DATABASE_URL from settings
# ---------------------------------------------------------------------------
from toolbridge.config import get_settings  # noqa: E402

_settings = get_settings()
config.set_main_option("sqlalchemy.url", _settings.async_database_url)


# ---------------------------------------------------------------------------
# Offline migration mode
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (SQL script output, no DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migration mode (async)
# ---------------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async engine (required for asyncpg driver)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a live database."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
