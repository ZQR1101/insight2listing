"""API schemas for the product facts centre (plan sections 6.6, 11, 16.6)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import FactStatus, FactType, WorkflowState


class ProductFactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    fact_type: FactType
    value: str
    unit: str | None
    source: str | None
    verification_status: FactStatus
    verified_by: str | None
    verified_at: datetime | None
    expires_at: datetime | None
    created_at: datetime


class ProductFactCreate(BaseModel):
    fact_type: FactType
    value: str = Field(min_length=1, max_length=2000)
    unit: str | None = Field(default=None, max_length=32)
    source: str | None = Field(default=None, max_length=255)


class ProductFactStatusUpdate(BaseModel):
    status: FactStatus = Field(description="user_confirmed | document_confirmed | rejected")


class FactList(BaseModel):
    items: list[ProductFactRead]
    total: int


class FactsConfirmResult(BaseModel):
    project_id: uuid.UUID
    status: WorkflowState
    confirmed_facts: int
