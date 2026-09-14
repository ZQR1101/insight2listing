"""Model provider interfaces (plan section 15.4).

Providers are swappable abstractions over text, embedding, image and
moderation models. They own retry/timeout, model selection, usage & cost
recording and input/output audit. The first milestone ships the abstract
contracts and a :class:`MockProvider`; real OpenAI wiring comes later.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any

from app.core.config import get_settings


@dataclass
class Usage:
    """Recorded cost/usage for a single provider call."""

    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class Provider(abc.ABC):
    """Base contract shared by all providers.

    Concrete providers should implement :meth:`_call` with their own protocol
    and rely on the inherited retry/timeout/cost plumbing for consistency.
    """

    provider_name: str = "base"

    def __init__(self, *, model: str | None = None) -> None:
        self.model = model or self._default_model()
        self.model_key = get_settings().redact(self.model)

    @classmethod
    @abc.abstractmethod
    def _default_model(cls) -> str:
        """Return the default model id for this provider."""
        raise NotImplementedError

    @abc.abstractmethod
    async def _call(self, *, model: str, **kwargs: Any) -> tuple[Any, Usage]:
        """Execute a single model call and report usage.

        Returns ``(result, usage)``. Implementations must not log API keys.
        """
        raise NotImplementedError

    async def call(self, **kwargs: Any) -> tuple[Any, Usage]:
        """Public entry point for a model call (contract wrapper)."""
        usage = Usage(model=self.model, provider=self.provider_name)
        result = await self._call(model=self.model, **kwargs)
        if isinstance(result, tuple) and len(result) == 2:
            result, measured = result
            usage = measured
        return result, usage


class TextInsightProvider(Provider):
    """Provider for market-insight / review-analysis text tasks."""

    provider_name = "text-insight"


class EmbeddingProvider(Provider):
    """Provider for vector embeddings (search / clustering)."""

    provider_name = "embedding"


class ImageProvider(Provider):
    """Provider for image generation and editing (e.g. gpt-image-2)."""

    provider_name = "image"


class ModerationProvider(Provider):
    """Provider for content moderation / safety checks."""

    provider_name = "moderation"
