"""add fcfe and dividend models

Revision ID: 416f1d347c22
Revises: 415e1d347c21
Create Date: 2026-06-17 10:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '416f1d347c22'
down_revision = '415e1d347c21'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # dcf_assumption_sets
    op.add_column('dcf_assumption_sets', sa.Column('net_income', sa.Float(), nullable=True))
    op.add_column('dcf_assumption_sets', sa.Column('capex', sa.Float(), nullable=True))
    op.add_column('dcf_assumption_sets', sa.Column('depreciation', sa.Float(), nullable=True))
    op.add_column('dcf_assumption_sets', sa.Column('change_in_nwc', sa.Float(), nullable=True))
    op.add_column('dcf_assumption_sets', sa.Column('new_debt_issued', sa.Float(), nullable=True))
    op.add_column('dcf_assumption_sets', sa.Column('debt_repaid', sa.Float(), nullable=True))
    op.add_column('dcf_assumption_sets', sa.Column('dividends', sa.Float(), nullable=True))
    op.add_column('dcf_assumption_sets', sa.Column('buybacks', sa.Float(), nullable=True))
    op.add_column('dcf_assumption_sets', sa.Column('stock_issuances', sa.Float(), nullable=True))
    op.add_column('dcf_assumption_sets', sa.Column('company_age', sa.Float(), nullable=True))

    # dcf_outputs
    op.add_column('dcf_outputs', sa.Column('fcfe_intrinsic_value_per_share', sa.Float(), nullable=True))
    op.add_column('dcf_outputs', sa.Column('ddm_intrinsic_value_per_share', sa.Float(), nullable=True))

    # damodaran_industry_dividend_benchmarks
    op.create_table('damodaran_industry_dividend_benchmarks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('dataset_file_id', sa.Integer(), nullable=False),
    sa.Column('industry_name', sa.String(length=255), nullable=False),
    sa.Column('country', sa.String(length=100), nullable=True),
    sa.Column('dividend_yield', sa.Float(), nullable=True),
    sa.Column('payout_ratio', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['dataset_file_id'], ['damodaran_dataset_files.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_damodaran_industry_dividend_benchmarks_id'), 'damodaran_industry_dividend_benchmarks', ['id'], unique=False)
    op.create_index(op.f('ix_damodaran_industry_dividend_benchmarks_industry_name'), 'damodaran_industry_dividend_benchmarks', ['industry_name'], unique=False)

    # damodaran_industry_fcfe_benchmarks
    op.create_table('damodaran_industry_fcfe_benchmarks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('dataset_file_id', sa.Integer(), nullable=False),
    sa.Column('industry_name', sa.String(length=255), nullable=False),
    sa.Column('country', sa.String(length=100), nullable=True),
    sa.Column('net_income', sa.Float(), nullable=True),
    sa.Column('capex_minus_depreciation', sa.Float(), nullable=True),
    sa.Column('change_in_wc', sa.Float(), nullable=True),
    sa.Column('net_debt_issued', sa.Float(), nullable=True),
    sa.Column('fcfe', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['dataset_file_id'], ['damodaran_dataset_files.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_damodaran_industry_fcfe_benchmarks_id'), 'damodaran_industry_fcfe_benchmarks', ['id'], unique=False)
    op.create_index(op.f('ix_damodaran_industry_fcfe_benchmarks_industry_name'), 'damodaran_industry_fcfe_benchmarks', ['industry_name'], unique=False)

def downgrade() -> None:
    pass
