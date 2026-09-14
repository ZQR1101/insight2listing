"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.api.deps import SessionDep
from app.core.config import get_settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(session: SessionDep) -> HealthResponse:
    settings = get_settings()
    try:
        await session.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "unreachable"
    if database != "ok":
        raise HTTPException(status_code=503, detail="database unreachable")
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        env=settings.app_env,
        locale=settings.app_locale,
        database=database,
    )
