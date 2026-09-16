"""Unit tests for the deterministic scoring functions (plan section 10)."""

from __future__ import annotations

from app.opportunities.scoring import (
    OPPORTUNITY_WEIGHTS,
    PAIN_POINT_WEIGHTS,
    opportunity_score,
    pain_point_score,
    weighted_score,
)


def test_weighted_score_uses_available_weight_pool() -> None:
    result = weighted_score({"a": 50.0, "b": 70.0}, {"a": 0.5, "b": 0.5})
    assert result.score == 60.0
    assert result.confidence == 1.0
    assert result.missing == []


def test_weighted_score_missing_dimension_not_zeroed() -> None:
    result = weighted_score({"a": 50.0}, {"a": 0.5, "b": 0.5})
    # Missing b is excluded (not zeroed), confidence is the covered weight.
    assert result.score == 50.0
    assert result.confidence == 0.5
    assert result.missing == ["b"]


def test_weighted_score_all_missing() -> None:
    result = weighted_score({}, {"a": 0.5, "b": 0.5})
    assert result.score is None
    assert result.confidence == 0.0


def test_pain_point_score_shapes() -> None:
    result = pain_point_score(
        frequency=12,
        severity=85.0,
        rating_impact=70.0,
        cross_competitor=80.0,
        recency=60.0,
    )
    assert result.score is not None
    assert 0 <= result.score <= 100
    assert result.confidence < 1.0  # solvability not provided
    assert "solvability" in result.missing


def test_opportunity_score_only_review_dimensions() -> None:
    result = opportunity_score(pain=60.0, gap=40.0, differentiation=70.0)
    assert result.score is not None
    assert abs(result.confidence - (0.20 + 0.15 + 0.10)) < 1e-9
    for dim in ("demand", "growth", "unit_econ", "risk"):
        assert dim in result.missing


def test_weights_encode_plan() -> None:
    assert sum(PAIN_POINT_WEIGHTS.values()) == 1.0
    assert sum(OPPORTUNITY_WEIGHTS.values()) == 1.0
    assert abs(sum(PAIN_POINT_WEIGHTS.values()) - 1.0) < 1e-9
