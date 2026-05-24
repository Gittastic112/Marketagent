from pathlib import Path


def test_initial_alembic_migration_contains_mvp_tables() -> None:
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    migration_text = "\n".join(path.read_text(encoding="utf-8") for path in versions_dir.glob("*.py"))

    for table_name in ["companies", "sources", "raw_documents", "events", "alerts", "thesis_notes"]:
        assert f'create_table("{table_name}"' in migration_text
