"""normalize peer valuation members and revision snapshots

Revision ID: l3l3l3l3l3l3
Revises: k2k2k2k2k2k2
Create Date: 2026-09-02
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Any

from alembic import op
import sqlalchemy as sa


revision: str = "l3l3l3l3l3l3"
down_revision: str | None = "k2k2k2k2k2k2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _member_columns(parent_column: str, parent_table: str) -> list[sa.Column[Any]]:
    return [
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(parent_column, sa.Integer(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("identifier", sa.String(length=80), nullable=False),
        sa.Column("peer_company_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=160), nullable=True),
        sa.Column("included", sa.Boolean(), nullable=False),
        sa.Column("pe", sa.Float(), nullable=True),
        sa.Column("pbv", sa.Float(), nullable=True),
        sa.Column("ps", sa.Float(), nullable=True),
        sa.Column("ev_sales", sa.Float(), nullable=True),
        sa.Column("ev_ebitda", sa.Float(), nullable=True),
        sa.Column("ev_ebit", sa.Float(), nullable=True),
        sa.Column("source_name", sa.String(length=160), nullable=True),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("source_as_of", sa.Date(), nullable=True),
        sa.Column("claim_type", sa.String(length=30), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("country", sa.String(length=120), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("fiscal_period_end", sa.Date(), nullable=True),
        sa.Column("accounting_standard", sa.String(length=40), nullable=True),
        sa.Column("market_cap", sa.Float(), nullable=True),
        sa.Column("revenue_growth_pct", sa.Float(), nullable=True),
        sa.Column("ebitda_margin_pct", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint([parent_column], [f"{parent_table}.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["peer_company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    ]


def _date_value(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _normalized_row(
    member: Any,
    *,
    parent_column: str,
    parent_id: int,
    ordinal: int,
    company_ids: set[int],
) -> dict[str, Any] | None:
    raw = member if isinstance(member, dict) else {"identifier": str(member)}
    identifier = str(raw.get("identifier") or "").strip().upper()
    if not identifier:
        return None
    multiples = raw.get("multiples") if isinstance(raw.get("multiples"), dict) else {}
    peer_company_id = raw.get("companyId")
    if not isinstance(peer_company_id, int) or peer_company_id not in company_ids:
        peer_company_id = None
    currency = str(raw.get("currency") or "").strip().upper() or None
    return {
        parent_column: parent_id,
        "ordinal": ordinal,
        "identifier": identifier,
        "peer_company_id": peer_company_id,
        "name": raw.get("name"),
        "included": bool(raw.get("included", True)),
        "pe": multiples.get("pe"),
        "pbv": multiples.get("pbv"),
        "ps": multiples.get("ps"),
        "ev_sales": multiples.get("ev_sales"),
        "ev_ebitda": multiples.get("ev_ebitda"),
        "ev_ebit": multiples.get("ev_ebit"),
        "source_name": raw.get("sourceName"),
        "source_url": raw.get("sourceUrl"),
        "source_as_of": _date_value(raw.get("sourceAsOf")),
        "claim_type": raw.get("claimType"),
        "notes": raw.get("notes"),
        "country": raw.get("country"),
        "currency": currency,
        "fiscal_period_end": _date_value(raw.get("fiscalPeriodEnd")),
        "accounting_standard": raw.get("accountingStandard"),
        "market_cap": raw.get("marketCap"),
        "revenue_growth_pct": raw.get("revenueGrowthPct"),
        "ebitda_margin_pct": raw.get("ebitdaMarginPct"),
    }


def _backfill_rows(
    rows: list[dict[str, Any]],
    *,
    parent_column: str,
    company_ids: set[int],
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        seen: set[str] = set()
        for ordinal, member in enumerate(row["members"] or []):
            item = _normalized_row(
                member,
                parent_column=parent_column,
                parent_id=row["id"],
                ordinal=ordinal,
                company_ids=company_ids,
            )
            if item is None or item["identifier"] in seen:
                continue
            seen.add(item["identifier"])
            normalized.append(item)
    return normalized


def upgrade() -> None:
    current_members = op.create_table(
        "peer_valuation_members",
        *_member_columns("peer_set_id", "peer_valuation_sets"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "peer_set_id", "ordinal", name="uq_peer_valuation_members_set_ordinal"
        ),
        sa.UniqueConstraint(
            "peer_set_id", "identifier", name="uq_peer_valuation_members_set_identifier"
        ),
    )
    revision_members = op.create_table(
        "peer_valuation_revision_members",
        *_member_columns("revision_id", "peer_valuation_set_revisions"),
        sa.UniqueConstraint(
            "revision_id", "ordinal", name="uq_peer_revision_members_revision_ordinal"
        ),
        sa.UniqueConstraint(
            "revision_id", "identifier", name="uq_peer_revision_members_revision_identifier"
        ),
    )
    for table_name, parent_column in (
        ("peer_valuation_members", "peer_set_id"),
        ("peer_valuation_revision_members", "revision_id"),
    ):
        op.create_index(f"ix_{table_name}_{parent_column}", table_name, [parent_column])
        op.create_index(f"ix_{table_name}_identifier", table_name, ["identifier"])
        op.create_index(f"ix_{table_name}_peer_company_id", table_name, ["peer_company_id"])

    connection = op.get_bind()
    company_ids = set(connection.execute(sa.text("SELECT id FROM companies")).scalars())
    current_rows = [
        {"id": row["id"], "members": row["peer_identifiers_json"]}
        for row in connection.execute(
            sa.text("SELECT id, peer_identifiers_json FROM peer_valuation_sets")
        ).mappings()
    ]
    revision_rows = [
        {"id": row["id"], "members": row["members_json"]}
        for row in connection.execute(
            sa.text("SELECT id, members_json FROM peer_valuation_set_revisions")
        ).mappings()
    ]
    current_backfill = _backfill_rows(
        current_rows,
        parent_column="peer_set_id",
        company_ids=company_ids,
    )
    revision_backfill = _backfill_rows(
        revision_rows,
        parent_column="revision_id",
        company_ids=company_ids,
    )
    if current_backfill:
        op.bulk_insert(current_members, current_backfill)
    if revision_backfill:
        op.bulk_insert(revision_members, revision_backfill)


def downgrade() -> None:
    op.drop_table("peer_valuation_revision_members")
    op.drop_table("peer_valuation_members")
