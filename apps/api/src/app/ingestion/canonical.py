"""Canonical record types and row normalisation.

Rows are converted from (source header, value, mapping) into strongly typed
canonical records. This is the boundary between raw source data and the
business domain (plan section 8.4). Values that fail coercion or that are
missing where required produce :class:`RowIssue` entries instead of silently
being filled in.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.ingestion.errors import RowIssue

_TRUTHY = {"true", "1", "yes", "y", "verified"}


def _strip(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    return str(value)


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    text = str(value).strip()
    if text.startswith("'"):  # formula-escaped cell, treat as non-numeric
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    f = _to_float(value)
    if f is None:
        return None
    return int(f)


def _to_decimal(value: Any) -> Decimal | None:
    f = _to_float(value)
    if f is None:
        return None
    return Decimal(f).quantize(Decimal("0.01"))


def _to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return None
    return str(value).strip().lower() in _TRUTHY


_ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _to_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not _ISO_RE.match(text):
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


@dataclass(slots=True)
class CanonicalProduct:
    external_id: str | None
    category: str | None
    title: str
    brand: str | None
    price: Decimal | None
    currency: str | None
    rating: float | None
    review_count: int | None
    observed_at: datetime | None


@dataclass(slots=True)
class CanonicalReview:
    product_external_id: str | None
    external_review_id: str | None
    rating: int | None
    title: str | None
    body: str
    language: str | None
    verified_purchase: bool | None
    reviewed_at: datetime | None


def _value(row: dict[str, Any], mapping: dict[str, str], canonical_key: str) -> Any:
    """Return the raw value for a canonical key, if it was mapped."""
    header = next((h for h, k in mapping.items() if k == canonical_key), None)
    if header is None:
        return None
    value = row.get(header)
    return value


def normalise_product(row: dict[str, Any], mapping: dict[str, str], row_number: int) -> tuple[
    CanonicalProduct | None, list[RowIssue]
]:
    issues: list[RowIssue] = []

    title = _strip(_value(row, mapping, "title"))
    if title is None:
        issues.append(
            RowIssue(row_number, "missing required field", field="title", severity="error")
        )
    external_id = _strip(_value(row, mapping, "external_id"))
    category = _strip(_value(row, mapping, "category"))
    brand = _strip(_value(row, mapping, "brand"))
    currency = _strip(_value(row, mapping, "currency")) or "USD"
    price = _to_decimal(_value(row, mapping, "price"))
    rating = _to_float(_value(row, mapping, "rating"))
    review_count = _to_int(_value(row, mapping, "review_count"))
    observed_at = _to_datetime(_value(row, mapping, "observed_at"))

    if title is None:
        return None, issues
    return (
        CanonicalProduct(
            external_id=external_id,
            category=category,
            title=title,
            brand=brand,
            price=price,
            currency=currency,
            rating=rating,
            review_count=review_count,
            observed_at=observed_at,
        ),
        issues,
    )


def normalise_review(row: dict[str, Any], mapping: dict[str, str], row_number: int) -> tuple[
    CanonicalReview | None, list[RowIssue]
]:
    issues: list[RowIssue] = []
    body = _strip(_value(row, mapping, "body"))
    if body is None:
        issues.append(
            RowIssue(row_number, "missing required field", field="body", severity="error")
        )

    product_external_id = _strip(_value(row, mapping, "product_external_id"))
    external_review_id = _strip(_value(row, mapping, "external_review_id"))
    rating = _to_int(_value(row, mapping, "rating"))
    title = _strip(_value(row, mapping, "title"))
    language = _strip(_value(row, mapping, "language"))
    verified_purchase = _to_bool(_value(row, mapping, "verified_purchase"))
    reviewed_at = _to_datetime(_value(row, mapping, "reviewed_at"))

    if body is None:
        return None, issues
    return (
        CanonicalReview(
            product_external_id=product_external_id,
            external_review_id=external_review_id,
            rating=rating,
            title=title,
            body=body,
            language=language,
            verified_purchase=verified_purchase,
            reviewed_at=reviewed_at,
        ),
        issues,
    )
