"""Pure unit tests for field mapping, canonical normalisation and dedup keys."""

from __future__ import annotations

from decimal import Decimal

from app.core.enums import ImportTarget
from app.ingestion.canonical import normalise_product, normalise_review
from app.ingestion.dedup import review_content_hash
from app.ingestion.fieldmap import auto_map


def test_auto_map_recognises_synonyms() -> None:
    headers = ["ASIN", "Product Title", "Price (USD)", "Stars", "Num Reviews"]
    result = auto_map(headers, ImportTarget.PRODUCTS)
    assert result.mapping["ASIN"] == "external_id"
    assert result.mapping["Product Title"] == "title"
    assert result.mapping["Price (USD)"] == "price"
    assert result.mapping["Stars"] == "rating"
    assert result.mapping["Num Reviews"] == "review_count"


def test_auto_map_marks_unresolved() -> None:
    headers = ["mystery_column"]
    result = auto_map(headers, ImportTarget.PRODUCTS)
    assert result.unresolved == ["mystery_column"]


def test_normalise_product_coerces_and_requires_title() -> None:
    row = {"title": "Cubes", "price": "19.99", "rating": "4.5", "review_count": "120"}
    mapping = {"title": "title", "price": "price", "rating": "rating", "review_count": "review_count"}
    product, issues = normalise_product(row, mapping, 1)
    assert issues == []
    assert product is not None
    assert product.price == Decimal("19.99")
    assert product.rating == 4.5

    bad_product, bad_issues = normalise_product({"price": "1"}, {"price": "price"}, 1)
    assert bad_product is None
    assert bad_issues[0].field == "title"


def test_normalise_review_requires_body() -> None:
    mapping = {"body": "body", "rating": "rating"}
    review, issues = normalise_review({"body": "", "rating": "2"}, mapping, 1)
    assert review is None
    assert issues[0].field == "body"


def test_dedup_keys_are_stable() -> None:
    from app.ingestion.canonical import CanonicalReview

    a = CanonicalReview(
        product_external_id="A", external_review_id=None, rating=1, title=None,
        body="  Great   thing!  ", language=None, verified_purchase=None, reviewed_at=None,
    )
    b = CanonicalReview(
        product_external_id="B", external_review_id=None, rating=2, title=None,
        body="great thing!", language=None, verified_purchase=None, reviewed_at=None,
    )
    assert review_content_hash(a) == review_content_hash(b)
