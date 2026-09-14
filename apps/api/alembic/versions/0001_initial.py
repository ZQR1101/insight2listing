"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-14

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
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
    # ---- identity ----
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        *_common(),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column(
            "last_login_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        *_common(),
    )
    op.create_index("ix_users_workspace_id", "users", ["workspace_id"])
    op.create_unique_constraint("uq_users_email", "users", ["email"])

    # ---- sources & imports ----
    op.create_table(
        "sources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("source_type", sa.String(length=32), server_default="user_upload", nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=True),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("license", sa.String(length=255), nullable=True),
        sa.Column("usage_scope", sa.String(length=255), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_attested", sa.String(length=255), nullable=True),
        sa.Column("raw_payload_hash", sa.String(length=128), nullable=True),
        *_common(),
    )
    op.create_index("ix_sources_workspace_id", "sources", ["workspace_id"])

    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("marketplace", sa.String(length=32), server_default="amazon_us", nullable=False),
        sa.Column("target_locale", sa.String(length=16), server_default="en-US", nullable=False),
        sa.Column("interface_locale", sa.String(length=16), server_default="zh-CN", nullable=False),
        sa.Column("currency", sa.String(length=8), server_default="USD", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="DRAFT", nullable=False),
        *_common(),
    )
    op.create_index("ix_projects_workspace_id", "projects", ["workspace_id"])
    op.create_index("ix_projects_status", "projects", ["status"])

    # ---- catalog ----
    op.create_table(
        "product_candidates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=1000), nullable=False),
        sa.Column("brand", sa.String(length=255), nullable=True),
        sa.Column("currency", sa.String(length=8), server_default="USD", nullable=False),
        sa.Column("rating", sa.Numeric(4, 2), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("freshness", JSONB(), nullable=True),
        *_common(),
    )
    op.create_index("ix_product_candidates_project_id", "product_candidates", ["project_id"])

    op.create_table(
        "product_variants",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("product_candidates.id"), nullable=False),
        sa.Column("sku", sa.String(length=255), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("color", sa.String(length=255), nullable=True),
        sa.Column("size", sa.String(length=255), nullable=True),
        sa.Column("package_quantity", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        *_common(),
    )
    op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"])

    # ---- reviews ----
    op.create_table(
        "reviews",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("product_candidates.id"), nullable=True),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("external_review_id", sa.String(length=255), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=1000), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("verified_purchase", sa.Boolean(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        *_common(),
    )
    op.create_index("ix_reviews_project_id", "reviews", ["project_id"])
    op.create_index("ix_reviews_product_id", "reviews", ["product_id"])
    op.create_index("ix_reviews_content_hash", "reviews", ["content_hash"])

    # ---- import batches ----
    op.create_table(
        "import_batches",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("target", sa.String(length=32), nullable=False),
        sa.Column("source_file_name", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("report", JSONB(), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        *_common(),
    )
    op.create_index("ix_import_batches_project_id", "import_batches", ["project_id"])

    # ---- audit ----
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), nullable=True),
        sa.Column("actor", sa.String(length=255), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=True),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("before", JSONB(), nullable=True),
        sa.Column("after", JSONB(), nullable=True),
        *_common(),
    )
    op.create_index("ix_audit_events_workspace_id", "audit_events", ["workspace_id"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])


def downgrade() -> None:
    for table in (
        "audit_events",
        "import_batches",
        "reviews",
        "product_variants",
        "product_candidates",
        "projects",
        "sources",
        "users",
        "workspaces",
    ):
        op.drop_table(table)