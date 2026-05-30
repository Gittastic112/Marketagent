"""add_missing_tables

Revision ID: 20260530_0725
Revises: 20260530_0718
Create Date: 2026-05-30 07:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260530_0725'
down_revision: Union[str, None] = '20260530_0718'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Exposure Tags
    op.create_table('exposure_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exposure_tags_name'), 'exposure_tags', ['name'], unique=True)

    op.create_table('company_exposure_tags',
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['exposure_tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('company_id', 'tag_id')
    )

    # 2. Event Corroborations and Contradictions
    op.create_table('event_corroborations',
        sa.Column('source_event_id', sa.Integer(), nullable=False),
        sa.Column('target_event_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['source_event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['target_event_id'], ['events.id'], ),
        sa.PrimaryKeyConstraint('source_event_id', 'target_event_id')
    )

    op.create_table('event_contradictions',
        sa.Column('source_event_id', sa.Integer(), nullable=False),
        sa.Column('target_event_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['source_event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['target_event_id'], ['events.id'], ),
        sa.PrimaryKeyConstraint('source_event_id', 'target_event_id')
    )

    # 3. Thesis Assumptions and Changes
    op.create_table('thesis_assumptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thesis_note_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('original_confidence', sa.String(length=40), nullable=False),
        sa.Column('current_confidence', sa.String(length=40), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['thesis_note_id'], ['thesis_notes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('thesis_changes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thesis_note_id', sa.Integer(), nullable=False),
        sa.Column('change_summary', sa.Text(), nullable=False),
        sa.Column('drift_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['thesis_note_id'], ['thesis_notes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Thesis Note Drift Score
    op.add_column('thesis_notes', sa.Column('thesis_drift_score', sa.Float(), nullable=False, server_default='0.0'))


def downgrade() -> None:
    op.drop_column('thesis_notes', 'thesis_drift_score')
    op.drop_table('thesis_changes')
    op.drop_table('thesis_assumptions')
    op.drop_table('event_contradictions')
    op.drop_table('event_corroborations')
    op.drop_table('company_exposure_tags')
    op.drop_index(op.f('ix_exposure_tags_name'), table_name='exposure_tags')
    op.drop_table('exposure_tags')
