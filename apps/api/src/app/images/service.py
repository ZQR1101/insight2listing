"""Visual generation pipeline (plan section 13.4).

upload → creative brief → image engine → consistency check → deterministic
text overlay (never on a main image) → compliance check → human review.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.audit_logger import log_event
from app.core.config import get_settings
from app.core.enums import (
    AssetType,
    AuditAction,
    CheckStatus,
    InsightStatus,
    ReviewStatus,
    WorkflowState,
)
from app.facts.service import list_usable_facts
from app.images import checks
from app.images.brief import BriefInput, InsightBriefInput, build_brief
from app.images.engines import get_image_engine, image_dimensions, sniff_content_type
from app.images.overlay import apply_overlay
from app.images.storage import get_storage
from app.models.facts import ProductFact
from app.models.images import CreativeAsset, ProductImage
from app.models.insight import Insight
from app.models.project import Project
from app.workflows.transitions import advance_status

_ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg"}


class ImageUploadError(ValueError):
    """Base for upload problems (router maps to 422)."""


class RightsNotAttestedError(ImageUploadError):
    def __init__(self) -> None:
        super().__init__("usage rights must be attested before upload")


class ImageTooLargeError(ImageUploadError):
    def __init__(self, limit: int) -> None:
        super().__init__(f"image exceeds the {limit} byte limit")


class InvalidImageError(ImageUploadError):
    def __init__(self, report: checks.ImageCheckReport) -> None:
        self.issues = report.issues
        super().__init__("; ".join(i.issue for i in report.issues) or "invalid image")


class DuplicateImageError(ImageUploadError):
    def __init__(self, existing_id: uuid.UUID) -> None:
        self.existing_id = existing_id
        super().__init__("this image was already uploaded")


class CreativeGenerationError(ValueError):
    """Raised when generation preconditions are not met (router maps to 422)."""


@dataclass(slots=True)
class UploadedImage:
    width: int
    height: int
    checksum: str


async def upload_product_image(
    session: AsyncSession,
    *,
    project: Project,
    product_id: uuid.UUID,
    filename: str,
    content_type: str,
    data: bytes,
    rights_attested: bool,
    actor: str | None,
) -> ProductImage:
    settings = get_settings()
    if not rights_attested:
        raise RightsNotAttestedError()
    if not data:
        raise InvalidImageError(
            checks.ImageCheckReport(status=CheckStatus.FAILED, issues=[])
        )
    if len(data) > settings.max_image_bytes:
        raise ImageTooLargeError(settings.max_image_bytes)
    if content_type not in _ALLOWED_CONTENT_TYPES:
        try:
            content_type = sniff_content_type(data)
        except Exception:
            content_type = "application/octet-stream"
        if content_type not in _ALLOWED_CONTENT_TYPES:
            raise InvalidImageError(
                checks.ImageCheckReport(
                    status=CheckStatus.FAILED,
                    issues=[checks.ImageIssue("format", f"unsupported type {content_type}")],
                )
            )

    report = checks.check_upload(data, content_type)
    if report.status is not CheckStatus.PASSED:
        raise InvalidImageError(report)

    checksum = hashlib.sha256(data).hexdigest()
    duplicate = (
        await session.execute(
            select(ProductImage).where(
                ProductImage.product_id == product_id,
                ProductImage.checksum == checksum,
            )
        )
    ).scalar_one_or_none()
    if duplicate is not None:
        raise DuplicateImageError(duplicate.id)

    width, height = image_dimensions(data)

    safe_ext = "png" if content_type == "image/png" else "jpg"
    safe_name = f"{checksum[:16]}.{safe_ext}"
    storage_key = f"products/{product_id}/{safe_name}"
    storage = get_storage()
    await storage.save(storage_key, data, content_type)

    image = ProductImage(
        project_id=project.id,
        product_id=product_id,
        filename=filename or safe_name,
        content_type=content_type,
        size_bytes=len(data),
        width=width,
        height=height,
        checksum=checksum,
        storage_key=storage_key,
        uploaded_by=actor,
    )
    session.add(image)
    await log_event(
        session,
        workspace_id=project.workspace_id,
        action=AuditAction.IMAGE_UPLOADED,
        actor=actor,
        entity_type="product_image",
        after={"filename": image.filename, "checksum": checksum[:12]},
    )
    return image


async def load_source_images(
    session: AsyncSession, *, product_id: uuid.UUID, source_image_ids: list[str]
) -> tuple[list[ProductImage], list[bytes]]:
    rows: list[ProductImage] = []
    blobs: list[bytes] = []
    storage = get_storage()
    for raw_id in source_image_ids:
        image_id = uuid.UUID(raw_id)
        image = (
            await session.execute(select(ProductImage).where(ProductImage.id == image_id))
        ).scalar_one_or_none()
        if image is None or image.product_id != product_id:
            raise CreativeGenerationError(f"source image {raw_id} not found for product")
        rows.append(image)
        blobs.append(storage.load(image.storage_key))
    return rows, blobs


async def _confirmed_facts(
    session: AsyncSession, *, project: Project, product_id: uuid.UUID
) -> list[ProductFact]:
    facts = await list_usable_facts(session, project=project)
    return [f for f in facts if f.product_id == product_id]


async def _accepted_insights(
    session: AsyncSession, *, project: Project, product_id: uuid.UUID
) -> list[Insight]:
    rows = (
        await session.execute(
            select(Insight).where(
                Insight.project_id == project.id,
                Insight.product_id == product_id,
                Insight.status.in_(
                    [InsightStatus.ACCEPTED.value, InsightStatus.EDITED.value]
                ),
            )
        )
    ).scalars()
    return list(rows)


async def generate_creative(
    session: AsyncSession,
    *,
    project: Project,
    product_id: uuid.UUID,
    asset_type: AssetType,
    source_image_ids: list[str],
    overlay_lines: list[str],
    actor: str | None,
) -> CreativeAsset:
    settings = get_settings()
    if asset_type is AssetType.MAIN_IMAGE_EDIT:
        if not source_image_ids:
            raise CreativeGenerationError(
                "main image edit requires an uploaded source photo"
            )
        if overlay_lines:
            raise CreativeGenerationError(
                "main image must not contain added text or graphics"
            )

    facts = await _confirmed_facts(session, project=project, product_id=product_id)
    insights = await _accepted_insights(session, project=project, product_id=product_id)

    brief = build_brief(
        asset_type=asset_type,
        facts=[
            BriefInput(fact_type=f.fact_type, value=f.value, unit=f.unit) for f in facts
        ],
        insights=[
            InsightBriefInput(topic=i.topic, sentiment=i.sentiment) for i in insights
        ],
    )
    prompt = brief.to_prompt()

    source_rows, source_blobs = await load_source_images(
        session, product_id=product_id, source_image_ids=source_image_ids
    )

    engine = get_image_engine(settings)
    if asset_type is AssetType.MAIN_IMAGE_EDIT:
        result = await engine.edit(source_blobs, prompt)
    else:
        result = await engine.generate(prompt, 1024, 1024)

    consistency = checks.check_consistency(
        asset_type=asset_type, output=result.content, source_images=source_blobs
    )

    overlay_applied = bool(overlay_lines)
    content = result.content
    if overlay_applied:
        content = apply_overlay(content, overlay_lines)

    compliance = checks.check_compliance(
        asset_type=asset_type, output=content, overlay_applied=overlay_applied
    )

    width, height = _dimensions(content)
    ext = "png" if result.content_type == "image/png" else "jpg"
    output_key = f"creatives/{project.id}/{uuid.uuid4().hex}.{ext}"
    storage = get_storage()
    await storage.save(output_key, content, result.content_type)

    creative = CreativeAsset(
        project_id=project.id,
        product_id=product_id,
        asset_type=asset_type.value,
        locale=project.target_locale,
        source_images=[str(i.id) for i in source_rows] or None,
        creative_brief=brief.to_dict(),
        prompt=prompt,
        model=result.model,
        output_key=output_key,
        output_content_type=result.content_type,
        size_bytes=len(content),
        width=width,
        height=height,
        consistency_status=consistency.status.value,
        compliance_status=compliance.status.value,
        human_review_status=ReviewStatus.PENDING.value,
        created_by=actor,
    )
    session.add(creative)
    await session.flush()

    before = {"status": project.status}
    project.status = advance_status(project.status, WorkflowState.CREATIVES_GENERATED)
    if project.status != before["status"]:
        await log_event(
            session,
            workspace_id=project.workspace_id,
            action=AuditAction.PROJECT_STATUS_CHANGED,
            actor=actor,
            entity_type="project",
            entity_id=str(project.id),
            before=before,
            after={"status": project.status},
        )
    await log_event(
        session,
        workspace_id=project.workspace_id,
        action=AuditAction.CREATIVE_GENERATED,
        actor=actor,
        entity_type="creative",
        entity_id=str(creative.id),
        after={
            "asset_type": asset_type.value,
            "consistency": creative.consistency_status,
            "compliance": creative.compliance_status,
        },
    )
    return creative


def _dimensions(data: bytes) -> tuple[int, int]:
    from app.images.engines import image_dimensions

    return image_dimensions(data)


async def review_creative(
    session: AsyncSession,
    *,
    project: Project,
    creative: CreativeAsset,
    decision: ReviewStatus,
    actor: str | None,
) -> CreativeAsset:
    if decision not in {ReviewStatus.APPROVED, ReviewStatus.REJECTED}:
        raise ValueError("decision must be approved or rejected")
    creative.human_review_status = decision.value
    action = (
        AuditAction.CREATIVE_APPROVED
        if decision is ReviewStatus.APPROVED
        else AuditAction.CREATIVE_REJECTED
    )
    await log_event(
        session,
        workspace_id=project.workspace_id,
        action=action,
        actor=actor,
        entity_type="creative",
        entity_id=str(creative.id),
        after={"human_review_status": creative.human_review_status},
    )
    return creative
