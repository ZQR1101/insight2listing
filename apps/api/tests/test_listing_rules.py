"""Unit tests for Amazon listing platform rules (plan section 12.4)."""

from __future__ import annotations

from app.listings.rules import (
    MAX_BULLETS,
    MAX_TITLE_CHARS,
    check_fact_usage,
    check_listing,
)


def _clean(**overrides):
    payload = {
        "title": "Glass Oil Sprayer - 200 ml, stainless steel",
        "bullets": [
            "MATERIAL: borosilicate glass body.",
            "CAPACITY: 200 ml capacity.",
            "PLEASE NOTE: hand wash only.",
        ],
        "description": "Glass oil sprayer with 200 ml capacity.",
        "search_terms": "oil sprayer glass mist",
    }
    payload.update(overrides)
    return check_listing(**payload)


def test_clean_listing_passes() -> None:
    report = _clean()
    assert report.passed is True


def test_title_over_hard_limit_is_error() -> None:
    report = _clean(title="x" * (MAX_TITLE_CHARS + 1))
    assert report.passed is False
    assert any("200" in i.issue for i in report.issues if i.field == "title")


def test_title_over_recommended_is_warning_only() -> None:
    report = _clean(title="y" * 150)
    assert report.passed is True
    assert any(i.severity == "warning" for i in report.issues if i.field == "title")


def test_too_many_bullets_is_error() -> None:
    bullets = [f"Bullet number {i} with enough text." for i in range(MAX_BULLETS + 1)]
    report = _clean(bullets=bullets)
    assert report.passed is False


def test_search_terms_byte_limit() -> None:
    report = _clean(search_terms="word " * 60)
    assert report.passed is False
    assert any(i.field == "search_terms" for i in report.issues)


def test_forbidden_claim_is_error() -> None:
    report = _clean(
        description="The best oil sprayer you can buy, guaranteed."
    )
    assert report.passed is False
    assert any("promotional" in i.issue or "absolute" in i.issue for i in report.issues)


def test_caps_word_in_title_is_warning() -> None:
    report = _clean(title="AWESOME Glass Oil Sprayer - 200 ml")
    assert report.passed is True
    assert any("AWESOME" in i.issue for i in report.issues)


def test_keyword_stuffing_is_warning() -> None:
    report = _clean(
        description="sprayer sprayer sprayer sprayer sprayer sprayer for oil."
    )
    assert any("stuffing" in i.issue for i in report.issues)


def test_fact_usage_unconfirmed_reference_fails() -> None:
    report = check_fact_usage(
        bullets=[{"text": "b", "fact_ids": ["f-1"], "insight_ids": []}],
        confirmed_fact_ids={"f-2"},
    )
    assert report.passed is False


def test_fact_usage_confirmed_references_pass() -> None:
    report = check_fact_usage(
        bullets=[{"text": "b", "fact_ids": ["f-1"], "insight_ids": ["i-1"]}],
        confirmed_fact_ids={"f-1"},
    )
    assert report.passed is True
