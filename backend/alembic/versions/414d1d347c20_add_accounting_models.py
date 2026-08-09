"""add accounting normalization models

Revision ID: 414d1d347c20
Revises: 413c1d347c19
Create Date: 2026-06-17 04:28:30.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '414d1d347c20'
down_revision = '413c1d347c19'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Damodaran RD Benchmarks
    op.create_table('industry_rd_benchmarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_file_id', sa.Integer(), nullable=False),
        sa.Column('industry_name', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('rd_to_sales', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_file_id'], ['damodaran_dataset_files.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_industry_rd_benchmarks_id'), 'industry_rd_benchmarks', ['id'], unique=False)
    op.create_index(op.f('ix_industry_rd_benchmarks_industry_name'), 'industry_rd_benchmarks', ['industry_name'], unique=False)

    # 2. Damodaran Goodwill Benchmarks
    op.create_table('industry_goodwill_benchmarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_file_id', sa.Integer(), nullable=False),
        sa.Column('industry_name', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('goodwill_to_assets', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_file_id'], ['damodaran_dataset_files.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_industry_goodwill_benchmarks_id'), 'industry_goodwill_benchmarks', ['id'], unique=False)
    op.create_index(op.f('ix_industry_goodwill_benchmarks_industry_name'), 'industry_goodwill_benchmarks', ['industry_name'], unique=False)

    # 3. Company R&D History
    op.create_table('company_rd_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('rd_expense', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_company_rd_history_id'), 'company_rd_history', ['id'], unique=False)

    # 4. Valuation Accounting Adjustments
    op.create_table('valuation_accounting_adjustments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('valuation_run_id', sa.Integer(), nullable=False),
        sa.Column('adjustment_type', sa.String(length=50), nullable=False),
        sa.Column('original_value', sa.Float(), nullable=True),
        sa.Column('adjusted_value', sa.Float(), nullable=True),
        sa.Column('details_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['valuation_run_id'], ['valuation_models.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_valuation_accounting_adjustments_id'), 'valuation_accounting_adjustments', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_valuation_accounting_adjustments_id'), table_name='valuation_accounting_adjustments')
    op.drop_table('valuation_accounting_adjustments')

    op.drop_index(op.f('ix_company_rd_history_id'), table_name='company_rd_history')
    op.drop_table('company_rd_history')

    op.drop_index(op.f('ix_industry_goodwill_benchmarks_industry_name'), table_name='industry_goodwill_benchmarks')
    op.drop_index(op.f('ix_industry_goodwill_benchmarks_id'), table_name='industry_goodwill_benchmarks')
    op.drop_table('industry_goodwill_benchmarks')

    op.drop_index(op.f('ix_industry_rd_benchmarks_industry_name'), table_name='industry_rd_benchmarks')
    op.drop_index(op.f('ix_industry_rd_benchmarks_id'), table_name='industry_rd_benchmarks')
    op.drop_table('industry_rd_benchmarks')
