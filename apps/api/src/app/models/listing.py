"""Listing versions (plan sections 12, 16.10).

Every generation creates a new immutable-ish row; regeneration never overwrites
an approved version (section 12.3). Bullet points carry their supporting fact /
insight ids so every selling point stays attributable, and the fact / rule
check reports are stored on the version they apply to.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import CoreMixin


class ListingVersion(CoreMixin, Base):
    __tablename__ = "listing_versions"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("product_candidates.id"), nullable=False, index=True
    )
    marketplace: Mapped[str] = mapped_column(String(32), default="amazon_us", nullable=False)
    locale: Mapped[str] = mapped_column(String(16), default="en-US", nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    #: [{text, fact_ids, insight_ids}]
    bullet_points: Mapped[list[dict[str, object]] | None] = mapped_column(JSONB, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    input_snapshot_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    input_snapshot: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False, index=True)
    fact_check: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    rule_check: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
