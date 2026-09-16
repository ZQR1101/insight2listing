"""Unit tests for the visual pipeline modules (plan section 13)."""

from __future__ import annotations

import io

from PIL import Image  # type: ignore[import-untyped]

from app.core.enums import AssetType, CheckStatus
from app.images import checks
from app.images.brief import BriefInput, InsightBriefInput, build_brief
from app.images.engines import MockImageEngine, sniff_content_type
from app.images.overlay import apply_overlay


def _png(width: int = 1024, height: int = 1024, color=(200, 200, 200)) -> bytes:
    image = Image.new("RGB", (width, height), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_mock_edit_returns_source_untouched() -> None:
    import asyncio

    source = _png()
    result = asyncio.run(MockImageEngine().edit([source], "prompt"))
    assert result.content == source  # a mock must never alter the product
    assert result.content_type == "image/png"


def test_mock_generate_is_deterministic() -> None:
    import asyncio

    engine = MockImageEngine()
    a = asyncio.run(engine.generate("clean main image", 1024, 1024))
    b = asyncio.run(engine.generate("clean main image", 1024, 1024))
    assert a.content == b.content
    assert a.content_type == "image/png"
    with Image.open(io.BytesIO(a.content)) as image:
        assert image.size == (1024, 1024)


def test_sniff_content_type() -> None:
    assert sniff_content_type(_png()) == "image/png"


def test_overlay_deterministic_and_changes_bytes() -> None:
    source = _png()
    once = apply_overlay(source, ["200 ml", "hand wash only"])
    twice = apply_overlay(source, ["200 ml", "hand wash only"])
    assert once == twice  # deterministic typesetting (plan 13.5)
    assert once != source
    assert apply_overlay(source, []) == source


def test_brief_main_image_requires_source_and_bans_text() -> None:
    brief = build_brief(asset_type=AssetType.MAIN_IMAGE_EDIT, facts=[], insights=[])
    assert brief.source_required is True
    assert any("must be based on the real product" in item for item in brief.must_avoid)
    assert any("must not contain any added text" in item for item in brief.must_avoid)


def test_brief_size_image_collects_facts_and_overlay() -> None:
    brief = build_brief(
        asset_type=AssetType.SIZE_IMAGE,
        facts=[
            BriefInput(fact_type="size", value="30 x 20 x 10", unit="cm"),
            BriefInput(fact_type="material", value="nylon"),
        ],
        insights=[InsightBriefInput(topic="leaks", sentiment="negative")],
    )
    assert any("30 x 20 x 10 cm" in line for line in brief.overlay_lines)
    assert not any("nylon" in line for line in brief.must_show)  # size image ignores material
    assert "leaks" not in " ".join(brief.must_show)  # negative wishes never shown


def test_check_upload_rules() -> None:
    ok = checks.check_upload(_png(), "image/png")
    assert ok.status is CheckStatus.PASSED

    small = checks.check_upload(_png(500, 500), "image/png")
    assert small.status is CheckStatus.FAILED
    assert any("1000" in i.issue for i in small.issues)

    bad_type = checks.check_upload(_png(), "image/gif")
    assert bad_type.status is CheckStatus.FAILED


def test_compliance_main_image_rejects_overlay() -> None:
    report = checks.check_compliance(
        asset_type=AssetType.MAIN_IMAGE_EDIT,
        output=_png(),
        overlay_applied=True,
    )
    assert report.status is CheckStatus.FAILED
    assert any("must not contain added text" in i.issue for i in report.issues)


def test_consistency_aspect_mismatch_detected() -> None:
    source = _png(1000, 1000)
    output = _png(1000, 500)
    report = checks.check_consistency(
        asset_type=AssetType.MAIN_IMAGE_EDIT, output=output, source_images=[source]
    )
    assert report.status is CheckStatus.FAILED
    assert any("aspect" in i.check for i in report.issues)
