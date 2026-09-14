"""API schemas for data import (plan section 6.2, 8.4)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import ImportStatus, ImportTarget


class ImportPreviewRequest(BaseModel):
    """Metadata for a preview request (file is uploaded via multipart)."""

    target: ImportTarget
    source_name: str | None = None
    license: str | None = None
    usage_scope: str | None = None


class PreviewColumn(BaseModel):
    source_field: str
    detected_target: str | None = None
    sample_values: list[str] = Field(default_factory=list)


class ImportPreviewResponse(BaseModel):
    target: ImportTarget
    row_count: int
    columns: list[PreviewColumn]
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class FieldMapping(BaseModel):
    source_field: str
    target_field: str


class ImportCreate(BaseModel):
    """Metadata for a full import (file uploaded via multipart)."""

    target: ImportTarget
    source_name: str | None = None
    source_url: str | None = None
    license: str | None = None
    usage_scope: str | None = None
    observed_at: datetime | None = None
    user_attested: str | None = None
    mapping: list[FieldMapping] = Field(default_factory=list)


class ImportReport(BaseModel):
    target: ImportTarget
    rows_total: int = 0
    rows_valid: int = 0
    rows_invalid: int = 0
    imported: int = 0
    skipped_duplicates: int = 0
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ImportBatchRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    source_id: uuid.UUID | None
    target: ImportTarget
    source_file_name: str | None
    status: ImportStatus
    report: ImportReport | None
    finished_at: datetime | None
    created_at: datetime
