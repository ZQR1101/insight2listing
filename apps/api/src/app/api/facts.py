"""Product facts centre endpoints (plan sections 6.6, 7.3, 11)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ActorDep, SessionDep
from app.core.enums import FactStatus
from app.facts.service import (
    confirm_project_facts,
    create_fact,
    set_fact_status,
)
from app.models.catalog import ProductCandidate
from app.models.facts import ProductFact
from app.models.project import Project
from app.schemas.facts import (
    FactList,
    FactsConfirmResult,
    ProductFactCreate,
    ProductFactRead,
    ProductFactStatusUpdate,
)

router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["facts"])

_CONFIRMABLE = {FactStatus.USER_CONFIRMED, FactStatus.DOCUMENT_CONFIRMED, FactStatus.REJECTED}


async def _get_project(session: AsyncSession, project_id: uuid.UUID) -> Project:
    project = (
        await session.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    return project


async def _get_fact(session: AsyncSession, project_id: uuid.UUID, fact_id: uuid.UUID) -> ProductFact:
    fact = (
        await session.execute(select(ProductFact).where(ProductFact.id == fact_id))
    ).scalar_one_or_none()
    if fact is None or fact.project_id != project_id:
        raise HTTPException(status_code=404, detail="fact not found")
    return fact


@router.get("/facts", response_model=FactList)
async def list_facts(
    project_id: uuid.UUID,
    session: SessionDep,
    product_id: uuid.UUID | None = None,
    fact_status: FactStatus | None = None,
) -> FactList:
    await _get_project(session, project_id)
    filters = [ProductFact.project_id == project_id]
    if product_id is not None:
        filters.append(ProductFact.product_id == product_id)
    if fact_status is not None:
        filters.append(ProductFact.verification_status == fact_status.value)

    total = (
        await session.execute(select(func.count()).select_from(ProductFact).where(*filters))
    ).scalar_one()
    rows = (
        await session.execute(
            select(ProductFact).where(*filters).order_by(ProductFact.created_at.desc())
        )
    ).scalars()
    return FactList(items=[ProductFactRead.model_validate(f) for f in rows], total=total)


@router.post(
    "/products/{product_id}/facts",
    response_model=ProductFactRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_fact(
    project_id: uuid.UUID,
    product_id: uuid.UUID,
    payload: ProductFactCreate,
    session: SessionDep,
    actor: ActorDep,
) -> ProductFactRead:
    project = await _get_project(session, project_id)
    product = (
        await session.execute(select(ProductCandidate).where(ProductCandidate.id == product_id))
    ).scalar_one_or_none()
    if product is None or product.project_id != project_id:
        raise HTTPException(status_code=404, detail="product not found")

    fact = await create_fact(
        session, project=project, product_id=product_id, payload=payload, actor=actor
    )
    await session.commit()
    await session.refresh(fact)
    return ProductFactRead.model_validate(fact)


@router.patch("/facts/{fact_id}/status", response_model=ProductFactRead)
async def update_fact_status(
    project_id: uuid.UUID,
    fact_id: uuid.UUID,
    payload: ProductFactStatusUpdate,
    session: SessionDep,
    actor: ActorDep,
) -> ProductFactRead:
    if payload.status not in _CONFIRMABLE:
        raise HTTPException(
            status_code=422,
            detail="status must be user_confirmed, document_confirmed or rejected",
        )
    project = await _get_project(session, project_id)
    fact = await _get_fact(session, project_id, fact_id)
    updated = await set_fact_status(
        session, project=project, fact=fact, status=payload.status, actor=actor
    )
    await session.commit()
    await session.refresh(updated)
    return ProductFactRead.model_validate(updated)


@router.delete("/facts/{fact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fact(
    project_id: uuid.UUID, fact_id: uuid.UUID, session: SessionDep
) -> None:
    await _get_project(session, project_id)
    fact = await _get_fact(session, project_id, fact_id)
    await session.delete(fact)
    await session.commit()


@router.post("/facts/confirm", response_model=FactsConfirmResult)
async def confirm_facts(
    project_id: uuid.UUID, session: SessionDep, actor: ActorDep
) -> FactsConfirmResult:
    """The §7.3 human confirmation gate for product facts."""
    project = await _get_project(session, project_id)
    try:
        confirmed = await confirm_project_facts(session, project=project, actor=actor)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    await session.commit()
    await session.refresh(project)
    return FactsConfirmResult(
        project_id=project.id,
        status=project.status,  # type: ignore[arg-type]
        confirmed_facts=confirmed,
    )
