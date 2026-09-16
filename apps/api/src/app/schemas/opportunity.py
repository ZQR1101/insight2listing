"""API schemas for opportunity cards (plan section 16.9)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import OpportunityCardStatus


class OpportunityCardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    product_id: uuid.UUID
    title: str
    target_audience: str | None
    use_cases: list[str] | None
    competitor_gaps: list[str] | None
    differentiation_ideas: list[str] | None
    keywords: list[str] | None
    opportunity_score: float | None
    dimension_scores: dict[str, float | None] | None
    score_version: str | None
    confidence: float | None
    missing_dimensions: list[str] | None
    risk_flags: list[str] | None
    status: OpportunityCardStatus
    created_at: datetime


class OpportunityCardList(BaseModel):
    items: list[OpportunityCardRead]
    total: int
