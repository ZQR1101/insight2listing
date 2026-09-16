"""Unit tests for the deterministic insight engine."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from app.core.enums import EvidenceType, Sentiment, Severity
from app.opportunities.engine import ReviewInput, analyze

NOW = datetime(2026, 9, 1, tzinfo=UTC)


def _r(body: str, rating: int, product_id: uuid.UUID, days_ago: int = 0) -> ReviewInput:
    return ReviewInput(
        id=uuid.uuid4(),
        product_id=product_id,
        rating=rating,
        body=body,
        reviewed_at=NOW - timedelta(days=days_ago),
    )


def test_analyze_finds_negative_pain_topic_with_evidence() -> None:
    pid = uuid.uuid4()
    reviews = [
        _r("the nozzle leaks oil everywhere", 1, pid),
        _r("nozzle leaks after a week", 1, pid),
        _r("seriously leaks oil, bad", 2, pid),
        _r("great fine mist control", 5, pid),
        _r("love the fine mist", 5, pid),
    ]
    insights = analyze(reviews)

    leak = next((i for i in insights if i.topic == "leaks"), None)
    assert leak is not None
    assert leak.sentiment is Sentiment.NEGATIVE
    assert leak.frequency >= 3
    assert leak.severity is Severity.HIGH
    assert leak.rating_impact > 50
    assert leak.cross_competitor_score == 30.0  # single product
    assert leak.confidence >= 0.6
    types = {e.evidence_type for e in leak.evidence}
    assert EvidenceType.REVIEW_EXCERPT in types
    assert EvidenceType.AGGREGATED_TOPIC in types
    assert any(e.excerpt for e in leak.evidence)

    mist = next((i for i in insights if i.topic == "mist"), None)
    assert mist is not None
    assert mist.sentiment is Sentiment.POSITIVE


def test_analyze_cross_competitor_when_topic_spans_products() -> None:
    p1, p2 = uuid.uuid4(), uuid.uuid4()
    reviews = [
        _r("handle leaks badly", 1, p1),
        _r("also leaks oil", 1, p1),
        _r("the lid leaks over time", 1, p2),
        _r("yes it leaks too", 2, p2),
    ]
    insights = analyze(reviews)
    leak = next((i for i in insights if i.topic == "leaks"), None)
    assert leak is not None
    assert leak.cross_competitor_score == 80.0


def test_analyze_empty() -> None:
    assert analyze([]) == []


def test_analyze_single_mention_is_suppressed() -> None:
    # A keyword mentioned only once should not form a cluster (>=2 required).
    pid = uuid.uuid4()
    insights = analyze([_r("rarely mentioned widget", 1, pid)])
    assert all(i.topic != "widget" for i in insights)
