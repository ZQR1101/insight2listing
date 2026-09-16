"""Rule-template Listing generator (plan section 12.3).

Deterministic, fact-bound assembly — no LLM. Hard constraints:

- only confirmed, non-expired facts may back a claim (section 11.3);
- unknown attributes are reported as missing, never invented;
- every bullet records the fact / insight ids it was built from;
- insights without a supporting fact never become selling points (a consumer
  wish is never presented as an existing capability).
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field

from app.core.enums import FactType, Sentiment
from app.listings.rules import (
    MAX_BULLETS,
    MAX_SEARCH_TERM_BYTES,
    CheckReport,
    check_fact_usage,
    check_listing,
)

MODEL = "rule-template-v1"
PROMPT_VERSION = "listing-template-v1"
MAX_TITLE_CHARS = 200

#: Order in which plain fact bullets fill remaining slots.
_FACT_BULLET_ORDER: tuple[FactType, ...] = (
    FactType.ACCESSORY,
    FactType.MATERIAL,
    FactType.SIZE,
    FactType.CAPACITY,
    FactType.USAGE_LIMITATION,
    FactType.CERTIFICATION,
    FactType.COLOR,
    FactType.WEIGHT,
)

_LEADINS: dict[str, str] = {
    FactType.MATERIAL.value: "MATERIAL",
    FactType.SIZE.value: "SIZE",
    FactType.WEIGHT.value: "WEIGHT",
    FactType.CAPACITY.value: "CAPACITY",
    FactType.ACCESSORY.value: "WHAT'S INCLUDED",
    FactType.COLOR.value: "COLOR",
    FactType.USAGE_LIMITATION.value: "PLEASE NOTE",
    FactType.CERTIFICATION.value: "CERTIFICATION",
}

#: Attribute categories the facts centre expects (section 6.6).
_EXPECTED_ATTRIBUTES: tuple[str, ...] = (
    FactType.MATERIAL.value,
    FactType.SIZE.value,
    FactType.CAPACITY.value,
    FactType.ACCESSORY.value,
    FactType.USAGE_LIMITATION.value,
)

#: Descriptive labels used in the description paragraph.
_LABELS: dict[str, str] = {
    FactType.MATERIAL.value: "Material",
    FactType.SIZE.value: "Size",
    FactType.WEIGHT.value: "Weight",
    FactType.CAPACITY.value: "Capacity",
    FactType.ACCESSORY.value: "Included",
    FactType.COLOR.value: "Colour",
    FactType.CERTIFICATION.value: "Certification",
}


@dataclass(slots=True)
class FactInput:
    id: uuid.UUID
    fact_type: str
    value: str
    unit: str | None = None


@dataclass(slots=True)
class InsightInput:
    id: uuid.UUID
    topic: str
    sentiment: str


@dataclass(slots=True)
class BulletDraft:
    text: str
    fact_ids: list[str] = field(default_factory=list)
    insight_ids: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "text": self.text,
            "fact_ids": self.fact_ids,
            "insight_ids": self.insight_ids,
        }


@dataclass(slots=True)
class ListingDraft:
    title: str
    bullet_points: list[BulletDraft]
    description: str
    search_terms: str
    fact_check: CheckReport
    rule_check: CheckReport
    missing_attributes: list[str]
    input_snapshot: dict[str, object]
    model: str = MODEL
    prompt_version: str = PROMPT_VERSION

    @property
    def input_snapshot_id(self) -> str:
        digest = hashlib.sha256(repr(sorted(self.input_snapshot.items())).encode()).hexdigest()
        return f"snap-{digest[:16]}"

    def bullet_texts(self) -> list[str]:
        return [b.text for b in self.bullet_points]


def _value_with_unit(fact: FactInput) -> str:
    return f"{fact.value} {fact.unit}".strip() if fact.unit else fact.value


def _truncate_words(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    return cut[: cut.rfind(" ")].rstrip(" ,-")


def generate_listing(
    *,
    product_title: str,
    facts: list[FactInput],
    insights: list[InsightInput],
) -> ListingDraft:
    """Assemble a listing from confirmed facts and accepted insights only."""
    facts_by_type: dict[str, list[FactInput]] = {}
    for fact in facts:
        facts_by_type.setdefault(fact.fact_type, []).append(fact)

    bullets: list[BulletDraft] = []

    # 1. Traceable selling points: an accepted pain-point insight backed by a
    #    confirmed fact whose value mentions the topic.
    matched_fact_ids: set[uuid.UUID] = set()
    negative = [i for i in insights if i.sentiment == Sentiment.NEGATIVE.value]
    negative.sort(key=lambda i: i.topic)
    for insight in negative:
        if len(bullets) >= 2 or len(bullets) >= MAX_BULLETS:
            break
        token = insight.topic.lower()
        for fact in facts:
            if fact.id in matched_fact_ids:
                continue
            if token in fact.value.lower():
                bullets.append(
                    BulletDraft(
                        text=f"{insight.topic.upper()}: {_value_with_unit(fact)}.",
                        fact_ids=[str(fact.id)],
                        insight_ids=[str(insight.id)],
                    )
                )
                matched_fact_ids.add(fact.id)
                break

    # 2. Plain fact bullets in priority order.
    for fact_type in _FACT_BULLET_ORDER:
        if len(bullets) >= MAX_BULLETS:
            break
        group = facts_by_type.get(fact_type.value, [])
        for fact in group:
            if len(bullets) >= MAX_BULLETS:
                break
            if fact.id in matched_fact_ids:
                continue
            leadin = _LEADINS.get(fact_type.value, fact_type.value.upper())
            bullets.append(
                BulletDraft(text=f"{leadin}: {_value_with_unit(fact)}.", fact_ids=[str(fact.id)])
            )

    # 3. Title: product title + confirmed material/size phrases.
    phrases = [
        _value_with_unit(f)
        for f in facts
        if f.fact_type in (FactType.MATERIAL.value, FactType.SIZE.value)
    ]
    title = product_title
    if phrases:
        title = f"{product_title} - {', '.join(phrases)}"
    title = _truncate_words(title, MAX_TITLE_CHARS)

    # 4. Description: confirmed facts only.
    sentences: list[str] = []
    for ftype, label in _LABELS.items():
        group = facts_by_type.get(ftype, [])
        if group:
            joined = "; ".join(_value_with_unit(f) for f in group)
            sentences.append(f"{label}: {joined}.")
    limitations = facts_by_type.get(FactType.USAGE_LIMITATION.value, [])
    for limitation in limitations:
        sentences.append(f"Note: {_value_with_unit(limitation)}.")
    description = f"{title}. " + " ".join(sentences) if sentences else f"{title}."

    # 5. Search terms: insight topics + fact words, deduped, byte-limited.
    terms: list[str] = []
    for insight in insights:
        topic = insight.topic.lower()
        if topic not in terms:
            terms.append(topic)
    for fact in facts:
        for word in fact.value.lower().replace(",", " ").split():
            if len(word) >= 3 and word not in terms:
                terms.append(word)
    search_terms = ""
    for term in terms:
        candidate = f"{search_terms} {term}".strip()
        if len(candidate.encode("utf-8")) > MAX_SEARCH_TERM_BYTES:
            break
        search_terms = candidate

    # 6. Checks.
    confirmed_ids = {str(f.id) for f in facts}
    bullet_dicts = [b.as_dict() for b in bullets]
    fact_check = check_fact_usage(bullets=bullet_dicts, confirmed_fact_ids=confirmed_ids)
    rule_check = check_listing(
        title=title,
        bullets=[b.text for b in bullets],
        description=description,
        search_terms=search_terms,
    )

    missing = [a for a in _EXPECTED_ATTRIBUTES if a not in facts_by_type]

    snapshot: dict[str, object] = {
        "product_title": product_title,
        "fact_ids": sorted(confirmed_ids),
        "insight_ids": sorted(str(i.id) for i in insights),
        "model": MODEL,
        "prompt_version": PROMPT_VERSION,
    }

    return ListingDraft(
        title=title,
        bullet_points=bullets,
        description=description,
        search_terms=search_terms,
        fact_check=fact_check,
        rule_check=rule_check,
        missing_attributes=missing,
        input_snapshot=snapshot,
    )
