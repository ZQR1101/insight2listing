"""API schemas for the Listing workbench (plan sections 12, 16.10)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ListingStatus


class BulletRef(BaseModel):
    """A bullet point with the facts/insights it was built from (§12.3)."""

    text: str = Field(min_length=1, max_length=1000)
    fact_ids: list[str] = Field(default_factory=list)
    insight_ids: list[str] = Field(default_factory=list)


class ListingVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    product_id: uuid.UUID
    marketplace: str
    locale: str
    title: str
    bullet_points: list[BulletRef] | None
    description: str | None
    search_terms: str | None
    model: str | None
    prompt_version: str | None
    input_snapshot_id: str | None
    status: ListingStatus
    fact_check: dict[str, object] | None
    rule_check: dict[str, object] | None
    created_at: datetime


class ListingList(BaseModel):
    items: list[ListingVersionRead]
    total: int


class ListingEdit(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    bullet_points: list[BulletRef] | None = None
    description: str | None = Field(default=None, max_length=5000)
    search_terms: str | None = Field(default=None, max_length=1000)
