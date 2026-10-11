"""add DCF currency audit fields

Revision ID: h9h9h9h9h9h9
Revises: g8g8g8g8g8g8
Create Date: 2026-08-25 09:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "h9h9h9h9h9h9"
down_revision: str | None = "g8g8g8g8g8g8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("dcf_assumption_sets", sa.Column("cash_flow_currency", sa.String(length=10), nullable=True))
    op.add_column("dcf_assumption_sets", sa.Column("discount_rate_currency", sa.String(length=10), nullable=True))
    op.add_column("dcf_assumption_sets", sa.Column("currency_override_note", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("dcf_assumption_sets", "currency_override_note")
    op.drop_column("dcf_assumption_sets", "discount_rate_currency")
    op.drop_column("dcf_assumption_sets", "cash_flow_currency")
