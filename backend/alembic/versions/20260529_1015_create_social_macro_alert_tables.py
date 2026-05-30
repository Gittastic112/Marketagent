"""create_social_macro_alert_tables

Revision ID: 20260529_1015
Revises: 20260529_0940
Create Date: 2026-05-29 10:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260529_1015'
down_revision: Union[str, None] = '20260529_0940'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Social & Narratives
    op.create_table('social_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('author', sa.String(length=100), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payload_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_social_posts_content_hash'), 'social_posts', ['content_hash'], unique=True)
    op.create_index(op.f('ix_social_posts_platform'), 'social_posts', ['platform'], unique=False)

    op.create_table('sentiment_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('score', sa.String(length=50), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['post_id'], ['social_posts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sentiment_scores_company_id'), 'sentiment_scores', ['company_id'], unique=False)
    op.create_index(op.f('ix_sentiment_scores_post_id'), 'sentiment_scores', ['post_id'], unique=False)

    op.create_table('narrative_clusters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('narrative_claims',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cluster_id', sa.Integer(), nullable=False),
        sa.Column('claim_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['cluster_id'], ['narrative_clusters.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_narrative_claims_cluster_id'), 'narrative_claims', ['cluster_id'], unique=False)

    op.create_table('narrative_mentions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cluster_id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('context_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['cluster_id'], ['narrative_clusters.id'], ),
        sa.ForeignKeyConstraint(['post_id'], ['social_posts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_narrative_mentions_cluster_id'), 'narrative_mentions', ['cluster_id'], unique=False)
    op.create_index(op.f('ix_narrative_mentions_post_id'), 'narrative_mentions', ['post_id'], unique=False)

    # 2. Macro
    op.create_table('macro_series',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('units', sa.String(), nullable=True),
        sa.Column('frequency', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_macro_series_name'), 'macro_series', ['name'], unique=True)

    op.create_table('macro_observations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('series_id', sa.Integer(), nullable=False),
        sa.Column('date_recorded', sa.Date(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['series_id'], ['macro_series.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_macro_observations_date_recorded'), 'macro_observations', ['date_recorded'], unique=False)
    op.create_index(op.f('ix_macro_observations_series_id'), 'macro_observations', ['series_id'], unique=False)

    # 3. Config / Alerts
    op.create_table('alert_portfolio_impacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('exposure_amount', sa.Float(), nullable=False),
        sa.Column('impact_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['alert_id'], ['alerts.id'], ),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('scoring_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('weight_credibility', sa.Float(), nullable=False),
        sa.Column('weight_novelty', sa.Float(), nullable=False),
        sa.Column('weight_impact', sa.Float(), nullable=False),
        sa.Column('weight_speed', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('scoring_configs')
    op.drop_table('alert_portfolio_impacts')
    
    op.drop_index(op.f('ix_macro_observations_series_id'), table_name='macro_observations')
    op.drop_index(op.f('ix_macro_observations_date_recorded'), table_name='macro_observations')
    op.drop_table('macro_observations')
    op.drop_index(op.f('ix_macro_series_name'), table_name='macro_series')
    op.drop_table('macro_series')

    op.drop_index(op.f('ix_narrative_mentions_post_id'), table_name='narrative_mentions')
    op.drop_index(op.f('ix_narrative_mentions_cluster_id'), table_name='narrative_mentions')
    op.drop_table('narrative_mentions')
    op.drop_index(op.f('ix_narrative_claims_cluster_id'), table_name='narrative_claims')
    op.drop_table('narrative_claims')
    op.drop_table('narrative_clusters')
    op.drop_index(op.f('ix_sentiment_scores_post_id'), table_name='sentiment_scores')
    op.drop_index(op.f('ix_sentiment_scores_company_id'), table_name='sentiment_scores')
    op.drop_table('sentiment_scores')
    op.drop_index(op.f('ix_social_posts_platform'), table_name='social_posts')
    op.drop_index(op.f('ix_social_posts_content_hash'), table_name='social_posts')
    op.drop_table('social_posts')
