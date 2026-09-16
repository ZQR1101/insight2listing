"""Opportunity-card assembly (plan sections 10.2, 16.9).

Aggregates a product's insights into an explainable opportunity card: audience,
use cases, competitor gaps, differentiation, keywords, a weighted score with
per-dimension breakdown, confidence, and explicitly missing dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.enums import Sentiment
from app.opportunities.engine import InsightOutput
from app.opportunities.scoring import (
    OPPORTUNITY_WEIGHTS,
    SCORE_VERSION,
    opportunity_score,
    pain_point_score,
)

#: Extra dimensions the product team cares about but we cannot compute yet.
HARD_MISSING = ("supplier_cost", "advertising_cost", "absolute_search_volume")


@dataclass(slots=True)
class CardDraft:
    title: str
    target_audience: str | None
    use_cases: list[str]
    competitor_gaps: list[str]
    differentiation_ideas: list[str]
    keywords: list[str]
    opportunity_score: float | None
    dimension_scores: dict[str, float | None]
    score_version: str
    confidence: float
    missing_dimensions: list[str]
    risk_flags: list[str] = field(default_factory=list)


def build_card(
    *,
    product_title: str,
    insights: list[InsightOutput],
    total_reviews: int,
) -> CardDraft:
    """Build the scores and structured fields for one product's opportunity card.

    ``opportunity_score`` requires the seven plan dimensions. Only pain/gap/
    differentiation are derivable from reviews; the rest are left missing so
    confidence reflects exactly how much of the score is evidence-backed.
    """
    negative = [i for i in insights if i.sentiment is Sentiment.NEGATIVE]
    positive = [i for i in insights if i.sentiment is Sentiment.POSITIVE]

    pain_dim: float | None = None
    if negative:
        scores = [
            pain_point_score(
                frequency=i.frequency,
                severity=i.severity_value,
                rating_impact=i.rating_impact,
                cross_competitor=i.cross_competitor_score,
                recency=i.recency_score,
            )
            for i in negative
        ]
        present = [s.score for s in scores if s.score is not None]
        if present:
            pain_dim = round(sum(present) / len(present), 2)

    gap_dim = round(len(negative) / len(insights) * 100.0, 2) if insights else None
    differentiation_dim = (
        round(sum(i.confidence for i in positive) / len(positive) * 100.0, 2)
        if positive
        else None
    )

    result = opportunity_score(
        demand=None,
        growth=None,
        gap=gap_dim,
        pain=pain_dim,
        differentiation=differentiation_dim,
        unit_econ=None,
        risk=None,
    )

    dimension_scores: dict[str, float | None] = {
        "demand": None,
        "growth": None,
        "gap": gap_dim,
        "pain": pain_dim,
        "differentiation": differentiation_dim,
        "unit_econ": None,
        "risk": None,
    }

    risk_flags: list[str] = []
    if total_reviews < 10:
        risk_flags.append("low_review_volume")
    if result.score is not None and result.confidence < 0.6:
        risk_flags.append("limited_evidence_coverage")

    missing = list(dict.fromkeys([*result.missing, *HARD_MISSING]))

    return CardDraft(
        title=product_title or "Product opportunity",
        target_audience=_audience(negative, positive),
        use_cases=[i.topic for i in insights if i.sentiment is not Sentiment.NEGATIVE],
        competitor_gaps=[i.topic for i in negative],
        differentiation_ideas=[i.topic for i in positive],
        keywords=sorted({i.topic for i in insights}),
        opportunity_score=result.score,
        dimension_scores=dimension_scores,
        score_version=SCORE_VERSION,
        confidence=result.confidence,
        missing_dimensions=missing,
        risk_flags=risk_flags,
    )


def _audience(negative: list[InsightOutput], positive: list[InsightOutput]) -> str | None:
    top_neg = negative[0].topic if negative else None
    if top_neg:
        return f"Buyers concerned about {top_neg}, based on {len(negative)} negative theme(s)."
    if positive:
        return f"Buyers who value {positive[0].topic}, based on {len(positive)} positive theme(s)."
    return None


# Re-export weights for introspection / explainability.
__all__ = ["OPPORTUNITY_WEIGHTS", "SCORE_VERSION", "CardDraft", "build_card"]
