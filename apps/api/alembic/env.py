"""Alembic environment.

Uses a synchronous engine derived from the async ``DATABASE_URL`` (psycopg
replaces ``postgresql+asyncpg``-style drivers), consistent with the models.
"""

from __future__ import annotations

import asyncio
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from app.core.db import Base
import app.models  # noqa: F401  (register models on Base.metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Build a URL string the configured engine dialect can use. Models run on
# psycopg, so anything else (e.g. a +asyncpg driver) is normalised to psycopg.
_RAW = get_settings().database_url
_SYNC_URL = _RAW if ".psycopg:" in _RAW or _RAW.startswith("postgresql+psycopg:") else _RAW.replace(
    "+asyncpg", "+psycopg"
)
config.set_main_option("sqlalchemy.url", _SYNC_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL, not execute)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async engine created from the config URL."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    if sys.platform == "win32":  # psycopg async requires a selector event loop
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()