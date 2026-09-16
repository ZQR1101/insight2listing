"""Object storage abstraction (plan section 15.2).

The first milestone ships a local-disk implementation (``apps/api/data/local``
is gitignored); the protocol is the seam for an S3/MinIO implementation later.
Keys are slash-separated relative paths; implementations must keep ``save``
idempotent for the same key.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from app.core.config import get_settings


class ObjectStorage(Protocol):
    async def save(self, key: str, data: bytes, content_type: str) -> str:
        """Store bytes under ``key`` and return the key."""
        ...

    def load(self, key: str) -> bytes:
        """Return the bytes stored under ``key`` (raises KeyError if missing)."""
        ...


class LocalObjectStorage:
    """Local-disk storage rooted at ``settings.local_storage_dir``."""

    def __init__(self, root: str | Path | None = None) -> None:
        self._root = Path(root) if root else Path(get_settings().local_storage_dir)

    def _path(self, key: str) -> Path:
        resolved = (self._root / key).resolve()
        if not resolved.is_relative_to(self._root.resolve()):
            raise ValueError("storage key escapes the storage root")
        return resolved

    async def save(self, key: str, data: bytes, content_type: str) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def load(self, key: str) -> bytes:
        path = self._path(key)
        if not path.is_file():
            raise KeyError(key)
        return path.read_bytes()


_storage: ObjectStorage | None = None


def get_storage() -> ObjectStorage:
    global _storage
    if _storage is None:
        _storage = LocalObjectStorage()
    return _storage


def reset_storage() -> None:
    """Drop the cached storage (used by tests)."""
    global _storage
    _storage = None
