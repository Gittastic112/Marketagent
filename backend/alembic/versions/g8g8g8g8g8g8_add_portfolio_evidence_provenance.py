"""add portfolio evidence provenance

Revision ID: g8g8g8g8g8g8
Revises: f7f7f7f7f7f7
Create Date: 2026-08-24 20:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "g8g8g8g8g8g8"
down_revision: str | None = "f7f7f7f7f7f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("market_prices", sa.Column("source_url", sa.String(length=1000), nullable=True))
    op.add_column(
        "market_prices",
        sa.Column("claim_type", sa.String(length=30), server_default="Fact", nullable=False),
    )
    op.add_column("market_prices", sa.Column("import_run_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_market_prices_import_run_id_processing_runs",
        "market_prices",
        "processing_runs",
        ["import_run_id"],
        ["id"],
    )
    op.create_index("ix_market_prices_import_run_id", "market_prices", ["import_run_id"])
    op.add_column(
        "fx_rate_observations",
        sa.Column("claim_type", sa.String(length=30), server_default="Fact", nullable=False),
    )
    op.add_column("fx_rate_observations", sa.Column("import_run_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_fx_rate_observations_import_run_id_processing_runs",
        "fx_rate_observations",
        "processing_runs",
        ["import_run_id"],
        ["id"],
    )
    op.create_index(
        "ix_fx_rate_observations_import_run_id",
        "fx_rate_observations",
        ["import_run_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_fx_rate_observations_import_run_id", table_name="fx_rate_observations")
    op.drop_constraint(
        "fk_fx_rate_observations_import_run_id_processing_runs",
        "fx_rate_observations",
        type_="foreignkey",
    )
    op.drop_column("fx_rate_observations", "import_run_id")
    op.drop_column("fx_rate_observations", "claim_type")
    op.drop_index("ix_market_prices_import_run_id", table_name="market_prices")
    op.drop_constraint(
        "fk_market_prices_import_run_id_processing_runs",
        "market_prices",
        type_="foreignkey",
    )
    op.drop_column("market_prices", "import_run_id")
    op.drop_column("market_prices", "claim_type")
    op.drop_column("market_prices", "source_url")
