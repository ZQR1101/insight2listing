"""Opportunity-card read endpoints (plan sections 10, 16.9)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import SessionDep
from app.models.opportunity import OpportunityCard
from app.models.project import Project
from app.schemas.opportunity import OpportunityCardList, OpportunityCardRead

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/opportunity-cards", tags=["opportunity-cards"]
)


async def _get_project(session: AsyncSession, project_id: uuid.UUID) -> Project:
    project = (
        await session.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    return project


@router.get("", response_model=OpportunityCardList)
async def list_cards(project_id: uuid.UUID, session: SessionDep) -> OpportunityCardList:
    await _get_project(session, project_id)
    total = (
        await session.execute(
            select(func.count())
            .select_from(OpportunityCard)
            .where(OpportunityCard.project_id == project_id)
        )
    ).scalar_one()
    rows = (
        await session.execute(
            select(OpportunityCard)
            .where(OpportunityCard.project_id == project_id)
            .order_by(OpportunityCard.opportunity_score.desc().nulls_last())
        )
    ).scalars()
    items = [OpportunityCardRead.model_validate(c) for c in rows]
    return OpportunityCardList(items=items, total=total)


@router.get("/{product_id}", response_model=OpportunityCardRead)
async def get_card(
    project_id: uuid.UUID, product_id: uuid.UUID, session: SessionDep
) -> OpportunityCardRead:
    await _get_project(session, project_id)
    card = (
        await session.execute(
            select(OpportunityCard).where(
                OpportunityCard.project_id == project_id,
                OpportunityCard.product_id == product_id,
            )
        )
    ).scalar_one_or_none()
    if card is None:
        raise HTTPException(status_code=404, detail="opportunity card not found")
    return OpportunityCardRead.model_validate(card)
