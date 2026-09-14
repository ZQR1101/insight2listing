"""Project entity and its project-level fields.

See plan section 16.2. ``status`` follows the workflow state machine in 7.1
and is validated by Pydantic at the API boundary.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import CoreMixin


class Project(CoreMixin, Base):
    __tablename__ = "projects"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    marketplace: Mapped[str] = mapped_column(String(32), default="amazon_us", nullable=False)
    target_locale: Mapped[str] = mapped_column(String(16), default="en-US", nullable=False)
    interface_locale: Mapped[str] = mapped_column(String(16), default="zh-CN", nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", nullable=False, index=True)
