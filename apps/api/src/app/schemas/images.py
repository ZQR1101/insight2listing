"""API schemas for product images and creatives (plan sections 13, 16.11)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import AssetType, CheckStatus, ReviewStatus


class ProductImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    product_id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int
    width: int
    height: int
    checksum: str
    created_at: datetime


class ImageList(BaseModel):
    items: list[ProductImageRead]
    total: int


class CreativeGenerateRequest(BaseModel):
    asset_type: AssetType
    source_image_ids: list[str] = Field(default_factory=list)
    #: Deterministic text lines to typeset programmatically (not for main images).
    overlay_lines: list[str] = Field(default_factory=list)


class CreativeAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    asset_type: AssetType
    locale: str
    source_images: list[str] | None
    creative_brief: dict[str, object] | None
    prompt: str | None
    model: str | None
    size_bytes: int | None
    width: int | None
    height: int | None
    consistency_status: CheckStatus
    compliance_status: CheckStatus
    human_review_status: ReviewStatus
    created_at: datetime


class CreativeList(BaseModel):
    items: list[CreativeAssetRead]
    total: int
