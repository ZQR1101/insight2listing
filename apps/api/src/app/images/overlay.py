"""Deterministic text overlay (plan section 13.5).

Text, dimensions and brand elements are typeset programmatically (Pillow), not
by the image model, so spelling/numbers are correct and the same base image can
be reused across locales. Same inputs always produce byte-identical output.
"""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw

_MARGIN_PX = 32
_LINE_GAP_PX = 8
_TEXT_FILL = (33, 33, 33)
_PLAQUE_FILL = (255, 255, 255)


def apply_overlay(image_data: bytes, lines: list[str]) -> bytes:
    """Draw ``lines`` onto a white plaque in the top-left corner, deterministically."""
    if not lines:
        return image_data
    with Image.open(BytesIO(image_data)) as image:
        working = image.convert("RGBA")
        draw = ImageDraw.Draw(working)
        y = _MARGIN_PX
        width = working.width
        for line in lines:
            box = draw.textbbox((_MARGIN_PX, y), line)
            line_height = int(box[3] - box[1]) if box[3] > box[1] else 16
            draw.rectangle(
                [
                    _MARGIN_PX - 8,
                    y - 6,
                    min(width - _MARGIN_PX, _MARGIN_PX + box[2] - box[0] + 16),
                    y + line_height + 6,
                ],
                fill=_PLAQUE_FILL,
            )
            draw.text((_MARGIN_PX, y), line, fill=_TEXT_FILL)
            y += line_height + _LINE_GAP_PX + 12
        buffer = BytesIO()
        working.save(buffer, format=image.format or "PNG")
        return buffer.getvalue()
