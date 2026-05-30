"""create fundamentals and dcf tables

Revision ID: 20260528_2005
Revises: 20260528_0010
Create Date: 2026-05-28 20:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260528_2005'
down_revision: Union[str, None] = '20260528_0010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # financial_statement_periods
    op.create_table('financial_statement_periods',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('period_type', sa.String(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('quarter', sa.Integer(), nullable=True),
    sa.Column('report_date', sa.Date(), nullable=False),
    sa.Column('currency', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_statement_periods_company_id'), 'financial_statement_periods', ['company_id'], unique=False)
    op.create_index(op.f('ix_financial_statement_periods_period_type'), 'financial_statement_periods', ['period_type'], unique=False)
    op.create_index(op.f('ix_financial_statement_periods_year'), 'financial_statement_periods', ['year'], unique=False)

    # financial_metrics
    op.create_table('financial_metrics',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('period_id', sa.Integer(), nullable=False),
    sa.Column('metric_name', sa.String(), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('unit', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['period_id'], ['financial_statement_periods.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_metrics_period_id'), 'financial_metrics', ['period_id'], unique=False)
    op.create_index(op.f('ix_financial_metrics_metric_name'), 'financial_metrics', ['metric_name'], unique=False)

    # valuation_models
    op.create_table('valuation_models',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_valuation_models_company_id'), 'valuation_models', ['company_id'], unique=False)

    # dcf_assumption_sets
    op.create_table('dcf_assumption_sets',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('valuation_model_id', sa.Integer(), nullable=False),
    sa.Column('scenario', sa.String(), nullable=False),
    sa.Column('discount_rate', sa.Float(), nullable=False),
    sa.Column('terminal_growth_rate', sa.Float(), nullable=False),
    sa.Column('projection_years', sa.Integer(), nullable=False),
    sa.Column('assumptions_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['valuation_model_id'], ['valuation_models.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dcf_assumption_sets_valuation_model_id'), 'dcf_assumption_sets', ['valuation_model_id'], unique=False)

    # dcf_outputs
    op.create_table('dcf_outputs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('assumption_set_id', sa.Integer(), nullable=False),
    sa.Column('enterprise_value', sa.Float(), nullable=False),
    sa.Column('equity_value', sa.Float(), nullable=False),
    sa.Column('implied_share_price', sa.Float(), nullable=False),
    sa.Column('output_json', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['assumption_set_id'], ['dcf_assumption_sets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dcf_outputs_assumption_set_id'), 'dcf_outputs', ['assumption_set_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_dcf_outputs_assumption_set_id'), table_name='dcf_outputs')
    op.drop_table('dcf_outputs')
    op.drop_index(op.f('ix_dcf_assumption_sets_valuation_model_id'), table_name='dcf_assumption_sets')
    op.drop_table('dcf_assumption_sets')
    op.drop_index(op.f('ix_valuation_models_company_id'), table_name='valuation_models')
    op.drop_table('valuation_models')
    op.drop_index(op.f('ix_financial_metrics_metric_name'), table_name='financial_metrics')
    op.drop_index(op.f('ix_financial_metrics_period_id'), table_name='financial_metrics')
    op.drop_table('financial_metrics')
    op.drop_index(op.f('ix_financial_statement_periods_year'), table_name='financial_statement_periods')
    op.drop_index(op.f('ix_financial_statement_periods_period_type'), table_name='financial_statement_periods')
    op.drop_index(op.f('ix_financial_statement_periods_company_id'), table_name='financial_statement_periods')
    op.drop_table('financial_statement_periods')
