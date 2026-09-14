"""Mock providers for local development and tests.

These return deterministic results without calling any external service, so
the importer, tests and CI all run offline. See plan sections 15.4 and 8.4.
"""

from __future__ import annotations

from typing import Any

from app.providers.base import (
    EmbeddingProvider,
    ImageProvider,
    ModerationProvider,
    TextInsightProvider,
    Usage,
)


class MockTextInsightProvider(TextInsightProvider):
    provider_name = "mock-text"

    @classmethod
    def _default_model(cls) -> str:
        return "mock-text-model"

    async def _call(self, *, model: str, **kwargs: Any) -> tuple[Any, Usage]:
        prompt = kwargs.get("prompt", "")
        result = f"[mock insight summary for: {prompt[:60]}...]" if prompt else "[mock insight]"
        return result, Usage(model=model, provider=self.provider_name, input_tokens=len(prompt))


class MockEmbeddingProvider(EmbeddingProvider):
    provider_name = "mock-embedding"

    @classmethod
    def _default_model(cls) -> str:
        return "mock-embedding-model"

    async def _call(self, *, model: str, **kwargs: Any) -> tuple[Any, Usage]:
        text = kwargs.get("text", "")
        vector = [0.0] * 16
        if text:
            vector[0] = float(len(text)) / 100.0
        return vector, Usage(model=model, provider=self.provider_name, input_tokens=len(text))


class MockImageProvider(ImageProvider):
    provider_name = "mock-image"

    @classmethod
    def _default_model(cls) -> str:
        return "mock-image-model"

    async def _call(self, *, model: str, **kwargs: Any) -> tuple[Any, Usage]:
        # No real image is produced; return a placeholder marker only.
        return {"mock": True, "prompt": kwargs.get("prompt", "")}, Usage(
            model=model, provider=self.provider_name
        )


class MockModerationProvider(ModerationProvider):
    provider_name = "mock-moderation"

    @classmethod
    def _default_model(cls) -> str:
        return "mock-moderation-model"

    async def _call(self, *, model: str, **kwargs: Any) -> tuple[Any, Usage]:
        text: str = kwargs.get("text", "")
        flagged = any(word in text.lower() for word in ("spam", "banned"))
        return {"flagged": flagged, "reason": "mock" if flagged else None}, Usage(
            model=model, provider=self.provider_name, input_tokens=len(text)
        )
