"""product facts and listing versions

Revision ID: 0003_facts_listings
Revises: 0002_insights_opportunity
Create Date: 2026-09-16

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "0003_facts_listings"
down_revision = "0002_insights_opportunity"
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
        "product_facts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column(
            "product_id", sa.Uuid(), sa.ForeignKey("product_candidates.id"), nullable=False
        ),
        sa.Column(
            "variant_id", sa.Uuid(), sa.ForeignKey("product_variants.id"), nullable=True
        ),
        sa.Column("fact_type", sa.String(length=48), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column(
            "verification_status", sa.String(length=32), server_default="unverified", nullable=False
        ),
        sa.Column("verified_by", sa.String(length=255), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        *_common(),
    )
    op.create_index("ix_product_facts_project_id", "product_facts", ["project_id"])
    op.create_index("ix_product_facts_product_id", "product_facts", ["product_id"])
    op.create_index("ix_product_facts_fact_type", "product_facts", ["fact_type"])
    op.create_index(
        "ix_product_facts_verification_status", "product_facts", ["verification_status"]
    )

    op.create_table(
        "listing_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column(
            "product_id", sa.Uuid(), sa.ForeignKey("product_candidates.id"), nullable=False
        ),
        sa.Column("marketplace", sa.String(length=32), server_default="amazon_us", nullable=False),
        sa.Column("locale", sa.String(length=16), server_default="en-US", nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("bullet_points", JSONB(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("search_terms", sa.Text(), nullable=True),
        sa.Column("model", sa.String(length=64), nullable=True),
        sa.Column("prompt_version", sa.String(length=64), nullable=True),
        sa.Column("input_snapshot_id", sa.String(length=64), nullable=True),
        sa.Column("input_snapshot", JSONB(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("fact_check", JSONB(), nullable=True),
        sa.Column("rule_check", JSONB(), nullable=True),
        *_common(),
    )
    op.create_index("ix_listing_versions_project_id", "listing_versions", ["project_id"])
    op.create_index("ix_listing_versions_product_id", "listing_versions", ["product_id"])
    op.create_index("ix_listing_versions_status", "listing_versions", ["status"])


def downgrade() -> None:
    op.drop_table("listing_versions")
    op.drop_table("product_facts")