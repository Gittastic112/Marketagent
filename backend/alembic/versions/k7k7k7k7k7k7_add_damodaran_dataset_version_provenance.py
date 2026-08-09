"""Add Damodaran dataset version provenance and exact ROE fields.

Revision ID: k7k7k7k7k7k7
Revises: j6j6j6j6j6j6
Create Date: 2026-08-08
"""

import sqlalchemy as sa
from alembic import op


revision = "k7k7k7k7k7k7"
down_revision = "j6j6j6j6j6j6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "damodaran_dataset_files",
        sa.Column("source_sha256", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "damodaran_dataset_files",
        sa.Column("source_byte_size", sa.Integer(), nullable=True),
    )
    op.add_column(
        "damodaran_dataset_files",
        sa.Column("source_as_of", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "damodaran_dataset_files",
        sa.Column(
            "date_confidence",
            sa.String(length=20),
            nullable=False,
            server_default="unknown",
        ),
    )
    op.add_column(
        "damodaran_dataset_files",
        sa.Column("canonical_source_path", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "damodaran_dataset_files",
        sa.Column(
            "import_kind",
            sa.String(length=40),
            nullable=False,
            server_default="legacy_unknown",
        ),
    )
    op.add_column(
        "damodaran_dataset_files",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "damodaran_dataset_files",
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "damodaran_dataset_files",
        sa.Column("row_count", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_damodaran_dataset_files_source_sha256",
        "damodaran_dataset_files",
        ["source_sha256"],
    )
    op.create_index(
        "ix_damodaran_dataset_files_is_active",
        "damodaran_dataset_files",
        ["is_active"],
    )
    op.create_index(
        "ix_damodaran_dataset_identity_active",
        "damodaran_dataset_files",
        ["dataset_code", "country", "is_active"],
    )

    op.add_column(
        "damodaran_industry_roe_benchmarks",
        sa.Column("number_of_firms", sa.Integer(), nullable=True),
    )
    op.add_column(
        "damodaran_industry_roe_benchmarks",
        sa.Column("rd_adjusted_roe", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("damodaran_industry_roe_benchmarks", "rd_adjusted_roe")
    op.drop_column("damodaran_industry_roe_benchmarks", "number_of_firms")

    op.drop_index("ix_damodaran_dataset_identity_active", table_name="damodaran_dataset_files")
    op.drop_index("ix_damodaran_dataset_files_is_active", table_name="damodaran_dataset_files")
    op.drop_index("ix_damodaran_dataset_files_source_sha256", table_name="damodaran_dataset_files")
    op.drop_column("damodaran_dataset_files", "row_count")
    op.drop_column("damodaran_dataset_files", "superseded_at")
    op.drop_column("damodaran_dataset_files", "is_active")
    op.drop_column("damodaran_dataset_files", "import_kind")
    op.drop_column("damodaran_dataset_files", "canonical_source_path")
    op.drop_column("damodaran_dataset_files", "date_confidence")
    op.drop_column("damodaran_dataset_files", "source_as_of")
    op.drop_column("damodaran_dataset_files", "source_byte_size")
    op.drop_column("damodaran_dataset_files", "source_sha256")
