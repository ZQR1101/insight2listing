"""insights and opportunity cards

Revision ID: 0002_insights_opportunity
Revises: 0001_initial
Create Date: 2026-09-16

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "0002_insights_opportunity"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def _common() -> list[sa.Column]:
    return [
        sa.Column("schema_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(length=255), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "insights",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("product_candidates.id"), nullable=True),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("sentiment", sa.String(length=16), server_default="neutral", nullable=False),
        sa.Column("frequency", sa.Integer(), server_default="0", nullable=False),
        sa.Column("severity", sa.String(length=16), server_default="low", nullable=False),
        sa.Column("rating_impact", sa.Numeric(5, 2), nullable=True),
        sa.Column("recency_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("cross_competitor_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="generated", nullable=False),
        *_common(),
    )
    op.create_index("ix_insights_project_id", "insights", ["project_id"])
    op.create_index("ix_insights_product_id", "insights", ["product_id"])
    op.create_index("ix_insights_status", "insights", ["status"])

    op.create_table(
        "evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("insight_id", sa.Uuid(), sa.ForeignKey("insights.id"), nullable=False),
        sa.Column("evidence_type", sa.String(length=48), nullable=False),
        sa.Column("source_entity_id", sa.String(length=128), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("support_strength", sa.Numeric(5, 2), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        *_common(),
    )
    op.create_index("ix_evidence_insight_id", "evidence", ["insight_id"])

    op.create_table(
        "opportunity_cards",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("product_candidates.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("target_audience", sa.Text(), nullable=True),
        sa.Column("use_cases", JSONB(), nullable=True),
        sa.Column("competitor_gaps", JSONB(), nullable=True),
        sa.Column("differentiation_ideas", JSONB(), nullable=True),
        sa.Column("keywords", JSONB(), nullable=True),
        sa.Column("opportunity_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("dimension_scores", JSONB(), nullable=True),
        sa.Column("score_version", sa.String(length=64), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("missing_dimensions", JSONB(), nullable=True),
        sa.Column("risk_flags", JSONB(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        *_common(),
    )
    op.create_index("ix_opportunity_cards_project_id", "opportunity_cards", ["project_id"])
    op.create_index("ix_opportunity_cards_product_id", "opportunity_cards", ["product_id"])


def downgrade() -> None:
    for table in ("opportunity_cards", "evidence", "insights"):
        op.drop_table(table)