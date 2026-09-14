"""Model provider contract tests using mock implementations."""

from __future__ import annotations

import pytest

from app.providers import (
    MockEmbeddingProvider,
    MockImageProvider,
    MockModerationProvider,
    MockTextInsightProvider,
)


@pytest.mark.asyncio
async def test_text_provider_returns_summary_and_usage() -> None:
    provider = MockTextInsightProvider()
    result, usage = await provider.call(prompt="packing cubes leak")
    assert "[mock insight" in str(result)
    assert usage.model == "mock-text-model"
    assert usage.input_tokens > 0


@pytest.mark.asyncio
async def test_embedding_provider_returns_vector() -> None:
    provider = MockEmbeddingProvider()
    result, _usage = await provider.call(text="hello")
    assert len(result) == 16


@pytest.mark.asyncio
async def test_image_provider_is_swappable() -> None:
    provider = MockImageProvider()
    result, _usage = await provider.call(prompt="main product shot")
    assert result["mock"] is True


@pytest.mark.asyncio
async def test_moderation_flags_banned_words() -> None:
    provider = MockModerationProvider()
    flagged, _ = await provider.call(text="contains spam")
    assert flagged["flagged"] is True
    clean, _ = await provider.call(text="all good")
    assert clean["flagged"] is False
