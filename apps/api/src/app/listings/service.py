"""Listing workbench service (plan section 12).

Generation is rule-template based and fact-bound; approval is gated on both
the fact-check and rule-check reports; regeneration creates a new version and
never overwrites an approved one (section 12.3).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.audit_logger import log_event
from app.core.enums import (
    AuditAction,
    InsightStatus,
    ListingStatus,
    WorkflowState,
)
from app.facts.service import list_usable_facts
from app.listings import rules
from app.listings.generator import (
    FactInput,
    InsightInput,
)
from app.listings.generator import (
    generate_listing as build_draft,
)
from app.models.catalog import ProductCandidate
from app.models.facts import ProductFact
from app.models.insight import Insight
from app.models.listing import ListingVersion
from app.models.project import Project
from app.schemas.listings import ListingEdit
from app.workflows.transitions import advance_status


def _error_issues(report: dict[str, object] | None) -> list[dict[str, object]]:
    """Extract severity=error issues from a stored check report."""
    raw = (report or {}).get("issues")
    if not isinstance(raw, list):
        return []
    return [i for i in raw if isinstance(i, dict) and i.get("severity") == "error"]


class ListingGenerationError(ValueError):
    """Raised when generation preconditions are not met."""


def _bullet_dicts(listing: ListingVersion) -> list[dict[str, object]]:
    return list(listing.bullet_points or [])


async def _usable_facts_for_product(
    session: AsyncSession, *, project: Project, product_id: uuid.UUID
) -> list[ProductFact]:
    facts = await list_usable_facts(session, project=project)
    return [f for f in facts if f.product_id == product_id]


async def _accepted_insights_for_product(
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


async def generate_listing_version(
    session: AsyncSession,
    *,
    project: Project,
    product: ProductCandidate,
    actor: str | None,
) -> ListingVersion:
    """Create a new draft ListingVersion from confirmed facts + accepted insights."""
    facts = await _usable_facts_for_product(session, project=project, product_id=product.id)
    if not facts:
        raise ListingGenerationError("no confirmed facts for this product")

    insights = await _accepted_insights_for_product(
        session, project=project, product_id=product.id
    )

    draft = build_draft(
        product_title=product.title,
        facts=[
            FactInput(id=f.id, fact_type=f.fact_type, value=f.value, unit=f.unit)
            for f in facts
        ],
        insights=[
            InsightInput(id=i.id, topic=i.topic, sentiment=i.sentiment) for i in insights
        ],
    )

    listing = ListingVersion(
        project_id=project.id,
        product_id=product.id,
        marketplace=project.marketplace,
        locale=project.target_locale,
        title=draft.title,
        bullet_points=[b.as_dict() for b in draft.bullet_points],
        description=draft.description,
        search_terms=draft.search_terms,
        model=draft.model,
        prompt_version=draft.prompt_version,
        input_snapshot_id=draft.input_snapshot_id,
        input_snapshot=draft.input_snapshot,
        status=ListingStatus.DRAFT.value,
        fact_check=draft.fact_check.to_dict(),
        rule_check=draft.rule_check.to_dict(),
        created_by=actor,
    )
    session.add(listing)
    await session.flush()

    before = {"status": project.status}
    project.status = advance_status(
        project.status, WorkflowState.PRODUCT_FACTS_CONFIRMED, WorkflowState.LISTING_GENERATED
    )
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
        action=AuditAction.LISTING_GENERATED,
        actor=actor,
        entity_type="listing_version",
        entity_id=str(listing.id),
        after={
            "product_id": str(product.id),
            "facts_used": len(facts),
            "insights_used": len(insights),
            "missing_attributes": draft.missing_attributes,
        },
    )
    return listing


async def edit_listing_version(
    session: AsyncSession,
    *,
    project: Project,
    listing: ListingVersion,
    payload: ListingEdit,
    actor: str | None,
) -> ListingVersion:
    """Apply a human edit; an approved version returns to draft (§12.3)."""
    if payload.title is not None:
        listing.title = payload.title
    if payload.bullet_points is not None:
        listing.bullet_points = [b.model_dump() for b in payload.bullet_points]
    if payload.description is not None:
        listing.description = payload.description
    if payload.search_terms is not None:
        listing.search_terms = payload.search_terms

    # Re-validate against the *current* confirmed facts of the product.
    facts = await _usable_facts_for_product(session, project=project, product_id=listing.product_id)
    confirmed_ids = {str(f.id) for f in facts}
    bullets = _bullet_dicts(listing)
    listing.fact_check = rules.check_fact_usage(
        bullets=bullets, confirmed_fact_ids=confirmed_ids
    ).to_dict()
    listing.rule_check = rules.check_listing(
        title=listing.title,
        bullets=[str(b.get("text", "")) for b in bullets],
        description=listing.description or "",
        search_terms=listing.search_terms or "",
    ).to_dict()
    listing.status = ListingStatus.DRAFT.value

    await log_event(
        session,
        workspace_id=project.workspace_id,
        action=AuditAction.LISTING_EDITED,
        actor=actor,
        entity_type="listing_version",
        entity_id=str(listing.id),
        after={"status": listing.status},
    )
    return listing


async def approve_listing_version(
    session: AsyncSession,
    *,
    project: Project,
    listing: ListingVersion,
    actor: str | None,
) -> ListingVersion:
    """Approve only when both reports pass (§7.3 point 4 / §12.4)."""
    problems = [*_error_issues(listing.fact_check), *_error_issues(listing.rule_check)]
    fact_passed = bool((listing.fact_check or {}).get("passed"))
    rule_passed = bool((listing.rule_check or {}).get("passed"))
    if not fact_passed or not rule_passed:
        raise ListingGenerationError(f"listing checks failed: {problems}")

    listing.status = ListingStatus.APPROVED.value
    await log_event(
        session,
        workspace_id=project.workspace_id,
        action=AuditAction.LISTING_APPROVED,
        actor=actor,
        entity_type="listing_version",
        entity_id=str(listing.id),
        after={"status": listing.status},
    )
    return listing
