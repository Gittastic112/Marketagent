"""add damodaran fundamentals

Revision ID: 413c1d347c19
Revises: 412b1d347c18
Create Date: 2026-06-17 04:24:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '413c1d347c19'
down_revision = '412b1d347c18'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Margin Benchmarks
    op.create_table('damodaran_industry_margin_benchmarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_file_id', sa.Integer(), nullable=False),
        sa.Column('industry_name', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('gross_margin', sa.Float(), nullable=True),
        sa.Column('ebitda_margin', sa.Float(), nullable=True),
        sa.Column('ebit_margin', sa.Float(), nullable=True),
        sa.Column('net_margin', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_file_id'], ['damodaran_dataset_files.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_damodaran_industry_margin_benchmarks_id'), 'damodaran_industry_margin_benchmarks', ['id'], unique=False)
    op.create_index(op.f('ix_damodaran_industry_margin_benchmarks_industry_name'), 'damodaran_industry_margin_benchmarks', ['industry_name'], unique=False)

    # 2. Capex Benchmarks
    op.create_table('damodaran_industry_capex_benchmarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_file_id', sa.Integer(), nullable=False),
        sa.Column('industry_name', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('capex_to_sales', sa.Float(), nullable=True),
        sa.Column('net_capex_to_sales', sa.Float(), nullable=True),
        sa.Column('sales_to_capital', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_file_id'], ['damodaran_dataset_files.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_damodaran_industry_capex_benchmarks_id'), 'damodaran_industry_capex_benchmarks', ['id'], unique=False)
    op.create_index(op.f('ix_damodaran_industry_capex_benchmarks_industry_name'), 'damodaran_industry_capex_benchmarks', ['industry_name'], unique=False)

    # 3. WC Benchmarks
    op.create_table('damodaran_industry_working_capital_benchmarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_file_id', sa.Integer(), nullable=False),
        sa.Column('industry_name', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('wc_to_sales', sa.Float(), nullable=True),
        sa.Column('non_cash_wc_to_sales', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_file_id'], ['damodaran_dataset_files.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_damodaran_industry_working_capital_benchmarks_id'), 'damodaran_industry_working_capital_benchmarks', ['id'], unique=False)
    op.create_index(op.f('ix_damodaran_industry_working_capital_benchmarks_industry_name'), 'damodaran_industry_working_capital_benchmarks', ['industry_name'], unique=False)

    # 4. ROE Benchmarks
    op.create_table('damodaran_industry_roe_benchmarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_file_id', sa.Integer(), nullable=False),
        sa.Column('industry_name', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('roe', sa.Float(), nullable=True),
        sa.Column('roc', sa.Float(), nullable=True),
        sa.Column('roic', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_file_id'], ['damodaran_dataset_files.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_damodaran_industry_roe_benchmarks_id'), 'damodaran_industry_roe_benchmarks', ['id'], unique=False)
    op.create_index(op.f('ix_damodaran_industry_roe_benchmarks_industry_name'), 'damodaran_industry_roe_benchmarks', ['industry_name'], unique=False)

    # 5. Growth Benchmarks
    op.create_table('damodaran_industry_fundamental_growth',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_file_id', sa.Integer(), nullable=False),
        sa.Column('industry_name', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('expected_revenue_growth', sa.Float(), nullable=True),
        sa.Column('expected_ebit_growth', sa.Float(), nullable=True),
        sa.Column('expected_eps_growth', sa.Float(), nullable=True),
        sa.Column('historical_revenue_growth', sa.Float(), nullable=True),
        sa.Column('historical_ebit_growth', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_file_id'], ['damodaran_dataset_files.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_damodaran_industry_fundamental_growth_id'), 'damodaran_industry_fundamental_growth', ['id'], unique=False)
    op.create_index(op.f('ix_damodaran_industry_fundamental_growth_industry_name'), 'damodaran_industry_fundamental_growth', ['industry_name'], unique=False)

    # 6. Financing Flows
    op.create_table('damodaran_industry_financing_flows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_file_id', sa.Integer(), nullable=False),
        sa.Column('industry_name', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('debt_to_equity', sa.Float(), nullable=True),
        sa.Column('debt_to_capital', sa.Float(), nullable=True),
        sa.Column('effective_tax_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_file_id'], ['damodaran_dataset_files.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_damodaran_industry_financing_flows_id'), 'damodaran_industry_financing_flows', ['id'], unique=False)
    op.create_index(op.f('ix_damodaran_industry_financing_flows_industry_name'), 'damodaran_industry_financing_flows', ['industry_name'], unique=False)

    # 7. Regression Model Coefficients
    op.create_table('regression_model_coefficients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('variable_name', sa.String(length=100), nullable=False),
        sa.Column('coefficient_value', sa.Float(), nullable=False),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('version_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_regression_model_coefficients_id'), 'regression_model_coefficients', ['id'], unique=False)
    op.create_index(op.f('ix_regression_model_coefficients_model_name'), 'regression_model_coefficients', ['model_name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_regression_model_coefficients_model_name'), table_name='regression_model_coefficients')
    op.drop_index(op.f('ix_regression_model_coefficients_id'), table_name='regression_model_coefficients')
    op.drop_table('regression_model_coefficients')

    op.drop_index(op.f('ix_damodaran_industry_financing_flows_industry_name'), table_name='damodaran_industry_financing_flows')
    op.drop_index(op.f('ix_damodaran_industry_financing_flows_id'), table_name='damodaran_industry_financing_flows')
    op.drop_table('damodaran_industry_financing_flows')

    op.drop_index(op.f('ix_damodaran_industry_fundamental_growth_industry_name'), table_name='damodaran_industry_fundamental_growth')
    op.drop_index(op.f('ix_damodaran_industry_fundamental_growth_id'), table_name='damodaran_industry_fundamental_growth')
    op.drop_table('damodaran_industry_fundamental_growth')

    op.drop_index(op.f('ix_damodaran_industry_roe_benchmarks_industry_name'), table_name='damodaran_industry_roe_benchmarks')
    op.drop_index(op.f('ix_damodaran_industry_roe_benchmarks_id'), table_name='damodaran_industry_roe_benchmarks')
    op.drop_table('damodaran_industry_roe_benchmarks')

    op.drop_index(op.f('ix_damodaran_industry_working_capital_benchmarks_industry_name'), table_name='damodaran_industry_working_capital_benchmarks')
    op.drop_index(op.f('ix_damodaran_industry_working_capital_benchmarks_id'), table_name='damodaran_industry_working_capital_benchmarks')
    op.drop_table('damodaran_industry_working_capital_benchmarks')

    op.drop_index(op.f('ix_damodaran_industry_capex_benchmarks_industry_name'), table_name='damodaran_industry_capex_benchmarks')
    op.drop_index(op.f('ix_damodaran_industry_capex_benchmarks_id'), table_name='damodaran_industry_capex_benchmarks')
    op.drop_table('damodaran_industry_capex_benchmarks')

    op.drop_index(op.f('ix_damodaran_industry_margin_benchmarks_industry_name'), table_name='damodaran_industry_margin_benchmarks')
    op.drop_index(op.f('ix_damodaran_industry_margin_benchmarks_id'), table_name='damodaran_industry_margin_benchmarks')
    op.drop_table('damodaran_industry_margin_benchmarks')
