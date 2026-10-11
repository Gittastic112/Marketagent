from pathlib import Path

from app.services.runtime_readiness import EXPECTED_MIGRATION_HEAD


def test_alembic_migrations_contain_core_tables_and_company_fields() -> None:
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    migration_text = "\n".join(path.read_text(encoding="utf-8") for path in versions_dir.glob("*.py"))

    for table_name in [
        "companies",
        "sources",
        "raw_documents",
        "events",
        "alerts",
        "thesis_notes",
        "daily_briefs",
        "document_assets",
        "processing_runs",
        "portfolios",
        "portfolio_holdings",
        "portfolio_transactions",
        "portfolio_cash_balances",
        "portfolio_snapshots",
    ]:
        assert "create_table" in migration_text
        assert f'"{table_name}"' in migration_text or f"'{table_name}'" in migration_text

    for company_field in [
        "country",
        "region",
        "currency",
        "asset_type",
        "security_type",
        "market_cap_category",
        "is_etf",
        "etf_provider",
    ]:
        assert f'"{company_field}"' in migration_text or f"'{company_field}'" in migration_text

    for dataset_version_field in [
        "source_sha256",
        "source_byte_size",
        "source_as_of",
        "date_confidence",
        "canonical_source_path",
        "import_kind",
        "is_active",
        "superseded_at",
        "row_count",
        "rd_adjusted_roe",
        "number_of_firms",
        "fcfe_before_debt",
        "fcfe_after_debt",
    ]:
        assert (
            f'"{dataset_version_field}"' in migration_text
            or f"'{dataset_version_field}'" in migration_text
        )

    volatility_migration = (
        versions_dir / "m9m9m9m9m9m9_add_volatility_dataset_version.py"
    )
    assert volatility_migration.is_file()
    volatility_text = volatility_migration.read_text(encoding="utf-8")
    assert 'down_revision = "l8l8l8l8l8l8"' in volatility_text
    assert '"industry_volatility_benchmarks"' in volatility_text
    assert '"dataset_file_id"' in volatility_text
    assert '"damodaran_dataset_files"' in volatility_text
    assert '["id"]' in volatility_text

    current_head = versions_dir / "o6o6o6o6o6o6_add_peer_review_diagnostic_receipts.py"
    assert current_head.is_file()
    current_head_text = current_head.read_text(encoding="utf-8")
    assert 'revision: str = "o6o6o6o6o6o6"' in current_head_text
    assert 'down_revision: str | None = "n5n5n5n5n5n5"' in current_head_text
    assert '"review_diagnostics_sha256"' in current_head_text
    assert '"review_warning_codes_json"' in current_head_text
    assert '"review_diagnostics_as_of"' in current_head_text
    assert '"peer_valuation_set_revisions"' in current_head_text
    evaluation_head = (versions_dir / "p7p7p7p7p7p7_add_owned_evaluation_reports.py").read_text()
    assert 'revision: str = "p7p7p7p7p7p7"' in evaluation_head
    assert 'down_revision: str | None = "o6o6o6o6o6o6"' in evaluation_head
    assert '"report_json"' in evaluation_head
    assert '"user_id"' in evaluation_head
    source_head = (versions_dir / "q8q8q8q8q8q8_add_private_brief_sources.py").read_text()
    assert 'revision = "q8q8q8q8q8q8"' in source_head
    assert 'down_revision = "p7p7p7p7p7p7"' in source_head
    assert '"uq_brief_source_owner_content"' in source_head
    assert '"pdf_bytes"' in source_head
    lifecycle_head = (versions_dir / "r9r9r9r9r9r9_add_brief_source_lifecycle.py").read_text()
    assert 'revision = "r9r9r9r9r9r9"' in lifecycle_head
    assert 'down_revision = "q8q8q8q8q8q8"' in lifecycle_head
    assert '"archived_at"' in lifecycle_head and '"lifecycle_version"' in lifecycle_head
    review_head = (versions_dir / "s1s1s1s1s1s1_add_brief_comparison_reviews.py").read_text()
    assert f'revision = "{EXPECTED_MIGRATION_HEAD}"' in review_head
    assert 'down_revision = "r9r9r9r9r9r9"' in review_head
    assert '"brief_comparison_reviews"' in review_head
    assert '"uq_brief_review_scope_version"' in review_head
