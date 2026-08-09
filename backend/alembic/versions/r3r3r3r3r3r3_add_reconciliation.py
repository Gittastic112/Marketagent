"""add reconciliation records

Revision ID: r3r3r3r3r3r3
Revises: q2q2q2q2q2q2
Create Date: 2026-08-08 15:27:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'r3r3r3r3r3r3'
down_revision = 'q2q2q2q2q2q2'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'financial_reconciliation_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=False),
        sa.Column('check_name', sa.String(length=120), nullable=False),
        sa.Column('is_passed', sa.Boolean(), nullable=False),
        sa.Column('difference', sa.Float(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['period_id'], ['financial_statement_periods.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_reconciliation_records_company_id'), 'financial_reconciliation_records', ['company_id'], unique=False)
    op.create_index(op.f('ix_financial_reconciliation_records_period_id'), 'financial_reconciliation_records', ['period_id'], unique=False)
    op.create_index(op.f('ix_financial_reconciliation_records_check_name'), 'financial_reconciliation_records', ['check_name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_financial_reconciliation_records_check_name'), table_name='financial_reconciliation_records')
    op.drop_index(op.f('ix_financial_reconciliation_records_period_id'), table_name='financial_reconciliation_records')
    op.drop_index(op.f('ix_financial_reconciliation_records_company_id'), table_name='financial_reconciliation_records')
    op.drop_table('financial_reconciliation_records')
