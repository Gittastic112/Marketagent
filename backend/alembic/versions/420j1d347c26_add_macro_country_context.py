"""add_macro_country_context

Revision ID: 420j1d347c26
Revises: 419i1d347c25
Create Date: 2026-06-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "420j1d347c26"
down_revision: str | Sequence[str] | None = "419i1d347c25"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sector_macro_sensitivity_benchmarks",
        sa.Column("market", sa.String(length=10), nullable=False, server_default="IN"),
    )
    op.add_column(
        "sector_macro_sensitivity_benchmarks",
        sa.Column("country", sa.String(length=120), nullable=False, server_default="India"),
    )
    op.add_column(
        "sector_macro_sensitivity_benchmarks",
        sa.Column("classification_system", sa.String(length=40), nullable=False, server_default="SIC"),
    )
    op.add_column(
        "sector_macro_sensitivity_benchmarks",
        sa.Column("currency_context", sa.String(length=40), nullable=True, server_default="INR"),
    )
    op.add_column(
        "sector_macro_sensitivity_benchmarks",
        sa.Column(
            "currency_variable_description",
            sa.String(length=500),
            nullable=True,
            server_default="Source file currency movement convention not fully verified.",
        ),
    )

    op.create_index(
        op.f("ix_sector_macro_sensitivity_benchmarks_market"),
        "sector_macro_sensitivity_benchmarks",
        ["market"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sector_macro_sensitivity_benchmarks_country"),
        "sector_macro_sensitivity_benchmarks",
        ["country"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sector_macro_sensitivity_benchmarks_classification_system"),
        "sector_macro_sensitivity_benchmarks",
        ["classification_system"],
        unique=False,
    )

    op.alter_column("sector_macro_sensitivity_benchmarks", "market", server_default=None)
    op.alter_column("sector_macro_sensitivity_benchmarks", "country", server_default=None)
    op.alter_column("sector_macro_sensitivity_benchmarks", "classification_system", server_default=None)
    op.alter_column("sector_macro_sensitivity_benchmarks", "currency_context", server_default=None)
    op.alter_column("sector_macro_sensitivity_benchmarks", "currency_variable_description", server_default=None)


def downgrade() -> None:
    op.drop_index(
        op.f("ix_sector_macro_sensitivity_benchmarks_classification_system"),
        table_name="sector_macro_sensitivity_benchmarks",
    )
    op.drop_index(op.f("ix_sector_macro_sensitivity_benchmarks_country"), table_name="sector_macro_sensitivity_benchmarks")
    op.drop_index(op.f("ix_sector_macro_sensitivity_benchmarks_market"), table_name="sector_macro_sensitivity_benchmarks")
    op.drop_column("sector_macro_sensitivity_benchmarks", "currency_variable_description")
    op.drop_column("sector_macro_sensitivity_benchmarks", "currency_context")
    op.drop_column("sector_macro_sensitivity_benchmarks", "classification_system")
    op.drop_column("sector_macro_sensitivity_benchmarks", "country")
    op.drop_column("sector_macro_sensitivity_benchmarks", "market")
