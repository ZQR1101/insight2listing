"""Insight and opportunity-card endpoints (Phase C, plan sections 9 & 10)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ActorDep, SessionDep
from app.core.enums import InsightStatus, WorkflowState
from app.models.insight import Evidence, Insight
from app.models.project import Project
from app.opportunities.service import (
    edit_insight,
    generate_project_insights,
    set_insight_status,
)
from app.schemas.insights import (
    EvidenceRead,
    InsightDetail,
    InsightEdit,
    InsightGenerateResult,
    InsightList,
    InsightRead,
    InsightStatusUpdate,
)

router = APIRouter(prefix="/api/v1/projects/{project_id}/insights", tags=["insights"])

_HUMAN_STATUSES = {InsightStatus.ACCEPTED, InsightStatus.REJECTED, InsightStatus.EDITED}


async def _get_project(session: AsyncSession, project_id: uuid.UUID) -> Project:
    project = (
        await session.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    return project


async def _get_insight(session: AsyncSession, project_id: uuid.UUID, insight_id: uuid.UUID) -> Insight:
    insight = (
        await session.execute(select(Insight).where(Insight.id == insight_id))
    ).scalar_one_or_none()
    if insight is None or insight.project_id != project_id:
        raise HTTPException(status_code=404, detail="insight not found")
    return insight


@router.post("/generate", response_model=InsightGenerateResult)
async def generate(
    project_id: uuid.UUID, session: SessionDep, actor: ActorDep
) -> InsightGenerateResult:
    project = await _get_project(session, project_id)
    if _generated_beyond(project.status):
        raise HTTPException(status_code=409, detail="insights already generated")

    result = await generate_project_insights(session, project=project, actor=actor)
    await session.commit()
    return InsightGenerateResult(
        insights=result.insights,
        cards=result.cards,
        reviews_attributed=result.reviews_attributed,
        reviews_skipped=result.reviews_skipped,
    )


@router.get("", response_model=InsightList)
async def list_insights(
    project_id: uuid.UUID,
    session: SessionDep,
    product_id: uuid.UUID | None = None,
    insight_status: InsightStatus | None = None,
) -> InsightList:
    await _get_project(session, project_id)
    filters = [Insight.project_id == project_id]
    if product_id is not None:
        filters.append(Insight.product_id == product_id)
    if insight_status is not None:
        filters.append(Insight.status == insight_status.value)

    total = (
        await session.execute(select(func.count()).select_from(Insight).where(*filters))
    ).scalar_one()
    rows = (
        await session.execute(
            select(Insight).where(*filters).order_by(Insight.frequency.desc(), Insight.topic)
        )
    ).scalars()
    items = [InsightRead.model_validate(i) for i in rows]
    return InsightList(items=items, total=total)


@router.get("/{insight_id}", response_model=InsightDetail)
async def get_insight(
    project_id: uuid.UUID, insight_id: uuid.UUID, session: SessionDep
) -> InsightDetail:
    insight = await _get_insight(session, project_id, insight_id)
    evidence = (
        await session.execute(
            select(Evidence)
            .where(Evidence.insight_id == insight.id)
            .order_by(Evidence.support_strength.desc())
        )
    ).scalars()
    detail = InsightDetail.model_validate(insight)
    detail.evidence = [EvidenceRead.model_validate(e) for e in evidence]
    return detail


@router.patch("/{insight_id}/status", response_model=InsightRead)
async def review_insight(
    project_id: uuid.UUID,
    insight_id: uuid.UUID,
    payload: InsightStatusUpdate,
    session: SessionDep,
    actor: ActorDep,
) -> InsightRead:
    if payload.status not in _HUMAN_STATUSES:
        raise HTTPException(
            status_code=422, detail="status must be accepted, rejected or edited"
        )
    project = await _get_project(session, project_id)
    insight = await _get_insight(session, project_id, insight_id)
    updated = await set_insight_status(
        session, project=project, insight=insight, status=payload.status, actor=actor
    )
    await session.commit()
    await session.refresh(updated)
    return InsightRead.model_validate(updated)


@router.patch("/{insight_id}", response_model=InsightRead)
async def edit(
    project_id: uuid.UUID,
    insight_id: uuid.UUID,
    payload: InsightEdit,
    session: SessionDep,
    actor: ActorDep,
) -> InsightRead:
    project = await _get_project(session, project_id)
    insight = await _get_insight(session, project_id, insight_id)
    updated = await edit_insight(session, project=project, insight=insight, payload=payload, actor=actor)
    await session.commit()
    await session.refresh(updated)
    return InsightRead.model_validate(updated)


def _generated_beyond(current_status: str) -> bool:
    order = list(WorkflowState)
    try:
        idx = order.index(WorkflowState(current_status))
    except ValueError:
        return False
    return idx >= order.index(WorkflowState.INSIGHTS_GENERATED)
