"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_actor(x_actor: Annotated[str | None, Header()] = None) -> str | None:
    """Resolve an actor label.

    Auth is out of scope for the first milestone, so an optional ``X-Actor``
    header is used to attribute audit events without inventing a session.
    """
    return x_actor or None


ActorDep = Annotated[str | None, Depends(get_actor)]
