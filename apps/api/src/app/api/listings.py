"""Listing workbench endpoints (plan sections 6.7, 12)."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ActorDep, SessionDep
from app.listings import export_listing
from app.listings.service import (
    ListingGenerationError,
    approve_listing_version,
    edit_listing_version,
    generate_listing_version,
)
from app.models.catalog import ProductCandidate
from app.models.listing import ListingVersion
from app.models.project import Project
from app.schemas.listings import (
    ListingEdit,
    ListingList,
    ListingVersionRead,
)

router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["listings"])


async def _get_project(session: AsyncSession, project_id: uuid.UUID) -> Project:
    project = (
        await session.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    return project


async def _get_listing(
    session: AsyncSession, project_id: uuid.UUID, listing_id: uuid.UUID
) -> ListingVersion:
    listing = (
        await session.execute(select(ListingVersion).where(ListingVersion.id == listing_id))
    ).scalar_one_or_none()
    if listing is None or listing.project_id != project_id:
        raise HTTPException(status_code=404, detail="listing not found")
    return listing


@router.post(
    "/products/{product_id}/listings/generate",
    response_model=ListingVersionRead,
    status_code=status.HTTP_201_CREATED,
)
async def generate(
    project_id: uuid.UUID,
    product_id: uuid.UUID,
    session: SessionDep,
    actor: ActorDep,
) -> ListingVersionRead:
    project = await _get_project(session, project_id)
    product = (
        await session.execute(select(ProductCandidate).where(ProductCandidate.id == product_id))
    ).scalar_one_or_none()
    if product is None or product.project_id != project_id:
        raise HTTPException(status_code=404, detail="product not found")

    try:
        listing = await generate_listing_version(
            session, project=project, product=product, actor=actor
        )
    except ListingGenerationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await session.commit()
    await session.refresh(listing)
    return ListingVersionRead.model_validate(listing)


@router.get("/listings", response_model=ListingList)
async def list_listings(
    project_id: uuid.UUID,
    session: SessionDep,
    product_id: uuid.UUID | None = None,
    listing_status: Literal["draft", "approved"] | None = None,
) -> ListingList:
    await _get_project(session, project_id)
    filters = [ListingVersion.project_id == project_id]
    if product_id is not None:
        filters.append(ListingVersion.product_id == product_id)
    if listing_status is not None:
        filters.append(ListingVersion.status == listing_status)

    total = (
        await session.execute(
            select(func.count()).select_from(ListingVersion).where(*filters)
        )
    ).scalar_one()
    rows = (
        await session.execute(
            select(ListingVersion).where(*filters).order_by(ListingVersion.created_at.desc())
        )
    ).scalars()
    return ListingList(
        items=[ListingVersionRead.model_validate(row) for row in rows], total=total
    )


@router.get("/listings/{listing_id}", response_model=ListingVersionRead)
async def get_listing(
    project_id: uuid.UUID, listing_id: uuid.UUID, session: SessionDep
) -> ListingVersionRead:
    await _get_project(session, project_id)
    listing = await _get_listing(session, project_id, listing_id)
    return ListingVersionRead.model_validate(listing)


@router.patch("/listings/{listing_id}", response_model=ListingVersionRead)
async def edit_listing(
    project_id: uuid.UUID,
    listing_id: uuid.UUID,
    payload: ListingEdit,
    session: SessionDep,
    actor: ActorDep,
) -> ListingVersionRead:
    project = await _get_project(session, project_id)
    listing = await _get_listing(session, project_id, listing_id)
    updated = await edit_listing_version(
        session, project=project, listing=listing, payload=payload, actor=actor
    )
    await session.commit()
    await session.refresh(updated)
    return ListingVersionRead.model_validate(updated)


@router.post("/listings/{listing_id}/approve", response_model=ListingVersionRead)
async def approve_listing(
    project_id: uuid.UUID,
    listing_id: uuid.UUID,
    session: SessionDep,
    actor: ActorDep,
) -> ListingVersionRead:
    project = await _get_project(session, project_id)
    listing = await _get_listing(session, project_id, listing_id)
    try:
        updated = await approve_listing_version(
            session, project=project, listing=listing, actor=actor
        )
    except ListingGenerationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await session.commit()
    await session.refresh(updated)
    return ListingVersionRead.model_validate(updated)


@router.get("/listings/{listing_id}/export")
async def export(
    project_id: uuid.UUID,
    listing_id: uuid.UUID,
    session: SessionDep,
    format: Literal["json", "markdown", "csv"] = Query("json"),
) -> Response:
    await _get_project(session, project_id)
    listing = await _get_listing(session, project_id, listing_id)
    content, media_type, ext = export_listing(listing, format)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="listing_{listing.id}.{ext}"'},
    )
