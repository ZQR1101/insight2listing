"""Automated image checks (plan sections 13.3 and 13.7).

Deterministic, measurable checks only: format, minimum resolution, main-image
prohibitions (no overlay text) and source-aspect consistency. Visual product
consistency cannot be verified by rules — that is what the human review gate
(§13.7 最后一步) is for.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO

from PIL import Image

from app.core.enums import AssetType, CheckStatus

MIN_SIDE_PX = 1000
_ALLOWED_MIME = {"image/png", "image/jpeg"}


@dataclass(slots=True)
class ImageIssue:
    check: str
    issue: str


@dataclass(slots=True)
class ImageCheckReport:
    status: CheckStatus
    issues: list[ImageIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "issues": [{"check": i.check, "issue": i.issue} for i in self.issues],
        }


def _validate_upload_bytes(data: bytes) -> list[ImageIssue]:
    issues: list[ImageIssue] = []
    try:
        with Image.open(BytesIO(data)) as image:
            width, height = image.size
    except Exception:
        return [ImageIssue("decode", "file is not a readable image")]
    if width < MIN_SIDE_PX or height < MIN_SIDE_PX:
        issues.append(
            ImageIssue(
                "resolution",
                f"image is {width}x{height}, shortest side must be >= {MIN_SIDE_PX}px",
            )
        )
    return issues


def check_upload(data: bytes, content_type: str) -> ImageCheckReport:
    issues = _validate_upload_bytes(data)
    if content_type not in _ALLOWED_MIME:
        issues.append(ImageIssue("format", f"unsupported content type: {content_type}"))
    return ImageCheckReport(
        status=CheckStatus.FAILED if issues else CheckStatus.PASSED, issues=issues
    )


def check_consistency(
    *,
    asset_type: AssetType,
    output: bytes,
    source_images: list[bytes],
) -> ImageCheckReport:
    """Measurable consistency proxies for a generated asset."""
    issues = _validate_upload_bytes(output)
    if asset_type is AssetType.MAIN_IMAGE_EDIT:
        if not source_images:
            issues.append(ImageIssue("source", "main image edit ran without a source photo"))
        else:
            try:
                out_ratio = _aspect(output)
                src_ratio = _aspect(source_images[0])
                if abs(out_ratio - src_ratio) > 0.02:
                    issues.append(
                        ImageIssue(
                            "aspect",
                            "output aspect ratio differs from the source photo",
                        )
                    )
            except Exception:
                issues.append(ImageIssue("decode", "source photo is not readable"))
    return ImageCheckReport(
        status=CheckStatus.FAILED if issues else CheckStatus.PASSED, issues=issues
    )


def check_compliance(
    *,
    asset_type: AssetType,
    output: bytes,
    overlay_applied: bool,
) -> ImageCheckReport:
    issues: list[ImageIssue] = []
    if asset_type is AssetType.MAIN_IMAGE_EDIT and overlay_applied:
        issues.append(
            ImageIssue("main_image", "main image must not contain added text or graphics")
        )
    if asset_type is AssetType.MAIN_IMAGE_EDIT:
        try:
            with Image.open(BytesIO(output)) as image:
                if min(image.size) < MIN_SIDE_PX:
                    issues.append(
                        ImageIssue("resolution", "main image below minimum resolution")
                    )
        except Exception:
            issues.append(ImageIssue("decode", "output is not a readable image"))
    return ImageCheckReport(
        status=CheckStatus.FAILED if issues else CheckStatus.PASSED, issues=issues
    )


def _aspect(data: bytes) -> float:
    with Image.open(BytesIO(data)) as image:
        width, height = image.size
    return width / height if height else 0.0
