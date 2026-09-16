"""product images and creatives

Revision ID: 0004_images_creatives
Revises: 0003_facts_listings
Create Date: 2026-09-16

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "0004_images_creatives"
down_revision = "0003_facts_listings"
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
        "product_images",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column(
            "product_id", sa.Uuid(), sa.ForeignKey("product_candidates.id"), nullable=False
        ),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("uploaded_by", sa.String(length=255), nullable=True),
        *_common(),
    )
    op.create_index("ix_product_images_project_id", "product_images", ["project_id"])
    op.create_index("ix_product_images_product_id", "product_images", ["product_id"])
    op.create_index("ix_product_images_checksum", "product_images", ["checksum"])

    op.create_table(
        "creatives",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column(
            "product_id", sa.Uuid(), sa.ForeignKey("product_candidates.id"), nullable=False
        ),
        sa.Column("variant_id", sa.Uuid(), sa.ForeignKey("product_variants.id"), nullable=True),
        sa.Column("asset_type", sa.String(length=48), nullable=False),
        sa.Column("locale", sa.String(length=16), server_default="en-US", nullable=False),
        sa.Column("source_images", JSONB(), nullable=True),
        sa.Column("creative_brief", JSONB(), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("model", sa.String(length=64), nullable=True),
        sa.Column("output_key", sa.String(length=512), nullable=True),
        sa.Column("output_content_type", sa.String(length=64), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("consistency_status", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("compliance_status", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("human_review_status", sa.String(length=16), server_default="pending", nullable=False),
        *_common(),
    )
    op.create_index("ix_creatives_project_id", "creatives", ["project_id"])
    op.create_index("ix_creatives_product_id", "creatives", ["product_id"])
    op.create_index("ix_creatives_asset_type", "creatives", ["asset_type"])
    op.create_index("ix_creatives_human_review_status", "creatives", ["human_review_status"])


def downgrade() -> None:
    op.drop_table("creatives")
    op.drop_table("product_images")