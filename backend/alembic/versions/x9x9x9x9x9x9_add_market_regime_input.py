"""add market regime input

Revision ID: x9x9x9x9x9x9
Revises: w8w8w8w8w8w8
Create Date: 2026-08-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'x9x9x9x9x9x9'
down_revision = 'w8w8w8w8w8w8'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('market_regime_inputs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('metric_name', sa.String(length=50), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('as_of_date', sa.Date(), nullable=False),
    sa.Column('source_url', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_market_regime_inputs_as_of_date'), 'market_regime_inputs', ['as_of_date'], unique=False)
    op.create_index(op.f('ix_market_regime_inputs_metric_name'), 'market_regime_inputs', ['metric_name'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_market_regime_inputs_metric_name'), table_name='market_regime_inputs')
    op.drop_index(op.f('ix_market_regime_inputs_as_of_date'), table_name='market_regime_inputs')
    op.drop_table('market_regime_inputs')
