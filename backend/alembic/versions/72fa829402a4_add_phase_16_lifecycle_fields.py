"""add phase 16 lifecycle fields

Revision ID: 72fa829402a4
Revises: efdbfe770ca4
Create Date: 2026-06-19 07:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '72fa829402a4'
down_revision = 'efdbfe770ca4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # dcf_assumption_sets
    op.add_column('dcf_assumption_sets', sa.Column('probability_of_failure', sa.Float(), nullable=True))
    op.add_column('dcf_assumption_sets', sa.Column('distress_sale_proceeds', sa.Float(), nullable=True))
    op.add_column('dcf_assumption_sets', sa.Column('book_value_of_equity', sa.Float(), nullable=True))
    op.add_column('dcf_assumption_sets', sa.Column('target_roe', sa.Float(), nullable=True))
    op.add_column('dcf_assumption_sets', sa.Column('basic_shares', sa.Float(), nullable=True))

    # dcf_outputs
    op.add_column('dcf_outputs', sa.Column('base_dcf_value', sa.Float(), nullable=True))
    op.add_column('dcf_outputs', sa.Column('pv_of_excess_returns', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('dcf_outputs', 'pv_of_excess_returns')
    op.drop_column('dcf_outputs', 'base_dcf_value')

    op.drop_column('dcf_assumption_sets', 'basic_shares')
    op.drop_column('dcf_assumption_sets', 'target_roe')
    op.drop_column('dcf_assumption_sets', 'book_value_of_equity')
    op.drop_column('dcf_assumption_sets', 'distress_sale_proceeds')
    op.drop_column('dcf_assumption_sets', 'probability_of_failure')
