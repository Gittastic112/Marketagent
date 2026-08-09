"""add stage 14

Revision ID: v7v7v7v7v7v7
Revises: u6u6u6u6u6u6
Create Date: 2026-08-08 17:22:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'v7v7v7v7v7v7'
down_revision: Union[str, None] = 'u6u6u6u6u6u6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Modify DecisionLog
    op.add_column('decision_logs', sa.Column('current_thesis', sa.Text(), nullable=True))
    op.add_column('decision_logs', sa.Column('valuation', sa.Text(), nullable=True))
    op.add_column('decision_logs', sa.Column('decision_readiness', sa.String(length=50), nullable=True))
    op.add_column('decision_logs', sa.Column('key_supporting_evidence', sa.Text(), nullable=True))
    op.add_column('decision_logs', sa.Column('key_contradictory_evidence', sa.Text(), nullable=True))
    op.add_column('decision_logs', sa.Column('uncertainties', sa.Text(), nullable=True))
    op.add_column('decision_logs', sa.Column('expected_catalysts', sa.Text(), nullable=True))
    op.add_column('decision_logs', sa.Column('what_would_change_the_view', sa.Text(), nullable=True))
    op.add_column('decision_logs', sa.Column('portfolio_context', sa.Text(), nullable=True))

    # 2. Add OutcomeReview
    op.create_table(
        'outcome_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('decision_log_id', sa.Integer(), nullable=False),
        sa.Column('what_happened', sa.Text(), nullable=False),
        sa.Column('wrong_assumption', sa.Text(), nullable=True),
        sa.Column('information_unavailable_or_misinterpreted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('valuation_wrong', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('thesis_wrong', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('timing_wrong', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sizing_wrong', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['decision_log_id'], ['decision_logs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_outcome_reviews_decision_log_id'), 'outcome_reviews', ['decision_log_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_outcome_reviews_decision_log_id'), table_name='outcome_reviews')
    op.drop_table('outcome_reviews')

    op.drop_column('decision_logs', 'portfolio_context')
    op.drop_column('decision_logs', 'what_would_change_the_view')
    op.drop_column('decision_logs', 'expected_catalysts')
    op.drop_column('decision_logs', 'uncertainties')
    op.drop_column('decision_logs', 'key_contradictory_evidence')
    op.drop_column('decision_logs', 'key_supporting_evidence')
    op.drop_column('decision_logs', 'decision_readiness')
    op.drop_column('decision_logs', 'valuation')
    op.drop_column('decision_logs', 'current_thesis')
