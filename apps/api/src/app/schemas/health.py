"""Health / generic API schemas."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str
    env: str
    locale: str
    database: str = "not_checked"


class ErrorResponse(BaseModel):
    detail: str
