"""Deterministic Creative Brief builder (plan section 13.4).

The brief is assembled from confirmed facts and accepted insights only. It
carries the section 13.3 prohibitions verbatim so that neither the engine nor
a human reviewer has to remember them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.enums import AssetType, FactType, Sentiment

#: §13.3 prohibitions that apply to every asset.
BASE_PROHIBITIONS: tuple[str, ...] = (
    "do not invent product structures that do not exist",
    "do not add accessories that are not included",
    "do not change the product colour or variant",
    "no promotional text, logos or watermarks",
)

#: Extra prohibitions per asset type (main image is the strictest, section 13.3).
MAIN_IMAGE_EXTRA: tuple[str, ...] = (
    "main image must be based on the real product photo",
    "main image must not contain any added text or graphics",
)

_PURPOSE: dict[AssetType, str] = {
    AssetType.MAIN_IMAGE_EDIT: "Clean main-image presentation of the real product.",
    AssetType.LIFESTYLE_IMAGE: "Show the product in a realistic usage scene.",
    AssetType.FEATURE_IMAGE: "Highlight the key features of the product.",
    AssetType.COMPARISON_IMAGE: "Compare variants or sizes side by side.",
    AssetType.SIZE_IMAGE: "Communicate dimensions clearly.",
    AssetType.DETAIL_PAGE_SECTION: "Detail-page visual section supporting the copy.",
}

#: Fact categories that inform each asset type.
_FACT_HINTS: dict[AssetType, tuple[FactType, ...]] = {
    AssetType.MAIN_IMAGE_EDIT: (FactType.MATERIAL, FactType.COLOR),
    AssetType.LIFESTYLE_IMAGE: (FactType.ACCESSORY, FactType.CAPACITY),
    AssetType.FEATURE_IMAGE: (FactType.MATERIAL, FactType.CAPACITY, FactType.ACCESSORY),
    AssetType.COMPARISON_IMAGE: (FactType.COLOR, FactType.SIZE),
    AssetType.SIZE_IMAGE: (FactType.SIZE, FactType.WEIGHT, FactType.CAPACITY),
    AssetType.DETAIL_PAGE_SECTION: (FactType.USAGE_LIMITATION, FactType.CERTIFICATION),
}


@dataclass(slots=True)
class BriefInput:
    fact_type: str
    value: str
    unit: str | None = None


@dataclass(slots=True)
class InsightBriefInput:
    topic: str
    sentiment: str


@dataclass(slots=True)
class CreativeBrief:
    asset_type: AssetType
    purpose: str
    must_show: list[str] = field(default_factory=list)
    must_avoid: list[str] = field(default_factory=list)
    overlay_lines: list[str] = field(default_factory=list)
    source_required: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "asset_type": self.asset_type.value,
            "purpose": self.purpose,
            "must_show": self.must_show,
            "must_avoid": self.must_avoid,
            "overlay_lines": self.overlay_lines,
            "source_required": self.source_required,
        }

    def to_prompt(self) -> str:
        parts = [self.purpose]
        if self.must_show:
            parts.append("Show: " + "; ".join(self.must_show) + ".")
        parts.append("Avoid: " + "; ".join(self.must_avoid) + ".")
        if self.overlay_lines:
            parts.append("Text will be typeset programmatically, do not render text in the image.")
        return " ".join(parts)


def build_brief(
    *,
    asset_type: AssetType,
    facts: list[BriefInput],
    insights: list[InsightBriefInput],
) -> CreativeBrief:
    """Build the brief; every input is already fact/insight-gated upstream."""
    wanted = _FACT_HINTS.get(asset_type, ())
    must_show = [
        f"{f.fact_type}: {f.value}{f' {f.unit}' if f.unit else ''}"
        for f in facts
        if f.fact_type in {wt.value for wt in wanted}
    ]
    positives = [i.topic for i in insights if i.sentiment == Sentiment.POSITIVE.value]
    if positives:
        must_show.append(f"reflect buyer priorities: {', '.join(positives[:3])}")

    overlay_lines: list[str] = []
    if asset_type in (AssetType.SIZE_IMAGE, AssetType.FEATURE_IMAGE):
        overlay_lines = [
            f"{f.value}{f' {f.unit}' if f.unit else ''}"
            for f in facts
            if f.fact_type in (FactType.SIZE.value, FactType.CAPACITY.value)
        ]

    avoid = list(BASE_PROHIBITIONS)
    if asset_type is AssetType.MAIN_IMAGE_EDIT:
        avoid.extend(MAIN_IMAGE_EXTRA)

    return CreativeBrief(
        asset_type=asset_type,
        purpose=_PURPOSE[asset_type],
        must_show=must_show,
        must_avoid=avoid,
        overlay_lines=overlay_lines,
        source_required=asset_type is AssetType.MAIN_IMAGE_EDIT,
    )
