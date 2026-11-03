from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session


EXPECTED_MIGRATION_HEAD = "t2t2t2t2t2t2"
REQUIRED_SCHEMA: dict[str, set[str]] = {
    "brief_comparison_reviews": {"id", "user_id", "company_id", "field", "include_mock", "version", "evidence_hash", "evidence_json"},
    "users": {"id"},
    "evaluation_runs": {"id", "user_id", "report_json"},
    "processing_runs": {"id", "status", "metadata_json"},
    "daily_briefs": {"id", "user_id", "brief_date", "reviewed_at"},
    "brief_sources": {"id", "user_id", "company_id", "identity_hash", "content_text", "pdf_bytes", "analysis_status", "ai_output_id", "archived_at", "lifecycle_version"},
    "daily_brief_schedules": {
        "id",
        "user_id",
        "enabled",
        "timezone",
        "local_time",
        "days_of_week",
        "next_run_at",
        "lease_expires_at",
        "last_processing_run_id",
        "last_brief_id",
    },
    "macro_series": {"id", "provider_name", "source_url"},
    "market_regime_inputs": {
        "id",
        "source_record_type",
        "source_record_id",
    },
    "market_prices": {"id", "source_url", "claim_type", "import_run_id"},
    "fx_rate_observations": {"id", "claim_type", "import_run_id"},
    "dcf_assumption_sets": {
        "id",
        "cash_flow_currency",
        "discount_rate_currency",
        "currency_override_note",
    },
    "assumption_method_values": {"id", "dataset_file_id"},
    "damodaran_industry_fundamental_growth": {
        "id",
        "expected_revenue_growth_2y",
        "expected_revenue_growth_5y",
        "historical_net_income_growth",
    },
    "damodaran_industry_financing_flows": {
        "id",
        "number_of_firms",
        "dividends_usd_millions",
        "buybacks_usd_millions",
        "equity_issuance_usd_millions",
        "debt_raised_usd_millions",
        "debt_repaid_usd_millions",
    },
    "peer_valuation_sets": {
        "id",
        "user_id",
        "company_id",
        "peer_identifiers_json",
        "aggregate_metrics_json",
        "aggregation_method",
        "review_status",
        "reviewed_at",
        "reviewed_by_user_id",
        "version",
        "target_context_json",
        "import_sha256",
        "review_diagnostics_sha256",
        "review_warning_codes_json",
        "review_diagnostics_as_of",
    },
    "peer_valuation_set_revisions": {
        "id",
        "peer_set_id",
        "user_id",
        "version",
        "action",
        "changed_fields_json",
        "members_json",
        "aggregate_metrics_json",
        "target_context_json",
        "review_diagnostics_sha256",
        "review_warning_codes_json",
        "review_diagnostics_as_of",
    },
    "peer_valuation_members": {
        "id",
        "peer_set_id",
        "ordinal",
        "identifier",
        "source_url",
        "source_as_of",
        "currency",
        "fiscal_period_end",
        "market_cap",
        "updated_at",
    },
    "peer_valuation_revision_members": {
        "id",
        "revision_id",
        "ordinal",
        "identifier",
        "source_url",
        "source_as_of",
        "currency",
        "fiscal_period_end",
        "market_cap",
    },
    "peer_valuation_target_profiles": {
        "id",
        "peer_set_id",
        "source_url",
        "source_as_of",
        "currency",
        "fiscal_period_end",
        "market_cap",
        "updated_at",
    },
    "peer_valuation_revision_target_profiles": {
        "id",
        "revision_id",
        "source_url",
        "source_as_of",
        "currency",
        "fiscal_period_end",
        "market_cap",
    },
}
REQUIRED_UNIQUE_CONSTRAINTS: dict[str, set[str]] = {
    "brief_comparison_reviews": {"uq_brief_review_scope_version"},
    "brief_sources": {"uq_brief_source_owner_content"},
    "peer_valuation_sets": {
        "uq_peer_valuation_sets_owner_company_import_sha256",
    },
}


def _blocked_report(*, database_ready: bool) -> dict:
    return {
        "status": "blocked",
        "database_status": "ready" if database_ready else "unavailable",
        "schema_status": "blocked" if database_ready else "unknown",
        "expected_migration_head": EXPECTED_MIGRATION_HEAD,
        "current_migration_heads": [],
        "missing_tables": [],
        "missing_columns": [],
        "missing_constraints": [],
        "recovery_steps": (
            [
                "docker compose ps",
                "docker compose logs postgres backend --tail=100",
            ]
            if not database_ready
            else ["docker compose exec backend alembic upgrade head"]
        ),
    }


def check_runtime_readiness(db: Session) -> dict:
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db.rollback()
        return _blocked_report(database_ready=False)

    report = _blocked_report(database_ready=True)
    try:
        inspector = inspect(db.get_bind())
        table_names = set(inspector.get_table_names())
        missing_tables = sorted(set(REQUIRED_SCHEMA) - table_names)
        missing_columns: list[str] = []
        missing_constraints: list[str] = []
        for table_name, required_columns in REQUIRED_SCHEMA.items():
            if table_name not in table_names:
                continue
            present_columns = {
                column["name"] for column in inspector.get_columns(table_name)
            }
            missing_columns.extend(
                f"{table_name}.{column_name}"
                for column_name in sorted(required_columns - present_columns)
            )
        for table_name, required_constraints in REQUIRED_UNIQUE_CONSTRAINTS.items():
            if table_name not in table_names:
                continue
            present_constraints = {
                constraint["name"]
                for constraint in inspector.get_unique_constraints(table_name)
                if constraint.get("name")
            }
            missing_constraints.extend(
                f"{table_name}.{constraint_name}"
                for constraint_name in sorted(required_constraints - present_constraints)
            )

        current_heads = (
            sorted(db.execute(text("SELECT version_num FROM alembic_version")).scalars())
            if "alembic_version" in table_names
            else []
        )
    except Exception:
        db.rollback()
        return report

    schema_ready = (
        current_heads == [EXPECTED_MIGRATION_HEAD]
        and not missing_tables
        and not missing_columns
        and not missing_constraints
    )
    return {
        **report,
        "status": "ready" if schema_ready else "blocked",
        "schema_status": "ready" if schema_ready else "blocked",
        "current_migration_heads": current_heads,
        "missing_tables": missing_tables,
        "missing_columns": missing_columns,
        "missing_constraints": missing_constraints,
        "recovery_steps": [] if schema_ready else report["recovery_steps"],
    }
