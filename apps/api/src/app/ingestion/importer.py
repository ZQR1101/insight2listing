"""Import orchestration.

``preview_import`` inspects a file without persisting anything.
``run_import`` parses, maps, normalises, deduplicates and persists records,
recording a :class:`SourceRecord` and an :class:`ImportBatch`. The caller owns
the transaction / commit and is responsible for audit logging.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import FreshnessStatus, ImportStatus, ImportTarget, WorkflowState
from app.ingestion import adapter_for
from app.ingestion.canonical import normalise_product, normalise_review
from app.ingestion.dedup import normalise_text, product_key, review_content_hash
from app.ingestion.errors import RowIssue, UnsupportedFileTypeError
from app.ingestion.fieldmap import apply_mapping
from app.models.catalog import ProductCandidate
from app.models.project import Project
from app.models.review import Review
from app.models.source import ImportBatch, SourceRecord


@dataclass(slots=True)
class ImportMetadata:
    target: ImportTarget
    source_name: str | None = None
    source_url: str | None = None
    license: str | None = None
    usage_scope: str | None = None
    observed_at: datetime | None = None
    user_attested: str | None = None
    #: explicit (source_header, canonical_field) pairs
    mapping: list[tuple[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class PreviewColumnInfo:
    source_field: str
    detected_target: str | None
    sample_values: list[str]


@dataclass(slots=True)
class ImportPreview:
    target: ImportTarget
    row_count: int
    columns: list[PreviewColumnInfo]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ImportResult:
    batch: ImportBatch
    rows_total: int = 0
    imported: int = 0
    skipped_duplicates: int = 0
    rows_invalid: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    loaded: ImportTarget | None = None


def _parse(
    data: bytes,
    filename: str,
    target: ImportTarget,
    max_bytes: int,
) -> tuple[list[dict[str, object]], dict[str, str], list[str]]:
    """Read a file and produce (rows, mapping, warnings)."""
    adapter = adapter_for(filename, max_bytes=max_bytes)
    rows: list[dict[str, object]] = adapter.read(data)
    headers = list({k for row in rows for k in row})
    mapping_result, warnings = apply_mapping(headers, target, [])
    mapping = mapping_result.mapping
    warnings.extend(f"column '{h}' not mapped" for h in mapping_result.unresolved)
    return rows, mapping, warnings


def preview_import(
    data: bytes,
    filename: str,
    target: ImportTarget,
    *,
    max_bytes: int | None = None,
) -> ImportPreview:
    """Build a preview of a file without writing anything to the database."""
    limit = max_bytes or get_settings().max_upload_bytes
    rows, mapping, warnings = _parse(data, filename, target, limit)
    columns: list[PreviewColumnInfo] = []
    for header, canonical in mapping.items():
        sample = [row.get(header) for row in rows[:5]]
        columns.append(
            PreviewColumnInfo(
                source_field=header,
                detected_target=canonical,
                sample_values=["" if v is None else str(v) for v in sample],
            )
        )
    all_headers = {h for row in rows for h in row}
    for header in all_headers - set(mapping):
        columns.append(
            PreviewColumnInfo(source_field=header, detected_target=None, sample_values=[])
        )
    return ImportPreview(
        target=target,
        row_count=len(rows),
        columns=columns,
        warnings=warnings,
    )


async def run_import(
    session: AsyncSession,
    *,
    project: Project,
    filename: str,
    data: bytes,
    meta: ImportMetadata,
) -> ImportResult:
    """Persist an import in one transaction and return its report."""
    settings = get_settings()

    source = SourceRecord(
        workspace_id=project.workspace_id,
        source_type="user_upload",
        source_name=meta.source_name or filename,
        source_url=meta.source_url,
        license=meta.license,
        usage_scope=meta.usage_scope,
        observed_at=meta.observed_at,
        imported_at=datetime.now(UTC),
        user_attested=meta.user_attested,
        raw_payload_hash=f"sha256:{sha256(data).hexdigest()}",
    )
    session.add(source)
    await session.flush()

    batch = ImportBatch(
        project_id=project.id,
        source_id=source.id,
        target=meta.target.value,
        source_file_name=filename,
        status=ImportStatus.PROCESSING.value,
    )
    session.add(batch)
    await session.flush()

    result = ImportResult(batch=batch, loaded=meta.target)
    try:
        rows, mapping, warnings = _parse(data, filename, meta.target, settings.max_upload_bytes)
    except UnsupportedFileTypeError as exc:
        _fail(batch, [str(exc)])
        return result

    result.warnings.extend(warnings)
    result.rows_total = len(rows)

    if meta.target is ImportTarget.PRODUCTS:
        result.imported += await _import_products(session, project, source, rows, mapping, result)
    else:
        result.imported += await _import_reviews(session, project, source, rows, mapping, result)

    _complete(project, batch, result)
    return result


def _fail(batch: ImportBatch, errors: list[str]) -> None:
    batch.status = ImportStatus.FAILED.value
    batch.report = {"errors": errors, "imported": 0, "skipped_duplicates": 0}


def _complete(project: Project, batch: ImportBatch, result: ImportResult) -> None:
    batch.status = ImportStatus.COMPLETED.value
    batch.finished_at = datetime.now(UTC)
    batch.report = {
        "rows_total": result.rows_total,
        "rows_invalid": result.rows_invalid,
        "imported": result.imported,
        "skipped_duplicates": result.skipped_duplicates,
        "errors": result.errors,
        "warnings": result.warnings,
    }
    if project.status == WorkflowState.DRAFT:
        project.status = WorkflowState.DATA_IMPORTED.value


async def _existing_product_keys(session: AsyncSession, project: Project) -> set[str]:
    products = (
        await session.execute(
            select(ProductCandidate).where(ProductCandidate.project_id == project.id)
        )
    ).scalars()
    keys: set[str] = set()
    for product in products:
        if product.external_id:
            keys.add(f"external:{product.external_id}")
        else:
            keys.add(
                f"title:{normalise_text(product.title)}|{normalise_text(product.brand or '')}"
            )
    return keys


async def _import_products(
    session: AsyncSession,
    project: Project,
    source: SourceRecord,
    rows: list[dict[str, object]],
    mapping: dict[str, str],
    result: ImportResult,
) -> int:
    existing_keys = await _existing_product_keys(session, project)
    seen: set[str] = set()
    imported = 0
    for idx, row in enumerate(rows, start=1):
        canonical, issues = normalise_product(row, mapping, idx)
        result.errors.extend(_describe(issue) for issue in issues)
        if canonical is None:
            result.rows_invalid += 1
            continue
        key = product_key(canonical)
        if key in seen or key in existing_keys:
            result.skipped_duplicates += 1
            continue
        seen.add(key)
        existing_keys.add(key)
        session.add(
            ProductCandidate(
                project_id=project.id,
                source_id=source.id,
                external_id=canonical.external_id,
                category=canonical.category,
                title=canonical.title,
                brand=canonical.brand,
                currency=canonical.currency or "USD",
                rating=canonical.rating,
                review_count=canonical.review_count,
                observed_at=canonical.observed_at,
                freshness=_freshness(source, canonical.price, canonical.observed_at),
            )
        )
        imported += 1
    return imported


async def _import_reviews(
    session: AsyncSession,
    project: Project,
    source: SourceRecord,
    rows: list[dict[str, object]],
    mapping: dict[str, str],
    result: ImportResult,
) -> int:
    existing_hashes = set(
        (
            await session.execute(
                select(Review.content_hash).where(Review.project_id == project.id)
            )
        )
        .scalars()
        .all()
    )
    products: dict[str, uuid.UUID] = {}
    for product in (
        await session.execute(
            select(ProductCandidate).where(ProductCandidate.project_id == project.id)
        )
    ).scalars():
        if product.external_id:
            products[product.external_id] = product.id

    seen: set[str] = set()
    imported = 0
    for idx, row in enumerate(rows, start=1):
        canonical, issues = normalise_review(row, mapping, idx)
        result.errors.extend(_describe(issue) for issue in issues)
        if canonical is None:
            result.rows_invalid += 1
            continue
        digest = review_content_hash(canonical)
        if digest in seen or digest in existing_hashes:
            result.skipped_duplicates += 1
            continue
        seen.add(digest)
        existing_hashes.add(digest)
        session.add(
            Review(
                project_id=project.id,
                product_id=(
                    products.get(canonical.product_external_id)
                    if canonical.product_external_id
                    else None
                ),
                source_id=source.id,
                external_review_id=canonical.external_review_id,
                rating=canonical.rating,
                title=canonical.title,
                body=canonical.body,
                language=canonical.language,
                verified_purchase=canonical.verified_purchase,
                reviewed_at=canonical.reviewed_at,
                content_hash=digest,
            )
        )
        imported += 1
    return imported


def _freshness(
    source: SourceRecord, price: Decimal | None, observed_at: datetime | None
) -> dict[str, object]:
    """Price observation metadata (plan section 8.5)."""
    return {
        "value": str(price) if price is not None else None,
        "source": source.source_type,
        "observed_at": observed_at.isoformat() if observed_at else None,
        "source_updated_at": None,
        "freshness_status": FreshnessStatus.UNKNOWN.value,
        "license_ref": source.license,
        "raw_payload_hash": source.raw_payload_hash,
    }


def _describe(issue: RowIssue) -> str:
    field_part = f"::{issue.field}" if issue.field else ""
    return f"row {issue.row_number}{field_part}: {issue.issue}"
