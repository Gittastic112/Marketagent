from pathlib import Path


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
