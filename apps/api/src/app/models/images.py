"""Product images and generated creatives (plan sections 13, 16.11).

``ProductImage`` is a real product photo uploaded by the user (the only allowed
basis for a main image). ``CreativeAsset`` is a generated visual; it stores the
brief, prompt and engine used, the automated check outcomes, and a human review
status that gates downloads (plan section 13.7).
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import CoreMixin


class ProductImage(CoreMixin, Base):
    __tablename__ = "product_images"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("product_candidates.id"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_by: Mapped[str | None] = mapped_column(String(255), nullable=True)


class CreativeAsset(CoreMixin, Base):
    __tablename__ = "creatives"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("product_candidates.id"), nullable=False, index=True
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("product_variants.id"), nullable=True
    )
    asset_type: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(16), default="en-US", nullable=False)
    #: ids of ProductImage rows the asset was based on
    source_images: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    creative_brief: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    output_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    output_content_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    consistency_status: Mapped[str] = mapped_column(
        String(16), default="pending", nullable=False
    )
    compliance_status: Mapped[str] = mapped_column(
        String(16), default="pending", nullable=False
    )
    human_review_status: Mapped[str] = mapped_column(
        String(16), default="pending", nullable=False, index=True
    )
