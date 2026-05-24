"""create mvp tables

Revision ID: 20260524_0001
Revises:
Create Date: 2026-05-24
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260524_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table("companies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sector", sa.String(length=120), nullable=True),
        sa.Column("industry", sa.String(length=120), nullable=True),
        sa.Column("exchange", sa.String(length=80), nullable=True),
        sa.Column("cik", sa.String(length=20), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cik"),
        sa.UniqueConstraint("ticker"),
    )
    op.create_index("ix_companies_ticker", "companies", ["ticker"])

    op.create_table("sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=True),
        sa.Column("reliability_score", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_sources_name", "sources", ["name"])
    op.create_index("ix_sources_source_type", "sources", ["source_type"])

    op.create_table("raw_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("raw_payload_json", sa.JSON(), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_hash"),
    )
    op.create_index("ix_raw_documents_content_hash", "raw_documents", ["content_hash"])
    op.create_index("ix_raw_documents_document_type", "raw_documents", ["document_type"])

    op.create_table("events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("raw_document_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("information_speed", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("credibility_score", sa.Integer(), nullable=True),
        sa.Column("novelty_score", sa.Integer(), nullable=True),
        sa.Column("impact_score", sa.Integer(), nullable=True),
        sa.Column("priority_score", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["raw_document_id"], ["raw_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_event_type", "events", ["event_type"])
    op.create_index("ix_events_information_speed", "events", ["information_speed"])

    op.create_table("alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("alert_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("why_it_matters", sa.Text(), nullable=True),
        sa.Column("what_changed", sa.Text(), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("confidence_bucket", sa.String(length=20), nullable=False),
        sa.Column("review_status", sa.String(length=40), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_alert_type", "alerts", ["alert_type"])

    op.create_table("thesis_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("thesis_text", sa.Text(), nullable=False),
        sa.Column("assumptions_json", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("thesis_notes")
    op.drop_index("ix_alerts_alert_type", table_name="alerts")
    op.drop_table("alerts")
    op.drop_index("ix_events_information_speed", table_name="events")
    op.drop_index("ix_events_event_type", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_raw_documents_document_type", table_name="raw_documents")
    op.drop_index("ix_raw_documents_content_hash", table_name="raw_documents")
    op.drop_table("raw_documents")
    op.drop_index("ix_sources_source_type", table_name="sources")
    op.drop_index("ix_sources_name", table_name="sources")
    op.drop_table("sources")
    op.drop_index("ix_companies_ticker", table_name="companies")
    op.drop_table("companies")
