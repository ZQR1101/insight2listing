"""Comment insights and their evidence.

See plan sections 16.7 (Insight) and 16.8 (Evidence). Every insight carries
scored dimensions (frequency, severity, rating impact, recency, cross-competitor
breadth, confidence) and is backed by one or more :class:`Evidence` rows so its
claims stay attributable to review excerpts.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import CoreMixin


class Insight(CoreMixin, Base):
    __tablename__ = "insights"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("product_candidates.id"), nullable=True, index=True
    )
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment: Mapped[str] = mapped_column(String(16), default="neutral", nullable=False)
    frequency: Mapped[int] = mapped_column(default=0, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="low", nullable=False)
    rating_impact: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    recency_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    cross_competitor_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="generated", nullable=False, index=True
    )


class Evidence(CoreMixin, Base):
    __tablename__ = "evidence"

    insight_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("insights.id"), nullable=False, index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(48), nullable=False)
    source_entity_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    support_strength: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
