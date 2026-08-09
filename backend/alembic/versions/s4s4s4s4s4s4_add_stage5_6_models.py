"""add stage5_6_models

Revision ID: s4s4s4s4s4s4
Revises: r3r3r3r3r3r3
Create Date: 2026-08-08 16:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 's4s4s4s4s4s4'
down_revision: Union[str, None] = 'r3r3r3r3r3r3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # forecast_calibrations
    op.create_table(
        'forecast_calibrations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('valuation_model_id', sa.Integer(), nullable=True),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('metric_name', sa.String(length=120), nullable=False),
        sa.Column('forecast_value', sa.Float(), nullable=False),
        sa.Column('actual_value', sa.Float(), nullable=False),
        sa.Column('error_margin', sa.Float(), nullable=False),
        sa.Column('forecast_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actual_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('interpretation', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['valuation_model_id'], ['valuation_models.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_forecast_calibrations_company_id'), 'forecast_calibrations', ['company_id'], unique=False)
    op.create_index(op.f('ix_forecast_calibrations_metric_name'), 'forecast_calibrations', ['metric_name'], unique=False)

    # peer_valuation_sets
    op.create_table(
        'peer_valuation_sets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('peer_identifiers_json', sa.JSON(), nullable=False),
        sa.Column('aggregate_metrics_json', sa.JSON(), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_peer_valuation_sets_company_id'), 'peer_valuation_sets', ['company_id'], unique=False)
    op.create_index(op.f('ix_peer_valuation_sets_user_id'), 'peer_valuation_sets', ['user_id'], unique=False)

    # entity_scores
    op.create_table(
        'entity_scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('fundamental_score', sa.Integer(), nullable=True),
        sa.Column('valuation_score', sa.Integer(), nullable=True),
        sa.Column('narrative_score', sa.Integer(), nullable=True),
        sa.Column('sentiment_score', sa.Integer(), nullable=True),
        sa.Column('risk_score', sa.Integer(), nullable=True),
        sa.Column('momentum_score', sa.Integer(), nullable=True),
        sa.Column('overall_confidence_score', sa.Integer(), nullable=True),
        sa.Column('score_breakdown_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_entity_scores_company_id'), 'entity_scores', ['company_id'], unique=True)

    # decision_readiness
    op.create_table(
        'decision_readiness',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('financial_ready', sa.Boolean(), nullable=False),
        sa.Column('valuation_ready', sa.Boolean(), nullable=False),
        sa.Column('thesis_ready', sa.Boolean(), nullable=False),
        sa.Column('evidence_ready', sa.Boolean(), nullable=False),
        sa.Column('portfolio_ready', sa.Boolean(), nullable=False),
        sa.Column('catalyst_ready', sa.Boolean(), nullable=False),
        sa.Column('overall_status', sa.String(length=50), nullable=False),
        sa.Column('blocking_issues_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_decision_readiness_company_id'), 'decision_readiness', ['company_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_decision_readiness_company_id'), table_name='decision_readiness')
    op.drop_table('decision_readiness')
    op.drop_index(op.f('ix_entity_scores_company_id'), table_name='entity_scores')
    op.drop_table('entity_scores')
    op.drop_index(op.f('ix_peer_valuation_sets_user_id'), table_name='peer_valuation_sets')
    op.drop_index(op.f('ix_peer_valuation_sets_company_id'), table_name='peer_valuation_sets')
    op.drop_table('peer_valuation_sets')
    op.drop_index(op.f('ix_forecast_calibrations_metric_name'), table_name='forecast_calibrations')
    op.drop_index(op.f('ix_forecast_calibrations_company_id'), table_name='forecast_calibrations')
    op.drop_table('forecast_calibrations')
