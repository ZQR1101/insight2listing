"""Catalog entities: product candidates and their variants.

See plan sections 16.3 (ProductCandidate) and 16.4 (ProductVariant). Price is
carried as an observation with freshness metadata (section 8.5).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import CoreMixin


class ProductCandidate(CoreMixin, Base):
    __tablename__ = "product_candidates"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id"), nullable=False, index=True
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("sources.id"), nullable=True
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    rating: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    review_count: Mapped[int | None] = mapped_column(nullable=True)
    observed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Freshness metadata for the price observation (plan section 8.5).
    freshness: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)


class ProductVariant(CoreMixin, Base):
    __tablename__ = "product_variants"

    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("product_candidates.id"), nullable=False, index=True
    )
    sku: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    color: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size: Mapped[str | None] = mapped_column(String(255), nullable=True)
    package_quantity: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
