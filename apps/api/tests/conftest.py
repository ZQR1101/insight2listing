"""Shared pytest fixtures.

Tests use a dedicated Postgres database (``insight2listing_test``) derived from
``DATABASE_URL``, so test runs never touch dev/application data. Tables are
created once per session via ``Base.metadata.create_all`` and truncated before
each test for isolation.
"""

from __future__ import annotations

import asyncio
import os
import sys

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://insight2listing:insight2listing@localhost:5433/insight2listing",
)

BASE_URL = os.environ["DATABASE_URL"]
TEST_URL = f"{BASE_URL.rsplit('/', 1)[0]}/insight2listing_test"
os.environ["DATABASE_URL"] = TEST_URL


def _ensure_test_database() -> None:
    """Create the test database if it does not exist (best effort)."""
    import psycopg

    admin_url = BASE_URL.replace("postgresql+psycopg://", "postgresql://").rsplit("/", 1)[0] + "/postgres"
    db_name = TEST_URL.rsplit("/", 1)[1]
    conn = psycopg.connect(admin_url, autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if cur.fetchone() is None:
                cur.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        conn.close()


_ensure_test_database()


@pytest_asyncio.fixture(scope="session")
def event_loop_policy() -> asyncio.AbstractEventLoopPolicy:
    """Use a SelectorEventLoop on Windows so psycopg async can connect.

    The ProactorEventLoop (Windows default since Python 3.8) is not supported
    by psycopg's asyncio driver.
    """
    if sys.platform == "win32":
        return asyncio.WindowsSelectorEventLoopPolicy()
    return asyncio.DefaultEventLoopPolicy()


from app.core.db import Base, get_engine, reset_engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncEngine:
    reset_engine()
    engine_obj = get_engine()
    async with engine_obj.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.identity import Workspace

    async with AsyncSession(engine_obj) as session:
        exists = (await session.execute(select(Workspace).limit(1))).scalar_one_or_none()
        if exists is None:
            session.add(Workspace(name="Default Workspace"))
            await session.commit()
    yield engine_obj
    reset_engine()


@pytest_asyncio.fixture(autouse=True)
async def _clean_db(engine: AsyncEngine) -> AsyncEngine:
    tables = [t for t in Base.metadata.sorted_tables if t.name != "workspaces"]
    names = ", ".join(f'"{t.name}"' for t in tables)
    if names:
        async with engine.begin() as conn:
            await conn.execute(text(f"TRUNCATE TABLE {names} RESTART IDENTITY CASCADE"))
    return engine


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def create_project(client: AsyncClient, *, name: str = "Test Project") -> dict:
    """Create a project in the default workspace and return it."""
    ws = (await client.get("/api/v1/workspaces")).json()
    resp = await client.post(
        "/api/v1/projects", json={"workspace_id": ws["id"], "name": name}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
