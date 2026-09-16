"""Deterministic comment-insight engine (plan sections 9.1, 9.4).

A rule-based analyzer that is fully reproducible and offline. It clusters
reviews into themes by keyword frequency, derives sentiment/severity/impact/
recency/cross-competitor breadth/confidence from ratings and timestamps, and
binds each insight to review-excerpt evidence. No LLM is required; the provider
seam is reserved for richer semantic summaries later.
"""

from __future__ import annotations

import re
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.core.enums import EvidenceType, Sentiment, Severity

_WORD_RE = re.compile(r"[a-z0-9]{3,}")

_STOPWORDS = frozenset(
    {
        "the", "and", "for", "are", "but", "not", "you", "all", "can", "was",
        "this", "that", "with", "from", "have", "had", "has", "its", "one",
        "two", "use", "used", "using", "get", "got", "like", "just", "very",
        "really", "good", "great", "love", "would", "product", "item", "bought",
        "bottle", "bag", "bin", "after", "also", "when", "what", "them", "they",
        "well", "works", "work", "made", "make", "much", "more", "some", "than",
        "been", "your", "our", "their", "about", "into", "back", "came", "still",
    }
)

#: Metric to 0..100 mapping for the severity dimension.
_SEVERITY_VALUE = {Severity.LOW: 20, Severity.MEDIUM: 50, Severity.HIGH: 85}

_MAX_INSIGHTS_PER_PRODUCT = 8
_EXCERPT_LIMIT = 300
_RECENCY_DAYS = 30


@dataclass(slots=True)
class ReviewInput:
    id: uuid.UUID
    product_id: uuid.UUID
    rating: int | None
    body: str
    reviewed_at: datetime | None


@dataclass(slots=True)
class EvidenceDraft:
    evidence_type: EvidenceType
    source_entity_id: str | None
    excerpt: str
    support_strength: float
    observed_at: datetime | None


@dataclass(slots=True)
class InsightOutput:
    product_id: uuid.UUID
    topic: str
    summary: str
    sentiment: Sentiment
    frequency: int
    severity: Severity
    rating_impact: float  # 0..100
    recency_score: float  # 0..100
    cross_competitor_score: float  # 0..100
    confidence: float  # 0..1
    evidence: list[EvidenceDraft] = field(default_factory=list)
    severity_value: float = 0.0


def _tokens(text: str) -> list[str]:
    return [t for t in _WORD_RE.findall(text.lower()) if t not in _STOPWORDS]


def _sentiment_for(ratings: list[int]) -> Sentiment:
    if not ratings:
        return Sentiment.NEUTRAL
    avg = sum(ratings) / len(ratings)
    if avg >= 4.0:
        return Sentiment.POSITIVE
    if avg <= 2.4:
        return Sentiment.NEGATIVE
    return Sentiment.NEUTRAL


def _severity_for(negative_share: float, frequency: int) -> Severity:
    if (negative_share >= 0.5 and frequency >= 3) or (negative_share >= 0.3 and frequency >= 5):
        return Severity.HIGH
    if negative_share >= 0.25:
        return Severity.MEDIUM
    return Severity.LOW


def _confidence_for(frequency: int) -> float:
    if frequency >= 10:
        return 0.9
    if frequency >= 5:
        return 0.75
    if frequency >= 3:
        return 0.6
    if frequency >= 2:
        return 0.45
    return 0.3


def _recency_for(cluster: list[ReviewInput]) -> float:
    stamped = [r.reviewed_at for r in cluster if r.reviewed_at is not None]
    if not stamped:
        return 50.0
    newest = max(stamped)
    window_start = newest - timedelta(days=_RECENCY_DAYS)
    recent = sum(1 for d in stamped if d >= window_start)
    return round(recent / len(stamped) * 100.0, 2)


def _excerpt(body: str) -> str:
    return body.replace("\n", " ").strip()[:_EXCERPT_LIMIT]


