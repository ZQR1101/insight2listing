"""Data import endpoints (plan sections 6.2, 8.4, 18.4)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ActorDep, SessionDep
from app.audit.audit_logger import log_event
from app.core.enums import AuditAction, ImportStatus, ImportTarget
from app.ingestion.importer import (
    ImportMetadata,
    ImportPreview,
    preview_import,
    run_import,
)
from app.models.project import Project
from app.models.source import ImportBatch
from app.schemas.import_ import (
    FieldMapping,
    ImportBatchRead,
    ImportPreviewResponse,
    ImportReport,
    PreviewColumn,
)

router = APIRouter(prefix="/api/v1/projects/{project_id}/imports", tags=["imports"])


async def _get_project(session: SessionDep, project_id: uuid.UUID) -> Project:
    project = (
        await session.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    return project


def _parse_mapping(raw: str | None) -> list[tuple[str, str]]:
    if not raw:
        return []
    from pydantic import TypeAdapter

    adapter = TypeAdapter(list[FieldMapping])
    try:
        parsed = adapter.validate_json(raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"invalid mapping payload: {exc}") from exc
    return [(m.source_field, m.target_field) for m in parsed]


def _preview_schema(preview: ImportPreview) -> ImportPreviewResponse:
    return ImportPreviewResponse(
        target=preview.target,
        row_count=preview.row_count,
        columns=[
            PreviewColumn(
                source_field=c.source_field,
                detected_target=c.detected_target,
                sample_values=c.sample_values,
            )
            for c in preview.columns
        ],
        warnings=preview.warnings,
        errors=preview.errors,
    )


def _report_from_batch(batch: ImportBatch) -> ImportReport | None:
    report: dict[str, Any] | None = batch.report
    if not report:
        return None
    return ImportReport(
        target=ImportTarget(batch.target),
        rows_total=report.get("rows_total", 0),
        rows_valid=report.get("imported", 0),
        rows_invalid=report.get("rows_invalid", 0),
        imported=report.get("imported", 0),
        skipped_duplicates=report.get("skipped_duplicates", 0),
        errors=report.get("errors", []),
        warnings=report.get("warnings", []),
    )


async def _batch_read(session: AsyncSession, batch: ImportBatch) -> ImportBatchRead:
    await session.refresh(batch)
    return ImportBatchRead(
        id=batch.id,
        project_id=batch.project_id,
        source_id=batch.source_id,
        target=ImportTarget(batch.target),
        source_file_name=batch.source_file_name,
        status=ImportStatus(batch.status),
        report=_report_from_batch(batch),
        finished_at=batch.finished_at,
        created_at=batch.created_at,
    )


@router.post("/preview", response_model=ImportPreviewResponse)
async def preview(
    project_id: uuid.UUID,
    session: SessionDep,
    file: UploadFile = File(..., description="CSV, JSON or XLSX file"),
    target: str = Form(...),
    license: str | None = Form(None),
    usage_scope: str | None = Form(None),
) -> ImportPreviewResponse:
    await _get_project(session, project_id)
    data = await file.read()
    try:
        parsed_target = ImportTarget(target)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"invalid target: {target}") from exc
    preview_result = preview_import(data, file.filename or "upload", parsed_target)
    return _preview_schema(preview_result)


@router.post("", response_model=ImportBatchRead, status_code=status.HTTP_201_CREATED)
async def import_file(
    project_id: uuid.UUID,
    session: SessionDep,
    actor: ActorDep,
    file: UploadFile = File(..., description="CSV, JSON or XLSX file"),
    target: str = Form(...),
    source_name: str | None = Form(None),
    source_url: str | None = Form(None),
    license: str | None = Form(None),
    usage_scope: str | None = Form(None),
    observed_at: datetime | None = Form(None),
    user_attested: str | None = Form(None),
    mapping: str | None = Form(None),
) -> ImportBatchRead:
    project = await _get_project(session, project_id)
    try:
        parsed_target = ImportTarget(target)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"invalid target: {target}") from exc

    meta = ImportMetadata(
        target=parsed_target,
        source_name=source_name,
        source_url=source_url,
        license=license,
        usage_scope=usage_scope,
        observed_at=observed_at,
        user_attested=user_attested,
        mapping=_parse_mapping(mapping),
    )
    data = await file.read()
    result = await run_import(
        session,
        project=project,
        filename=file.filename or "upload",
        data=data,
        meta=meta,
    )

    action = (
        AuditAction.IMPORT_COMPLETED
        if result.batch.status == ImportStatus.COMPLETED.value
        else AuditAction.IMPORT_FAILED
    )
    await log_event(
        session,
        workspace_id=project.workspace_id,
        action=action,
        actor=actor,
        entity_type="import_batch",
        entity_id=str(result.batch.id),
        after={"target": parsed_target.value, "imported": result.imported},
    )
    await session.commit()
    return await _batch_read(session, result.batch)
