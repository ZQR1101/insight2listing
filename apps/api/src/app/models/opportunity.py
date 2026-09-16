"""Opportunity cards (plan section 16.9).

A card summarises why a product has (or lacks) opportunity: target audience,
use cases, competitor gaps, differentiation ideas, keywords, and an explainable
score with per-dimension breakdown, confidence and explicitly missing dimensions.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import CoreMixin


class OpportunityCard(CoreMixin, Base):
    __tablename__ = "opportunity_cards"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("product_candidates.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    use_cases: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    competitor_gaps: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    differentiation_ideas: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    opportunity_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    dimension_scores: Mapped[dict[str, float] | None] = mapped_column(JSONB, nullable=True)
    score_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    missing_dimensions: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    risk_flags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
