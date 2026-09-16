"""Insight2Listing API application root.

Wires routers under ``/api/v1`` and exposes OpenAPI docs. Nothing here reads,
logs or forwards API keys to the client (plan section 18.2).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select

from app.api import (
    facts,
    health,
    imports,
    insights,
    listings,
    opportunity_cards,
    products,
    projects,
    reviews,
)
from app.core.config import get_settings
from app.core.db import get_session_factory
from app.models.identity import Workspace

settings = get_settings()


async def _ensure_default_workspace() -> None:
    """Seed a single default workspace for the standalone local deployment."""
    async with get_session_factory()() as session:
        exists = (await session.execute(select(Workspace).limit(1))).scalar_one_or_none()
        if exists is None:
            session.add(Workspace(name="Default Workspace"))
            await session.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await _ensure_default_workspace()
    yield


app = FastAPI(
    title="Insight2Listing API",
    version="0.1.0",
    description="Evidence-grounded market insight, opportunity validation and Listing workflows.",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(projects.router)
app.include_router(imports.router)
app.include_router(products.router)
app.include_router(reviews.router)
app.include_router(insights.router)
app.include_router(opportunity_cards.router)
app.include_router(facts.router)
app.include_router(listings.router)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"name": settings.app_name, "docs": "/docs"}
