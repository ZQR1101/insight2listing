"""Audit helpers.

Thin service that persists an :class:`AuditEvent` within an active session.
Never pass secrets into ``before``/``after``; keep captured state to entity
identifiers and non-sensitive summary fields.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AuditAction
from app.models.audit import AuditEvent


async def log_event(
    session: AsyncSession,
    *,
    workspace_id: uuid.UUID | None,
    action: AuditAction,
    actor: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> AuditEvent:
    """Persist an audit event without committing (caller owns the transaction)."""
    event = AuditEvent(
        workspace_id=workspace_id,
        actor=actor,
        action=action.value,
        entity_type=entity_type,
        entity_id=entity_id,
        before=before,
        after=after,
    )
    session.add(event)
    return event
