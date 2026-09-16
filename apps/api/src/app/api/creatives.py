"""Product image upload and creative endpoints (plan section 13)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ActorDep, SessionDep
from app.core.enums import ReviewStatus
from app.images import (
    CreativeGenerationError,
    DuplicateImageError,
    ImageTooLargeError,
    ImageUploadError,
    generate_creative,
    review_creative,
    upload_product_image,
)
from app.images.storage import get_storage
from app.models.catalog import ProductCandidate
from app.models.images import CreativeAsset, ProductImage
from app.models.project import Project
from app.schemas.images import (
    CreativeAssetRead,
    CreativeGenerateRequest,
    CreativeList,
    ImageList,
    ProductImageRead,
)

router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["creatives"])


async def _get_project(session: AsyncSession, project_id: uuid.UUID) -> Project:
    project = (
        await session.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    return project


async def _get_product(
    session: AsyncSession, project_id: uuid.UUID, product_id: uuid.UUID
) -> ProductCandidate:
    product = (
        await session.execute(select(ProductCandidate).where(ProductCandidate.id == product_id))
    ).scalar_one_or_none()
    if product is None or product.project_id != project_id:
        raise HTTPException(status_code=404, detail="product not found")
    return product


@router.post(
    "/products/{product_id}/images",
    response_model=ProductImageRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_image(
    project_id: uuid.UUID,
    product_id: uuid.UUID,
    session: SessionDep,
    actor: ActorDep,
    file: UploadFile = File(...),
    rights_attested: bool = Form(False),
) -> ProductImageRead:
    project = await _get_project(session, project_id)
    await _get_product(session, project_id, product_id)
    data = await file.read()
    try:
        image = await upload_product_image(
            session,
            project=project,
            product_id=product_id,
            filename=file.filename or "upload",
            content_type=file.content_type or "application/octet-stream",
            data=data,
            rights_attested=rights_attested,
            actor=actor,
        )
    except DuplicateImageError as exc:
        raise HTTPException(
            status_code=409, detail={"message": str(exc), "existing_id": str(exc.existing_id)}
        ) from exc
    except ImageTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except ImageUploadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await session.commit()
    await session.refresh(image)
    return ProductImageRead.model_validate(image)


@router.get("/products/{product_id}/images", response_model=ImageList)
async def list_images(
    project_id: uuid.UUID, product_id: uuid.UUID, session: SessionDep
) -> ImageList:
    await _get_project(session, project_id)
    total = (
        await session.execute(
            select(func.count())
            .select_from(ProductImage)
            .where(
                ProductImage.project_id == project_id,
                ProductImage.product_id == product_id,
            )
        )
    ).scalar_one()
    rows = (
        await session.execute(
            select(ProductImage)
            .where(
                ProductImage.project_id == project_id,
                ProductImage.product_id == product_id,
            )
            .order_by(ProductImage.created_at.desc())
        )
    ).scalars()
    return ImageList(items=[ProductImageRead.model_validate(i) for i in rows], total=total)


@router.get("/images/{image_id}/file")
async def get_image_file(
    project_id: uuid.UUID, image_id: uuid.UUID, session: SessionDep
) -> Response:
    await _get_project(session, project_id)
    image = (
        await session.execute(select(ProductImage).where(ProductImage.id == image_id))
    ).scalar_one_or_none()
    if image is None or image.project_id != project_id:
        raise HTTPException(status_code=404, detail="image not found")
    try:
        data = get_storage().load(image.storage_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="image bytes missing") from exc
    return Response(content=data, media_type=image.content_type)


@router.post(
    "/products/{product_id}/creatives/generate",
    response_model=CreativeAssetRead,
    status_code=status.HTTP_201_CREATED,
)
async def generate_creative_endpoint(
    project_id: uuid.UUID,
    product_id: uuid.UUID,
    payload: CreativeGenerateRequest,
    session: SessionDep,
    actor: ActorDep,
) -> CreativeAssetRead:
    project = await _get_project(session, project_id)
    await _get_product(session, project_id, product_id)
    try:
        creative = await generate_creative(
            session,
            project=project,
            product_id=product_id,
            asset_type=payload.asset_type,
            source_image_ids=payload.source_image_ids,
            overlay_lines=payload.overlay_lines,
            actor=actor,
        )
    except CreativeGenerationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await session.commit()
    await session.refresh(creative)
    return CreativeAssetRead.model_validate(creative)


@router.get("/creatives", response_model=CreativeList)
async def list_creatives(
    project_id: uuid.UUID,
    session: SessionDep,
    product_id: uuid.UUID | None = None,
) -> CreativeList:
    await _get_project(session, project_id)
    filters = [CreativeAsset.project_id == project_id]
    if product_id is not None:
        filters.append(CreativeAsset.product_id == product_id)
    total = (
        await session.execute(
            select(func.count()).select_from(CreativeAsset).where(*filters)
        )
    ).scalar_one()
    rows = (
        await session.execute(
            select(CreativeAsset).where(*filters).order_by(CreativeAsset.created_at.desc())
        )
    ).scalars()
    return CreativeList(items=[CreativeAssetRead.model_validate(c) for c in rows], total=total)


@router.get("/creatives/{creative_id}", response_model=CreativeAssetRead)
async def get_creative(
    project_id: uuid.UUID, creative_id: uuid.UUID, session: SessionDep
) -> CreativeAssetRead:
    await _get_project(session, project_id)
    creative = await _get_creative(session, project_id, creative_id)
    return CreativeAssetRead.model_validate(creative)


@router.get("/creatives/{creative_id}/file")
async def get_creative_file(
    project_id: uuid.UUID, creative_id: uuid.UUID, session: SessionDep
) -> Response:
    """Inline preview — available before approval for the review UI."""
    await _get_project(session, project_id)
    creative = await _get_creative(session, project_id, creative_id)
    data = _load_output(creative)
    return Response(content=data, media_type=creative.output_content_type or "image/png")


@router.get("/creatives/{creative_id}/download")
async def download_creative(
    project_id: uuid.UUID, creative_id: uuid.UUID, session: SessionDep
) -> Response:
    """Export gate: only human-approved creatives may be downloaded (§13.7)."""
    await _get_project(session, project_id)
    creative = await _get_creative(session, project_id, creative_id)
    if creative.human_review_status != ReviewStatus.APPROVED.value:
        raise HTTPException(
            status_code=403, detail="creative must be approved before download"
        )
    data = _load_output(creative)
    ext = "png" if creative.output_content_type == "image/png" else "jpg"
    return Response(
        content=data,
        media_type=creative.output_content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="creative_{creative.id}.{ext}"'},
    )


@router.post("/creatives/{creative_id}/approve", response_model=CreativeAssetRead)
async def approve_creative(
    project_id: uuid.UUID,
    creative_id: uuid.UUID,
    session: SessionDep,
    actor: ActorDep,
) -> CreativeAssetRead:
    project = await _get_project(session, project_id)
    creative = await _get_creative(session, project_id, creative_id)
    updated = await review_creative(
        session, project=project, creative=creative, decision=ReviewStatus.APPROVED, actor=actor
    )
    await session.commit()
    await session.refresh(updated)
    return CreativeAssetRead.model_validate(updated)


@router.post("/creatives/{creative_id}/reject", response_model=CreativeAssetRead)
async def reject_creative(
    project_id: uuid.UUID,
    creative_id: uuid.UUID,
    session: SessionDep,
    actor: ActorDep,
) -> CreativeAssetRead:
    project = await _get_project(session, project_id)
    creative = await _get_creative(session, project_id, creative_id)
    updated = await review_creative(
        session, project=project, creative=creative, decision=ReviewStatus.REJECTED, actor=actor
    )
    await session.commit()
    await session.refresh(updated)
    return CreativeAssetRead.model_validate(updated)


async def _get_creative(
    session: AsyncSession, project_id: uuid.UUID, creative_id: uuid.UUID
) -> CreativeAsset:
    creative = (
        await session.execute(select(CreativeAsset).where(CreativeAsset.id == creative_id))
    ).scalar_one_or_none()
    if creative is None or creative.project_id != project_id:
        raise HTTPException(status_code=404, detail="creative not found")
    return creative


def _load_output(creative: CreativeAsset) -> bytes:
    if not creative.output_key:
        raise HTTPException(status_code=404, detail="creative has no output")
    try:
        return get_storage().load(creative.output_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="creative bytes missing") from exc
