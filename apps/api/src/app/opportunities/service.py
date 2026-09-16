"""Phase C orchestration service.

The router-facing layer: generates insights + opportunity cards from a project's
reviews, and applies human review (accept / reject / edit) while advancing the
project workflow state. The caller owns the session and commit.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.audit_logger import log_event
from app.core.enums import (
    AuditAction,
    InsightStatus,
    WorkflowState,
)
from app.models.catalog import ProductCandidate
from app.models.insight import Evidence, Insight
from app.models.opportunity import OpportunityCard
from app.models.project import Project
from app.models.review import Review
from app.opportunities import engine
from app.opportunities.opportunity_card import build_card
from app.schemas.insights import InsightEdit
from app.workflows.transitions import can_transition


@dataclass(slots=True)
class GenerateResult:
    insights: int
    cards: int
    reviews_attributed: int
    reviews_skipped: int


async def generate_project_insights(
    session: AsyncSession, *, project: Project, actor: str | None
) -> GenerateResult:
    """Run the rule engine over a project's reviews and persist the results."""
    reviews = (
        await session.execute(select(Review).where(Review.project_id == project.id))
    ).scalars().all()

    attributed = []
    skipped = 0
    for r in reviews:
        if r.product_id is None or not r.body:
            skipped += 1
            continue
        attributed.append(
            engine.ReviewInput(
                id=r.id,
                product_id=r.product_id,
                rating=r.rating,
                body=r.body,
                reviewed_at=r.reviewed_at,
            )
        )

    insights = engine.analyze(attributed)

    # Persist insights + their evidence.
    by_product: dict[uuid.UUID, list[engine.InsightOutput]] = {}
    for output in insights:
        insight = Insight(
            project_id=project.id,
            product_id=output.product_id,
            topic=output.topic,
            summary=output.summary,
            sentiment=output.sentiment.value,
            frequency=output.frequency,
            severity=output.severity.value,
            rating_impact=output.rating_impact,
            recency_score=output.recency_score,
            cross_competitor_score=output.cross_competitor_score,
            confidence=output.confidence,
            status=InsightStatus.GENERATED.value,
            created_by=actor,
        )
        session.add(insight)
        await session.flush()
        for ev in output.evidence:
            session.add(
                Evidence(
                    insight_id=insight.id,
                    evidence_type=ev.evidence_type.value,
                    source_entity_id=ev.source_entity_id,
                    excerpt=ev.excerpt,
                    support_strength=ev.support_strength,
                    observed_at=ev.observed_at,
                )
            )
        by_product.setdefault(output.product_id, []).append(output)

    # Build one opportunity card per product that produced insights.
    cards = 0
    if by_product:
        products = {
            p.id: p
            for p in (
                await session.execute(
                    select(ProductCandidate).where(
                        ProductCandidate.id.in_(by_product.keys())
                    )
                )
            ).scalars()
        }
        for product_id, outputs in by_product.items():
            product = products.get(product_id)
            title = product.title if product else ""
            total = sum(1 for r in attributed if r.product_id == product_id)
            draft = build_card(product_title=title, insights=outputs, total_reviews=total)
            session.add(
                OpportunityCard(
                    project_id=project.id,
                    product_id=product_id,
                    title=draft.title,
                    target_audience=draft.target_audience,
                    use_cases=draft.use_cases,
                    competitor_gaps=draft.competitor_gaps,
                    differentiation_ideas=draft.differentiation_ideas,
                    keywords=draft.keywords,
                    opportunity_score=draft.opportunity_score,
                    dimension_scores=draft.dimension_scores,
                    score_version=draft.score_version,
                    confidence=draft.confidence,
                    missing_dimensions=draft.missing_dimensions,
                    risk_flags=draft.risk_flags,
                    created_by=actor,
                )
            )
            cards += 1

    # Persisted rows exist; trigger insert ordering so FKs resolve on commit.
    await session.flush()

    if insights or cards:  # only advance workflow when there is real output
        _advance(project, WorkflowState.INSIGHTS_GENERATED)
        await log_event(
            session,
            workspace_id=project.workspace_id,
            action=AuditAction.INSIGHT_GENERATED,
            actor=actor,
            entity_type="project",
            entity_id=str(project.id),
            after={"insights": len(insights), "cards": cards},
        )
        if cards:
            await log_event(
                session,
                workspace_id=project.workspace_id,
                action=AuditAction.OPPORTUNITY_CARD_GENERATED,
                actor=actor,
                entity_type="project",
                entity_id=str(project.id),
                after={"cards": cards},
            )

    return GenerateResult(
        insights=len(insights),
        cards=cards,
        reviews_attributed=len(attributed),
        reviews_skipped=skipped,
    )


async def set_insight_status(
    session: AsyncSession,
    *,
    project: Project,
    insight: Insight,
    status: InsightStatus,
    actor: str | None,
) -> Insight:
    """Apply a human decision (accept / reject / edit) to an insight."""
    before = {"status": insight.status}
    insight.status = status.value
    _advance(project, WorkflowState.INSIGHTS_REVIEWED)
    await log_event(
        session,
        workspace_id=project.workspace_id,
        action=AuditAction.INSIGHT_STATUS_CHANGED,
        actor=actor,
        entity_type="insight",
        entity_id=str(insight.id),
        before=before,
        after={"status": insight.status},
    )
    return insight


async def edit_insight(
    session: AsyncSession,
    *,
    project: Project,
    insight: Insight,
    payload: InsightEdit,
    actor: str | None,
) -> Insight:
    """Apply an edited insight and mark it EDITED."""
    if payload.topic is not None:
        insight.topic = payload.topic
    if payload.summary is not None:
        insight.summary = payload.summary
    if payload.sentiment is not None:
        insight.sentiment = payload.sentiment.value
    if payload.severity is not None:
        insight.severity = payload.severity.value
    insight.status = InsightStatus.EDITED.value
    _advance(project, WorkflowState.INSIGHTS_REVIEWED)
    await log_event(
        session,
        workspace_id=project.workspace_id,
        action=AuditAction.INSIGHT_EDITED,
        actor=actor,
        entity_type="insight",
        entity_id=str(insight.id),
        after={"topic": insight.topic, "status": insight.status},
    )
    return insight


def _advance(project: Project, target: WorkflowState) -> None:
    try:
        current = WorkflowState(project.status)
    except ValueError:
        current = WorkflowState.DRAFT
    if can_transition(current, target):
        project.status = target.value
