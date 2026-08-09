"""add document assets

Revision ID: a7a7a7a7a7a7
Revises: f6f6f6f6f6f6
Create Date: 2026-07-25 13:30:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a7a7a7a7a7a7"
down_revision: str | Sequence[str] | None = "f6f6f6f6f6f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "document_assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("raw_document_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["raw_document_id"],
            ["raw_documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("raw_document_id"),
    )
    op.create_index(
        op.f("ix_document_assets_raw_document_id"),
        "document_assets",
        ["raw_document_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_document_assets_sha256"),
        "document_assets",
        ["sha256"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_document_assets_sha256"), table_name="document_assets")
    op.drop_index(op.f("ix_document_assets_raw_document_id"), table_name="document_assets")
    op.drop_table("document_assets")
