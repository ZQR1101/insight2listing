"""Deterministic deduplication keys (plan section 9.1 / import reports).

Re-importing the same file must not create duplicate records. Products are
keyed by external id when present, else by normalised title+brand. Reviews are
keyed by a sha256 of their normalised body.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

from app.ingestion.canonical import CanonicalProduct, CanonicalReview

_WS_RE = re.compile(r"\s+")


def normalise_text(value: str) -> str:
    """Lowercase, strip diacritics and collapse whitespace for stable hashing."""
    folded = unicodedata.normalize("NFKC", value)
    return _WS_RE.sub(" ", folded).strip().lower()


def product_key(product: CanonicalProduct) -> str:
    if product.external_id:
        return f"external:{product.external_id}"
    return f"title:{normalise_text(product.title or '')}|{normalise_text(product.brand or '')}"


def review_content_hash(review: CanonicalReview) -> str:
    """sha256 hexdigest of the normalised review body."""
    return hashlib.sha256(normalise_text(review.body).encode("utf-8")).hexdigest()
