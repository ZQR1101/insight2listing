"""Canonical field definitions and automatic field mapping.

A source file's columns are normalised to canonical keys. Auto-detection maps
a header to a canonical field via an alias table; callers may also supply an
explicit mapping which takes precedence. See plan section 6.2 / 8.4.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.enums import ImportTarget

_NON_ALNUM = re.compile(r"[^0-9a-z_]")

#: Trailing markers that can follow a field name in a real export (e.g. "price_usd").
_CURRENCY_SUFFIXES = ("usd", "eur", "cny", "gbp", "jpy", "aud", "cad")


def normalise_header(value: str) -> str:
    """Lowercase, strip and collapse a header to snake_case for matching."""
    lowered = value.lower()
    cleaned = _NON_ALNUM.sub("_", lowered).strip("_")
    return re.sub(r"_+", "_", cleaned)


@dataclass(frozen=True)
class CanonicalField:
    key: str
    required: bool = False
    aliases: tuple[str, ...] = ()


#: Canonical fields available for the ``products`` import target.
PRODUCT_FIELDS: dict[str, CanonicalField] = {
    "external_id": CanonicalField("external_id", aliases=("asin", "sku", "product_id")),
    "category": CanonicalField("category"),
    "title": CanonicalField("title", required=True, aliases=("product_title", "name")),
    "brand": CanonicalField("brand"),
    "price": CanonicalField("price", aliases=("listing_price", "unit_price")),
    "currency": CanonicalField("currency"),
    "rating": CanonicalField("rating", aliases=("star_rating", "stars", "avg_rating")),
    "review_count": CanonicalField("review_count", aliases=("reviews", "num_reviews")),
    "observed_at": CanonicalField("observed_at", aliases=("observed_date", "as_of")),
}

#: Canonical fields available for the ``reviews`` import target.
REVIEW_FIELDS: dict[str, CanonicalField] = {
    "product_external_id": CanonicalField(
        "product_external_id", aliases=("product_id", "asin", "external_id")
    ),
    "external_review_id": CanonicalField("external_review_id", aliases=("review_id",)),
    "rating": CanonicalField("rating", aliases=("stars", "star_rating")),
    "title": CanonicalField("title", aliases=("review_title", "subject")),
    "body": CanonicalField("body", required=True, aliases=("review", "comment", "review_text")),
    "language": CanonicalField("language"),
    "verified_purchase": CanonicalField("verified_purchase", aliases=("verified",)),
    "reviewed_at": CanonicalField("reviewed_at", aliases=("date", "review_date", "date_of_review")),
}


def fields_for(target: ImportTarget) -> dict[str, CanonicalField]:
    if target is ImportTarget.PRODUCTS:
        return PRODUCT_FIELDS
    if target is ImportTarget.REVIEWS:
        return REVIEW_FIELDS
    raise ValueError(f"unknown import target: {target}")


def _alias_index(target: ImportTarget) -> dict[str, str]:
    index: dict[str, str] = {}
    for canonical in fields_for(target).values():
        index[canonical.key] = canonical.key
        for alias in canonical.aliases:
            index[alias] = canonical.key
    return index


@dataclass(slots=True)
class MappingResult:
    #: source header -> canonical key (only for recognised columns)
    mapping: dict[str, str] = field(default_factory=dict)
    #: headers that could not be matched to any canonical field
    unresolved: list[str] = field(default_factory=list)


def auto_map(headers: list[str], target: ImportTarget) -> MappingResult:
    """Infer a source-header to canonical-key mapping."""
    index = _alias_index(target)
    mapping: dict[str, str] = {}
    unresolved: list[str] = []
    for header in headers:
        key = normalise_header(header)
        canonical = index.get(key)
        if canonical is None:
            canonical = _match_with_currency_suffix(key, index)
        if canonical is None or header in mapping:
            unresolved.append(header)
        else:
            mapping[header] = canonical
    return MappingResult(mapping=mapping, unresolved=unresolved)


def _match_with_currency_suffix(key: str, index: dict[str, str]) -> str | None:
    """Retry a header like ``price_usd`` against ``price`` after dropping the suffix."""
    for suffix in _CURRENCY_SUFFIXES:
        marker = f"_{suffix}"
        if key.endswith(marker):
            base = key[: -len(marker)]
            canonical = index.get(base)
            if canonical is not None:
                return canonical
    return None


def apply_mapping(
    headers: list[str], target: ImportTarget, explicit: list[tuple[str, str]]
) -> tuple[MappingResult, list[str]]:
    """Apply an explicit header->canonical mapping merged with auto-detection.

    Returns ``(mapping_result, mapping_warnings)``. Explicit entries win;
    unrecognised explicit targets produce warnings.
    """
    auto = auto_map(headers, target)
    canonical_keys = {f.key for f in fields_for(target).values()}
    warnings: list[str] = []
    for source_field, target_field in explicit:
        if target_field not in canonical_keys:
            warnings.append(f"unknown canonical field '{target_field}' ignored")
            continue
        if source_field not in headers:
            warnings.append(f"source field '{source_field}' not present in file")
            continue
        auto.mapping[source_field] = target_field
    return auto, warnings
