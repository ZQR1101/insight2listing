"""Product facts service (plan sections 6.6, 11, 7.3).

Facts start UNVERIFIED and only become usable once a human confirms them. The
project-level confirm step is the §7.3 human confirmation gate that advances
the workflow to PRODUCT_FACTS_CONFIRMED.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.audit_logger import log_event
from app.core.enums import AuditAction, FactStatus, WorkflowState
from app.models.facts import ProductFact
from app.models.project import Project
from app.schemas.facts import ProductFactCreate
from app.workflows.transitions import advance_status

_CONFIRMED_VALUES = {
    FactStatus.USER_CONFIRMED.value,
    FactStatus.DOCUMENT_CONFIRMED.value,
}


def _is_usable(fact: ProductFact) -> bool:
    """Confirmed and not expired (an expired fact can no longer back a claim)."""
    if fact.verification_status not in _CONFIRMED_VALUES:
        return False
    return fact.expires_at is None or fact.expires_at > datetime.now(UTC)


async def create_fact(
    session: AsyncSession,
    *,
    project: Project,
    product_id: uuid.UUID,
    payload: ProductFactCreate,
    actor: str | None,
) -> ProductFact:
    fact = ProductFact(
        project_id=project.id,
        product_id=product_id,
        fact_type=payload.fact_type.value,
        value=payload.value,
        unit=payload.unit,
        source=payload.source or "user_entry",
        verification_status=FactStatus.UNVERIFIED.value,
        created_by=actor,
    )
    session.add(fact)
    await log_event(
        session,
        workspace_id=project.workspace_id,
        action=AuditAction.FACT_CREATED,
        actor=actor,
        entity_type="product_fact",
        after={"fact_type": fact.fact_type, "value": fact.value[:80]},
    )
    return fact


async def set_fact_status(
    session: AsyncSession,
    *,
    project: Project,
    fact: ProductFact,
    status: FactStatus,
    actor: str | None,
) -> ProductFact:
    """Confirm or reject a fact. Confirmations stamp who/when."""
    before = {"verification_status": fact.verification_status}
    fact.verification_status = status.value
    if status in {FactStatus.USER_CONFIRMED, FactStatus.DOCUMENT_CONFIRMED}:
        fact.verified_by = actor
        fact.verified_at = datetime.now(UTC)
    await log_event(
        session,
        workspace_id=project.workspace_id,
        action=AuditAction.FACT_STATUS_CHANGED,
        actor=actor,
        entity_type="product_fact",
        entity_id=str(fact.id),
        before=before,
        after={"verification_status": fact.verification_status},
    )
    return fact


async def count_usable_facts(session: AsyncSession, *, project: Project) -> int:
    facts = (
        await session.execute(select(ProductFact).where(ProductFact.project_id == project.id))
    ).scalars().all()
    return sum(1 for f in facts if _is_usable(f))


async def list_usable_facts(session: AsyncSession, *, project: Project) -> list[ProductFact]:
    """Confirmed, non-expired facts — the only inputs Listing generation may use."""
    facts = (
        await session.execute(select(ProductFact).where(ProductFact.project_id == project.id))
    ).scalars().all()
    return [f for f in facts if _is_usable(f)]


async def confirm_project_facts(
    session: AsyncSession, *, project: Project, actor: str | None
) -> int:
    """The §7.3 human confirmation gate.

    Requires at least one usable (confirmed, non-expired) fact; advances the
    project to PRODUCT_FACTS_CONFIRMED. Returns the number of usable facts, or
    raises ValueError when nothing is confirmed (router maps that to 409).
    """
    usable = await count_usable_facts(session, project=project)
    if usable == 0:
        raise ValueError("no confirmed facts")

    before = {"status": project.status}
    project.status = advance_status(project.status, WorkflowState.PRODUCT_FACTS_CONFIRMED)
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
    return usable
