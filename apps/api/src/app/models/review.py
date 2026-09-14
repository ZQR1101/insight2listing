"""Reviews, the core input for insight generation.

See plan section 16.5. A deterministic ``content_hash`` enables idempotent
imports (deduplication across file uploads).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import CoreMixin


class Review(CoreMixin, Base):
    __tablename__ = "reviews"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("product_candidates.id"), nullable=True, index=True
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("sources.id"), nullable=True
    )
    external_review_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rating: Mapped[int | None] = mapped_column(nullable=True)
    title: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    verified_purchase: Mapped[bool | None] = mapped_column(nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    #: sha256 of the canonical body, used for deduplication.
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
