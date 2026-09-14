"""Catalog product and variant read endpoints (plan section 6.3)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.models.catalog import ProductCandidate
from app.models.project import Project
from app.schemas.catalog import ProductList, ProductRead

router = APIRouter(prefix="/api/v1/projects/{project_id}/products", tags=["products"])


@router.get("", response_model=ProductList)
async def list_products(project_id: uuid.UUID, session: SessionDep) -> ProductList:
    project = (
        await session.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")

    total = (
        await session.execute(
            select(func.count()).select_from(ProductCandidate).where(
                ProductCandidate.project_id == project_id
            )
        )
    ).scalar_one()
    rows = (
        await session.execute(
            select(ProductCandidate).where(ProductCandidate.project_id == project_id)
        )
    ).scalars()
    items = [ProductRead.model_validate(p) for p in rows]
    return ProductList(items=items, total=total)
