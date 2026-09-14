"""ORM model registry.

Importing this package registers every model with the core ``Base`` metadata
so that Alembic autogenerate can discover them and ``Base.metadata`` is
complete.
"""

from app.models.audit import AuditEvent
from app.models.catalog import ProductCandidate, ProductVariant
from app.models.identity import User, Workspace
from app.models.project import Project
from app.models.review import Review
from app.models.source import ImportBatch, SourceRecord

__all__ = [
    "AuditEvent",
    "ImportBatch",
    "ProductCandidate",
    "ProductVariant",
    "Project",
    "Review",
    "SourceRecord",
    "User",
    "Workspace",
]
