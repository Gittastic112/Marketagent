"""Link volatility benchmarks to preserved Damodaran dataset versions.

Revision ID: m9m9m9m9m9m9
Revises: l8l8l8l8l8l8
Create Date: 2026-08-08
"""

import sqlalchemy as sa
from alembic import op


revision = "m9m9m9m9m9m9"
down_revision = "l8l8l8l8l8l8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "industry_volatility_benchmarks",
        sa.Column("dataset_file_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_industry_volatility_benchmarks_dataset_file_id",
        "industry_volatility_benchmarks",
        "damodaran_dataset_files",
        ["dataset_file_id"],
        ["id"],
    )
    op.create_index(
        "ix_industry_volatility_benchmarks_dataset_file_id",
        "industry_volatility_benchmarks",
        ["dataset_file_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_industry_volatility_benchmarks_dataset_file_id",
        table_name="industry_volatility_benchmarks",
    )
    op.drop_constraint(
        "fk_industry_volatility_benchmarks_dataset_file_id",
        "industry_volatility_benchmarks",
        type_="foreignkey",
    )
    op.drop_column("industry_volatility_benchmarks", "dataset_file_id")
