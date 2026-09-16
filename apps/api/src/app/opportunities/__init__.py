"""Insight & opportunity-card analysis (Phase C)."""

from app.opportunities import engine, opportunity_card, scoring
from app.opportunities.service import (
    GenerateResult,
    edit_insight,
    generate_project_insights,
    set_insight_status,
)

__all__ = [
    "GenerateResult",
    "edit_insight",
    "engine",
    "generate_project_insights",
    "opportunity_card",
    "scoring",
    "set_insight_status",
]
