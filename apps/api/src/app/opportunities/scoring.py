"""Deterministic opportunity & pain-point scoring (plan section 10).

Weights follow the plan. Dimensions that are unavailable are *not* counted as
zero — they are excluded from the weighted pool, reported in ``missing``, and
lower the confidence by their absent weight (see section 10.5). All input
dimension values are expected to be normalised to 0..100.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Pain-point opportunity score weights (section 10.3).
PAIN_POINT_WEIGHTS: dict[str, float] = {
    "frequency": 0.25,
    "severity": 0.20,
    "rating_impact": 0.20,
    "cross_competitor": 0.15,
    "recency": 0.10,
    "solvability": 0.10,
}

#: Product opportunity score weights (section 10.2).
OPPORTUNITY_WEIGHTS: dict[str, float] = {
    "demand": 0.20,
    "growth": 0.15,
    "gap": 0.15,
    "pain": 0.20,
    "differentiation": 0.10,
    "unit_econ": 0.10,
    "risk": 0.10,
}

SCORE_VERSION = "opportunity-v1"


@dataclass(slots=True)
class WeightedScore:
    score: float | None
    confidence: float
    missing: list[str] = field(default_factory=list)


def weighted_score(
    values: dict[str, float | None], weights: dict[str, float]
) -> WeightedScore:
    """Weighted mean over available dimensions (missing excluded, not zeroed)."""
    present = {k: v for k, v in values.items() if v is not None}
    pool = sum(weights[k] for k in weights if k in present)
    if pool <= 0:
        return WeightedScore(score=None, confidence=0.0, missing=list(weights))

    total = sum(weights[k] * present[k] for k in present)
    confidence = round(pool, 2)
    missing = [k for k in weights if k not in present]

    # Clamp drift from rounding into 0..100.
    score = min(100.0, max(0.0, total / pool))
    return WeightedScore(score=round(score, 2), confidence=confidence, missing=missing)


def pain_point_score(
    *,
    frequency: int,
    severity: float,
    rating_impact: float,
    cross_competitor: float,
    recency: float,
    solvability: float | None = None,
) -> WeightedScore:
    """Score a single pain point, all metrics normalised to 0..100."""
    return weighted_score(
        {
            "frequency": _frequency01(frequency) * 100,
            "severity": severity,
            "rating_impact": rating_impact,
            "cross_competitor": cross_competitor,
            "recency": recency,
            "solvability": solvability,
        },
        PAIN_POINT_WEIGHTS,
    )


def opportunity_score(
    *,
    demand: float | None = None,
    growth: float | None = None,
    gap: float | None = None,
    pain: float | None = None,
    differentiation: float | None = None,
    unit_econ: float | None = None,
    risk: float | None = None,
) -> WeightedScore:
    """Score a product opportunity across the seven plan dimensions."""
    return weighted_score(
        {
            "demand": demand,
            "growth": growth,
            "gap": gap,
            "pain": pain,
            "differentiation": differentiation,
            "unit_econ": unit_econ,
            "risk": risk,
        },
        OPPORTUNITY_WEIGHTS,
    )


def _frequency01(frequency: int) -> float:
    """Map a raw mention count to a saturated 0..1 scale."""
    if frequency <= 0:
        return 0.0
    return min(1.0, 0.2 + 0.8 * (1.0 - 1.0 / float(frequency)))
