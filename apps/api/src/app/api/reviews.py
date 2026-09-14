"""Review read endpoints (plan section 6.4 helpers)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, or_, select

from app.api.deps import SessionDep
from app.models.project import Project
from app.models.review import Review
from app.schemas.catalog import ReviewList, ReviewRead

router = APIRouter(prefix="/api/v1/projects/{project_id}/reviews", tags=["reviews"])


@router.get("", response_model=ReviewList)
async def list_reviews(
    project_id: uuid.UUID,
    session: SessionDep,
    q: str | None = Query(None, description="substring search over review body/title"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> ReviewList:
    project = (
        await session.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")

    filters = [Review.project_id == project_id]
    if q:
        like = f"%{q}%"
        filters.append(or_(Review.body.ilike(like), Review.title.ilike(like)))

    base = select(Review).where(*filters)
    total = (await session.execute(select(func.count()).select_from(Review).where(*filters))).scalar_one()
    rows = (
        await session.execute(base.order_by(Review.reviewed_at.desc()).limit(limit).offset(offset))
    ).scalars()
    items = [ReviewRead.model_validate(r) for r in rows]
    return ReviewList(items=items, total=total)