def analyze(
    reviews: list[ReviewInput], *, max_insights_per_product: int = _MAX_INSIGHTS_PER_PRODUCT
) -> list[InsightOutput]:
    """Cluster project reviews into evidence-bound insights."""
    if not reviews:
        return []

    # token -> set(product_ids) across the whole project (cross-competitor breadth)
    token_products: dict[str, set[uuid.UUID]] = defaultdict(set)
    # (product_id, token) -> reviews mentioning the token
    clusters: dict[tuple[uuid.UUID, str], list[ReviewInput]] = defaultdict(list)

    for review in reviews:
        for token in set(_tokens(review.body)):
            token_products[token].add(review.product_id)
            clusters[(review.product_id, token)].append(review)

    # Candidate topics: within a product a keyword must appear in >=2 reviews.
    # Deterministic global ordering by project breadth, then token alphabetically.
    candidates: list[tuple[uuid.UUID, str]] = []
    seen_per_product: dict[uuid.UUID, set[str]] = defaultdict(set)
    for (product_id, token), cluster in clusters.items():
        if len(cluster) >= 2 and token not in seen_per_product[product_id]:
            seen_per_product[product_id].add(token)
            candidates.append((product_id, token))
    candidates.sort(
        key=lambda pt: (-len(token_products[pt[1]]), -len(clusters[pt]), pt[1])
    )

    produced: dict[uuid.UUID, int] = defaultdict(int)
    outputs: list[InsightOutput] = []
    for product_id, token in candidates:
        if produced[product_id] >= max_insights_per_product:
            continue
        cluster = sorted(clusters[(product_id, token)], key=lambda r: (r.rating is None, r.rating or 0))

        ratings = [r.rating for r in cluster if r.rating is not None]
        negative_share = (
            sum(1 for rt in ratings if rt <= 2) / len(ratings) if ratings else 0.5
        )
        sentiment = _sentiment_for(ratings)
        severity = _severity_for(negative_share, len(cluster))
        frequency = len(cluster)
        confidence = _confidence_for(frequency)

        source_entity_id = f"review:{cluster[0].id}"

        evidence: list[EvidenceDraft] = []
        for review in cluster[:3]:
            strength = round((6 - review.rating) / 5.0, 2) if review.rating else 0.5
            evidence.append(
                EvidenceDraft(
                    evidence_type=EvidenceType.REVIEW_EXCERPT,
                    source_entity_id=f"review:{review.id}",
                    excerpt=_excerpt(review.body),
                    support_strength=max(0.0, min(1.0, strength)),
                    observed_at=review.reviewed_at,
                )
            )
        # Aggregate evidence summarising the cluster.
        evidence.insert(
            0,
            EvidenceDraft(
                evidence_type=EvidenceType.AGGREGATED_TOPIC,
                source_entity_id=source_entity_id,
                excerpt=f"{token}: {frequency} review(s), {sentiment.value} sentiment",
                support_strength=round(confidence, 2),
                observed_at=max((r.reviewed_at for r in cluster if r.reviewed_at), default=None),
            ),
        )

        outputs.append(
            InsightOutput(
                product_id=product_id,
                topic=token,
                summary=_summary(token, frequency, sentiment, severity),
                sentiment=sentiment,
                frequency=frequency,
                severity=severity,
                rating_impact=round(negative_share * 100.0, 2),
                recency_score=_recency_for(cluster),
                cross_competitor_score=80.0 if len(token_products[token]) >= 2 else 30.0,
                confidence=round(confidence, 2),
                evidence=evidence,
                severity_value=_SEVERITY_VALUE[severity],
            )
        )
        produced[product_id] += 1

    return outputs


def _summary(topic: str, frequency: int, sentiment: Sentiment, severity: Severity) -> str:
    return (
        f"{topic} appears in {frequency} review(s) with {sentiment.value} sentiment "
        f"and {severity.value} severity."
    )
