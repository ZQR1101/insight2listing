"""API schemas for comment insights (plan sections 9, 16.7/16.8)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import InsightStatus, Sentiment, Severity


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    insight_id: uuid.UUID
    evidence_type: str
    source_entity_id: str | None
    excerpt: str
    support_strength: float | None
    observed_at: datetime | None


class InsightRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    product_id: uuid.UUID | None
    topic: str
    summary: str | None
    sentiment: Sentiment
    frequency: int
    severity: Severity
    rating_impact: float | None
    recency_score: float | None
    cross_competitor_score: float | None
    confidence: float | None
    status: InsightStatus
    created_at: datetime


class InsightList(BaseModel):
    items: list[InsightRead]
    total: int


class InsightDetail(InsightRead):
    evidence: list[EvidenceRead] = Field(default_factory=list)


class InsightStatusUpdate(BaseModel):
    status: InsightStatus = Field(description="accepted | rejected | edited")


class InsightEdit(BaseModel):
    topic: str | None = None
    summary: str | None = None
    sentiment: Sentiment | None = None
    severity: Severity | None = None


class InsightGenerateResult(BaseModel):
    insights: int
    cards: int
    reviews_attributed: int
    reviews_skipped: int
