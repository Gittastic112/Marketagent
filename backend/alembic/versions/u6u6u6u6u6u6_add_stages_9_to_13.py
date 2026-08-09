"""add stages 9 to 13

Revision ID: u6u6u6u6u6u6
Revises: t5t5t5t5t5t5
Create Date: 2026-08-08 17:19:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'u6u6u6u6u6u6'
down_revision: Union[str, None] = 't5t5t5t5t5t5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add Evaluation Models (Stage 9)
    op.create_table(
        'evaluation_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('run_name', sa.String(length=200), nullable=False),
        sa.Column('evaluation_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='running'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'financial_extraction_evals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evaluation_run_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('precision', sa.Float(), nullable=True),
        sa.Column('recall', sa.Float(), nullable=True),
        sa.Column('unit_accuracy', sa.Float(), nullable=True),
        sa.Column('period_accuracy', sa.Float(), nullable=True),
        sa.Column('source_locator_accuracy', sa.Float(), nullable=True),
        sa.Column('manual_intervention_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['raw_documents.id'], ),
        sa.ForeignKeyConstraint(['evaluation_run_id'], ['evaluation_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_extraction_evals_document_id'), 'financial_extraction_evals', ['document_id'], unique=False)
    op.create_index(op.f('ix_financial_extraction_evals_evaluation_run_id'), 'financial_extraction_evals', ['evaluation_run_id'], unique=False)

    op.create_table(
        'event_extraction_evals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evaluation_run_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('precision', sa.Float(), nullable=True),
        sa.Column('recall', sa.Float(), nullable=True),
        sa.Column('duplicate_suppression_rate', sa.Float(), nullable=True),
        sa.Column('false_positive_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('missed_material_events_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['raw_documents.id'], ),
        sa.ForeignKeyConstraint(['evaluation_run_id'], ['evaluation_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_event_extraction_evals_document_id'), 'event_extraction_evals', ['document_id'], unique=False)
    op.create_index(op.f('ix_event_extraction_evals_evaluation_run_id'), 'event_extraction_evals', ['evaluation_run_id'], unique=False)

    op.create_table(
        'alert_evals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evaluation_run_id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('user_classification', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['alert_id'], ['alerts.id'], ),
        sa.ForeignKeyConstraint(['evaluation_run_id'], ['evaluation_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alert_evals_alert_id'), 'alert_evals', ['alert_id'], unique=False)
    op.create_index(op.f('ix_alert_evals_evaluation_run_id'), 'alert_evals', ['evaluation_run_id'], unique=False)

    op.create_table(
        'valuation_evals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evaluation_run_id', sa.Integer(), nullable=False),
        sa.Column('valuation_model_id', sa.Integer(), nullable=False),
        sa.Column('reproducibility_passed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('guardrail_behavior_passed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('accounting_bridge_passed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('scenario_behavior_passed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reverse_dcf_passed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['evaluation_run_id'], ['evaluation_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['valuation_model_id'], ['valuation_models.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_valuation_evals_evaluation_run_id'), 'valuation_evals', ['evaluation_run_id'], unique=False)
    op.create_index(op.f('ix_valuation_evals_valuation_model_id'), 'valuation_evals', ['valuation_model_id'], unique=False)

    # 2. Modify NarrativeCluster (Stage 11)
    op.add_column('narrative_clusters', sa.Column('first_seen', sa.DateTime(timezone=True), nullable=True))
    op.add_column('narrative_clusters', sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True))
    op.add_column('narrative_clusters', sa.Column('velocity', sa.Float(), nullable=True))
    op.add_column('narrative_clusters', sa.Column('source_diversity', sa.Float(), nullable=True))
    op.add_column('narrative_clusters', sa.Column('confidence', sa.String(length=50), nullable=True))
    op.add_column('narrative_clusters', sa.Column('status', sa.String(length=50), nullable=False, server_default='Emerging'))

    # 3. Add MarketRegimeScore (Stage 12)
    op.create_table(
        'market_regime_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('score_date', sa.Date(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('options_score', sa.Float(), nullable=True),
        sa.Column('liquidity_score', sa.Float(), nullable=True),
        sa.Column('volume_score', sa.Float(), nullable=True),
        sa.Column('breadth_score', sa.Float(), nullable=True),
        sa.Column('macro_score', sa.Float(), nullable=True),
        sa.Column('confidence', sa.String(length=50), nullable=False, server_default='low'),
        sa.Column('warnings', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('mode', sa.String(length=50), nullable=False, server_default='Prototype'),
        sa.Column('live_modules', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('manual_modules', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('simulated_modules', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_market_regime_scores_score_date'), 'market_regime_scores', ['score_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_market_regime_scores_score_date'), table_name='market_regime_scores')
    op.drop_table('market_regime_scores')

    op.drop_column('narrative_clusters', 'status')
    op.drop_column('narrative_clusters', 'confidence')
    op.drop_column('narrative_clusters', 'source_diversity')
    op.drop_column('narrative_clusters', 'velocity')
    op.drop_column('narrative_clusters', 'last_seen')
    op.drop_column('narrative_clusters', 'first_seen')

    op.drop_index(op.f('ix_valuation_evals_valuation_model_id'), table_name='valuation_evals')
    op.drop_index(op.f('ix_valuation_evals_evaluation_run_id'), table_name='valuation_evals')
    op.drop_table('valuation_evals')

    op.drop_index(op.f('ix_alert_evals_evaluation_run_id'), table_name='alert_evals')
    op.drop_index(op.f('ix_alert_evals_alert_id'), table_name='alert_evals')
    op.drop_table('alert_evals')

    op.drop_index(op.f('ix_event_extraction_evals_evaluation_run_id'), table_name='event_extraction_evals')
    op.drop_index(op.f('ix_event_extraction_evals_document_id'), table_name='event_extraction_evals')
    op.drop_table('event_extraction_evals')

    op.drop_index(op.f('ix_financial_extraction_evals_evaluation_run_id'), table_name='financial_extraction_evals')
    op.drop_index(op.f('ix_financial_extraction_evals_document_id'), table_name='financial_extraction_evals')
    op.drop_table('financial_extraction_evals')

    op.drop_table('evaluation_runs')
