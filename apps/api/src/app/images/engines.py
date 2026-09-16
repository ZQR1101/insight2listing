"""Image generation engines (plan section 13.1).

``ImageEngine`` is the concrete wiring behind the swappable
``ImageModelProvider`` seam. Two implementations:

- ``MockImageEngine`` — offline, deterministic. Main-image edits return the
  source image untouched (a mock must never alter the product, section 13.3);
  pure generation renders a clearly-labelled placeholder via Pillow.
- ``OpenAIImageEngine`` — the real gpt-image-2 wiring via the OpenAI images
  API. Dormant unless configured; never exercised by tests.

Use :func:`get_image_engine` to resolve the engine from settings
(``IMAGE_PROVIDER=auto|mock|openai``).
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Protocol

from PIL import Image, ImageDraw

from app.core.config import Settings, get_settings

_PIL_TO_MIME = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}


@dataclass(slots=True)
class EngineResult:
    content: bytes
    content_type: str
    model: str


def sniff_content_type(data: bytes) -> str:
    with Image.open(BytesIO(data)) as image:
        return _PIL_TO_MIME.get(image.format or "PNG", "application/octet-stream")


def image_dimensions(data: bytes) -> tuple[int, int]:
    with Image.open(BytesIO(data)) as image:
        width, height = image.size
        return int(width), int(height)


class ImageEngine(Protocol):
    engine_name: str

    async def edit(self, sources: list[bytes], prompt: str) -> EngineResult: ...

    async def generate(self, prompt: str, width: int, height: int) -> EngineResult: ...


class MockImageEngine:
    """Offline deterministic engine (also the safe default without a key)."""

    engine_name = "mock"

    @classmethod
    def _default_model(cls) -> str:
        return "mock-image-model"

    async def edit(self, sources: list[bytes], prompt: str) -> EngineResult:
        if not sources:
            raise ValueError("mock image edit requires a source image")
        # A mock must never alter the product: return the first source as-is.
        first = sources[0]
        return EngineResult(
            content=first,
            content_type=sniff_content_type(first),
            model=self._default_model(),
        )

    async def generate(self, prompt: str, width: int, height: int) -> EngineResult:
        image = Image.new("RGB", (width, height), (242, 242, 242))
        draw = ImageDraw.Draw(image)
        label = f"MOCK CREATIVE\n{prompt[:60]}"
        draw.multiline_text((32, 32), label, fill=(90, 90, 90))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return EngineResult(
            content=buffer.getvalue(), content_type="image/png", model=self._default_model()
        )


class OpenAIImageEngine:
    """Real gpt-image-2 wiring via the OpenAI images API (dormant without a key)."""

    engine_name = "openai"

    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1") -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    async def edit(self, sources: list[bytes], prompt: str) -> EngineResult:
        import httpx

        files: list[tuple[str, tuple[str, bytes, str]]] = []
        for idx, source in enumerate(sources):
            ext = "png" if sniff_content_type(source) == "image/png" else "jpg"
            files.append(("image[]", (f"source_{idx}.{ext}", source, sniff_content_type(source))))
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self._base_url}/images/edits",
                headers={"Authorization": f"Bearer {self._api_key}"},
                data={"model": self._model, "prompt": prompt},
                files=files,
            )
            response.raise_for_status()
            payload = response.json()
        return self._decode(payload)

    async def generate(self, prompt: str, width: int, height: int) -> EngineResult:
        import httpx

        size = f"{width}x{height}"
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self._base_url}/images/generations",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": self._model, "prompt": prompt, "size": size},
            )
            response.raise_for_status()
            payload = response.json()
        return self._decode(payload)

    def _decode(self, payload: dict[str, Any]) -> EngineResult:
        item = (payload.get("data") or [{}])[0]
        b64 = item.get("b64_json")
        if not b64:
            raise ValueError("image response did not contain b64_json")
        content = base64.b64decode(b64)
        return EngineResult(
            content=content,
            content_type=sniff_content_type(content),
            model=self._model,
        )


def get_image_engine(settings: Settings | None = None) -> ImageEngine:
    resolved = settings or get_settings()
    provider = resolved.image_provider.lower()
    if provider == "mock":
        return MockImageEngine()
    if provider == "openai" or (provider == "auto" and resolved.openai_api_key):
        return OpenAIImageEngine(
            api_key=resolved.openai_api_key, model=resolved.openai_image_model
        )
    return MockImageEngine()
