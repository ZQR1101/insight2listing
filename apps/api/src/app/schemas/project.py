"""API schemas for workspaces, projects and their lifecycle."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import Marketplace, WorkflowState


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime


class ProjectCreate(BaseModel):
    workspace_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    marketplace: Marketplace = Marketplace.AMAZON_US
    target_locale: str = "en-US"
    interface_locale: str = "zh-CN"
    currency: str = "USD"


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    marketplace: str
    target_locale: str
    interface_locale: str
    currency: str
    status: WorkflowState
    created_at: datetime
    updated_at: datetime


class ProjectStatusUpdate(BaseModel):
    status: WorkflowState


class ProjectList(BaseModel):
    items: list[ProjectRead]
    total: int
