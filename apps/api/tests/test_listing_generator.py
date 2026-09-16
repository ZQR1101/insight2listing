"""Unit tests for the rule-template listing generator (plan section 12.3)."""

from __future__ import annotations

import uuid

from app.core.enums import FactType, Sentiment
from app.listings.generator import FactInput, InsightInput, generate_listing
from app.listings.rules import MAX_BULLETS, MAX_SEARCH_TERM_BYTES, MAX_TITLE_CHARS


def _fact(value: str, fact_type: FactType, unit: str | None = None) -> FactInput:
    return FactInput(id=uuid.uuid4(), fact_type=fact_type.value, value=value, unit=unit)


def test_generates_traceable_pain_point_bullet() -> None:
    gasket_fact = _fact("silicone gasket seal", FactType.MATERIAL)
    insight = InsightInput(
        id=uuid.uuid4(), topic="gasket", sentiment=Sentiment.NEGATIVE.value
    )
    draft = generate_listing(
        product_title="Glass Oil Sprayer",
        facts=[gasket_fact, _fact("200", FactType.CAPACITY, "ml")],
        insights=[insight],
    )
    gasket_bullets = [
        b for b in draft.bullet_points if gasket_fact.id in {uuid.UUID(f) for f in b.fact_ids}
        and insight.id in {uuid.UUID(i) for i in b.insight_ids}
    ]
    assert len(gasket_bullets) == 1
    assert "GASKET" in gasket_bullets[0].text
    assert "silicone gasket seal" in gasket_bullets[0].text


def test_unmentioned_insight_does_not_become_a_claim() -> None:
    """A pain point with no supporting fact must not turn into a capability."""
    insight = InsightInput(
        id=uuid.uuid4(), topic="bpa", sentiment=Sentiment.NEGATIVE.value
    )
    draft = generate_listing(
        product_title="Glass Oil Sprayer",
        facts=[_fact("200", FactType.CAPACITY, "ml")],
        insights=[insight],
    )
    assert all("bpa" not in b.text.lower() for b in draft.bullet_points)
    assert all(str(insight.id) not in b.insight_ids for b in draft.bullet_points)


def test_usage_limitation_and_accessory_bullets() -> None:
    draft = generate_listing(
        product_title="Car Trash Can",
        facts=[
            _fact("foldable liner bag", FactType.ACCESSORY),
            _fact("hand wash only", FactType.USAGE_LIMITATION),
        ],
        insights=[],
    )
    texts = [b.text for b in draft.bullet_points]
    assert any(t.startswith("WHAT'S INCLUDED") for t in texts)
    assert any(t.startswith("PLEASE NOTE") and "hand wash only" in t for t in texts)


def test_title_within_limits_and_contains_facts() -> None:
    draft = generate_listing(
        product_title="Compression Packing Cubes",
        facts=[_fact("nylon", FactType.MATERIAL), _fact("30 x 20 x 10", FactType.SIZE, "cm")],
        insights=[],
    )
    assert len(draft.title) <= MAX_TITLE_CHARS
    assert "Compression Packing Cubes" in draft.title
    assert "nylon" in draft.title


def test_search_terms_byte_limited_and_deduped() -> None:
    draft = generate_listing(
        product_title="Glass Oil Sprayer",
        facts=[_fact("borosilicate glass body", FactType.MATERIAL)] * 1,
        insights=[
            InsightInput(id=uuid.uuid4(), topic="mist", sentiment="positive"),
            InsightInput(id=uuid.uuid4(), topic="mist", sentiment="positive"),
        ],
    )
    assert len(draft.search_terms.encode("utf-8")) <= MAX_SEARCH_TERM_BYTES
    assert draft.search_terms.count("mist") == 1


def test_missing_attributes_reported() -> None:
    draft = generate_listing(
        product_title="Glass Oil Sprayer",
        facts=[_fact("nylon", FactType.MATERIAL)],
        insights=[],
    )
    assert "capacity" in draft.missing_attributes
    assert "accessory" in draft.missing_attributes
    assert "material" not in draft.missing_attributes


def test_fact_and_rule_checks_run() -> None:
    draft = generate_listing(
        product_title="Glass Oil Sprayer",
        facts=[_fact("borosilicate glass", FactType.MATERIAL)],
        insights=[],
    )
    assert draft.fact_check.passed is True
    assert draft.rule_check.passed is True
    assert draft.model == "rule-template-v1"
    assert draft.input_snapshot_id.startswith("snap-")


def test_bullet_cap_respected() -> None:
    draft = generate_listing(
        product_title="P",
        facts=[
            _fact("nylon", FactType.MATERIAL),
            _fact("30 x 20", FactType.SIZE, "cm"),
            _fact("2 l", FactType.CAPACITY),
            _fact("liner", FactType.ACCESSORY),
            _fact("hand wash", FactType.USAGE_LIMITATION),
            _fact("500 g", FactType.WEIGHT, "g"),
            _fact("black", FactType.COLOR),
        ],
        insights=[],
    )
    assert len(draft.bullet_points) <= MAX_BULLETS
