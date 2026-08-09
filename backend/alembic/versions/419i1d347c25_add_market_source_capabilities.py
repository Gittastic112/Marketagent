"""add_market_source_capabilities

Revision ID: 419i1d347c25
Revises: 418h1d347c24
Create Date: 2026-06-17 00:00:00.000000
"""

from collections.abc import Sequence
from datetime import UTC, datetime

from alembic import op
import sqlalchemy as sa


revision: str = "419i1d347c25"
down_revision: str | Sequence[str] | None = "418h1d347c24"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "market_source_capabilities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("market", sa.String(length=10), nullable=False),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("provider_name", sa.String(length=120), nullable=False),
        sa.Column("capability", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("requires_api_key", sa.Boolean(), nullable=False),
        sa.Column("freshness_expected_seconds", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(length=1000), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "market",
            "source_type",
            "provider_name",
            "capability",
            name="uq_market_source_capability",
        ),
    )
    op.create_index(op.f("ix_market_source_capabilities_market"), "market_source_capabilities", ["market"])
    op.create_index(op.f("ix_market_source_capabilities_source_type"), "market_source_capabilities", ["source_type"])
    op.create_index(op.f("ix_market_source_capabilities_provider_name"), "market_source_capabilities", ["provider_name"])
    op.create_index(op.f("ix_market_source_capabilities_capability"), "market_source_capabilities", ["capability"])
    op.create_index(op.f("ix_market_source_capabilities_status"), "market_source_capabilities", ["status"])

    capabilities = sa.table(
        "market_source_capabilities",
        sa.column("market", sa.String),
        sa.column("source_type", sa.String),
        sa.column("provider_name", sa.String),
        sa.column("capability", sa.String),
        sa.column("status", sa.String),
        sa.column("requires_api_key", sa.Boolean),
        sa.column("freshness_expected_seconds", sa.Integer),
        sa.column("notes", sa.String),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    now = datetime.now(UTC)
    op.bulk_insert(
        capabilities,
        [
            {
                "market": "US",
                "source_type": "filings",
                "provider_name": "SEC EDGAR",
                "capability": "sec_filings",
                "status": "available",
                "requires_api_key": False,
                "freshness_expected_seconds": 86400,
                "notes": "SEC EDGAR submissions and filing documents. Requires a valid SEC_USER_AGENT.",
                "updated_at": now,
            },
            {
                "market": "US",
                "source_type": "fundamentals",
                "provider_name": "SEC EDGAR",
                "capability": "sec_fundamentals",
                "status": "available",
                "requires_api_key": False,
                "freshness_expected_seconds": 86400,
                "notes": "SEC companyfacts XBRL data. Requires a valid SEC_USER_AGENT.",
                "updated_at": now,
            },
            {
                "market": "US",
                "source_type": "market_prices",
                "provider_name": "Alpha Vantage/FMP",
                "capability": "market_prices",
                "status": "not_configured",
                "requires_api_key": True,
                "freshness_expected_seconds": 3600,
                "notes": "Provider-backed US prices require ALPHA_VANTAGE_API_KEY or FMP_API_KEY.",
                "updated_at": now,
            },
            {
                "market": "IN",
                "source_type": "filings",
                "provider_name": "NSE/BSE",
                "capability": "corporate_announcements",
                "status": "manual_only",
                "requires_api_key": False,
                "freshness_expected_seconds": None,
                "notes": "Official exchange pages exist, but automated provider ingestion is not enabled.",
                "updated_at": now,
            },
            {
                "market": "IN",
                "source_type": "fundamentals",
                "provider_name": "Manual Upload",
                "capability": "financial_statements",
                "status": "manual_only",
                "requires_api_key": False,
                "freshness_expected_seconds": None,
                "notes": "Use manual entries or uploads until a licensed India fundamentals provider is configured.",
                "updated_at": now,
            },
            {
                "market": "IN",
                "source_type": "market_prices",
                "provider_name": "Alpha Vantage/FMP",
                "capability": "market_prices",
                "status": "not_configured",
                "requires_api_key": True,
                "freshness_expected_seconds": 3600,
                "notes": "Provider-backed India prices require symbol support and ALPHA_VANTAGE_API_KEY or FMP_API_KEY.",
                "updated_at": now,
            },
            {
                "market": "IN",
                "source_type": "valuation_benchmarks",
                "provider_name": "Damodaran",
                "capability": "damodaran_benchmarks",
                "status": "available",
                "requires_api_key": False,
                "freshness_expected_seconds": None,
                "notes": "Imported Damodaran industry valuation benchmark files are available locally.",
                "updated_at": now,
            },
            {
                "market": "IN",
                "source_type": "macro",
                "provider_name": "Damodaran",
                "capability": "macro_sensitivity",
                "status": "available",
                "requires_api_key": False,
                "freshness_expected_seconds": None,
                "notes": "Imported macro duration and macro sensitivity files are available locally.",
                "updated_at": now,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_market_source_capabilities_status"), table_name="market_source_capabilities")
    op.drop_index(op.f("ix_market_source_capabilities_capability"), table_name="market_source_capabilities")
    op.drop_index(op.f("ix_market_source_capabilities_provider_name"), table_name="market_source_capabilities")
    op.drop_index(op.f("ix_market_source_capabilities_source_type"), table_name="market_source_capabilities")
    op.drop_index(op.f("ix_market_source_capabilities_market"), table_name="market_source_capabilities")
    op.drop_table("market_source_capabilities")
