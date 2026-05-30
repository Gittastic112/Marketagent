"""add_company_market_data

Revision ID: 20260530_1003
Revises: 20260530_0725
Create Date: 2026-05-30 10:03:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260530_1003'
down_revision: Union[str, None] = '20260530_0725'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('company_market_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('current_price', sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('change_percent', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('volume', sa.Integer(), nullable=True),
        sa.Column('market_cap', sa.Numeric(precision=25, scale=2), nullable=True),
        sa.Column('pe_ratio', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('fifty_two_week_high', sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column('fifty_two_week_low', sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_company_market_data_company_id'), 'company_market_data', ['company_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_company_market_data_company_id'), table_name='company_market_data')
    op.drop_table('company_market_data')
