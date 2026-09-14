"""Data sources, their license scope and import batches.

``SourceRecord`` implements plan section 16.12 (source, license, observed time,
payload hash). ``ImportBatch`` tracks a single file import and its report.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import CoreMixin


class SourceRecord(CoreMixin, Base):
    __tablename__ = "sources"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(String(32), default="user_upload", nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    license: Mapped[str | None] = mapped_column(String(255), nullable=True)
    usage_scope: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_attested: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_payload_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)


class ImportBatch(CoreMixin, Base):
    __tablename__ = "import_batches"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id"), nullable=False, index=True
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("sources.id"), nullable=True
    )
    target: Mapped[str] = mapped_column(String(32), nullable=False)
    source_file_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    #: Human/machine readable import report (counts, errors, warnings).
    report: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
