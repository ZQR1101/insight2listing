"""API schemas for catalog products, variants and reviews."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    external_id: str | None
    category: str | None
    title: str
    brand: str | None
    currency: str
    rating: float | None
    review_count: int | None
    observed_at: datetime | None
    freshness: dict[str, object] | None


class VariantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    sku: str | None
    external_id: str | None
    color: str | None
    size: str | None
    package_quantity: int | None
    status: str


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    product_id: uuid.UUID | None
    external_review_id: str | None
    rating: int | None
    title: str | None
    body: str
    language: str | None
    verified_purchase: bool | None
    reviewed_at: datetime | None
    content_hash: str | None


class ProductList(BaseModel):
    items: list[ProductRead]
    total: int


class ReviewList(BaseModel):
    items: list[ReviewRead]
    total: int


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_type: str
    source_name: str | None
    source_url: str | None
    license: str | None
    usage_scope: str | None
    observed_at: datetime | None
    imported_at: datetime | None
    expires_at: datetime | None
    user_attested: str | None
    raw_payload_hash: str | None
