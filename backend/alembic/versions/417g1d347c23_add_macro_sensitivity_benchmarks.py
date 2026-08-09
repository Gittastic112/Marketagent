"""add macro sensitivity benchmarks

Revision ID: 417g1d347c23
Revises: 416f1d347c22
Create Date: 2026-06-17 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '417g1d347c23'
down_revision = '416f1d347c22'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'sector_macro_sensitivity_benchmarks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_file', sa.String(length=255), nullable=False),
        sa.Column('sic_code', sa.String(length=20), nullable=False),
        sa.Column('industry_name', sa.String(length=255), nullable=False),
        sa.Column('firm_value_duration', sa.Float(), nullable=True),
        sa.Column('firm_value_cyclicality', sa.Float(), nullable=True),
        sa.Column('firm_value_inflation', sa.Float(), nullable=True),
        sa.Column('firm_value_currency', sa.Float(), nullable=True),
        sa.Column('operating_income_duration', sa.Float(), nullable=True),
        sa.Column('operating_income_cyclicality', sa.Float(), nullable=True),
        sa.Column('operating_income_inflation', sa.Float(), nullable=True),
        sa.Column('operating_income_currency', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_sector_macro_sensitivity_benchmarks_source_file'),
        'sector_macro_sensitivity_benchmarks',
        ['source_file'],
        unique=False,
    )
    op.create_index(
        op.f('ix_sector_macro_sensitivity_benchmarks_sic_code'),
        'sector_macro_sensitivity_benchmarks',
        ['sic_code'],
        unique=False,
    )
    op.create_index(
        op.f('ix_sector_macro_sensitivity_benchmarks_industry_name'),
        'sector_macro_sensitivity_benchmarks',
        ['industry_name'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_sector_macro_sensitivity_benchmarks_industry_name'),
        table_name='sector_macro_sensitivity_benchmarks',
    )
    op.drop_index(
        op.f('ix_sector_macro_sensitivity_benchmarks_sic_code'),
        table_name='sector_macro_sensitivity_benchmarks',
    )
    op.drop_index(
        op.f('ix_sector_macro_sensitivity_benchmarks_source_file'),
        table_name='sector_macro_sensitivity_benchmarks',
    )
    op.drop_table('sector_macro_sensitivity_benchmarks')
