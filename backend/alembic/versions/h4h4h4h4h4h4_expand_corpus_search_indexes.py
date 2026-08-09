"""Expand PostgreSQL full-text indexes to the owned research corpus.

Revision ID: h4h4h4h4h4h4
Revises: g3g3g3g3g3g3
Create Date: 2026-08-01
"""

from alembic import op


revision = "h4h4h4h4h4h4"
down_revision = "g3g3g3g3g3g3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX ix_thesis_notes_search_vector ON thesis_notes USING gin "
        "(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(thesis_text, '')))"
    )
    op.execute(
        "CREATE INDEX ix_alerts_search_vector ON alerts USING gin "
        "(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(summary, '') || ' ' || "
        "coalesce(what_changed, '') || ' ' || coalesce(why_it_matters, '') || ' ' || coalesce(evidence, '')))"
    )
    op.execute(
        "CREATE INDEX ix_decision_logs_search_vector ON decision_logs USING gin "
        "(to_tsvector('english', coalesce(decision_type, '') || ' ' || coalesce(rationale, '') || ' ' || "
        "coalesce(alternatives_considered, '')))"
    )
    op.execute(
        "CREATE INDEX ix_valuation_models_search_vector ON valuation_models USING gin "
        "(to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, '')))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_valuation_models_search_vector")
    op.execute("DROP INDEX IF EXISTS ix_decision_logs_search_vector")
    op.execute("DROP INDEX IF EXISTS ix_alerts_search_vector")
    op.execute("DROP INDEX IF EXISTS ix_thesis_notes_search_vector")
