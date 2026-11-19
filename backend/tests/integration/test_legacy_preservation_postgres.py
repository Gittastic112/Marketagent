"""Opt-in preflight proof in fresh Mock Data schemas, never a restored database."""
import os
from pathlib import Path
from uuid import uuid4

from alembic.script import ScriptDirectory
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from app.db.migration_safety import LEGACY_DROP_TABLES, assert_legacy_upgrade_safe


SCRIPT = ScriptDirectory(str(Path(__file__).resolve().parents[2] / "alembic"))


@pytest.fixture
def legacy_schema():
    url = os.getenv("INGESTION_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires a disposable PostgreSQL environment")
    parsed = make_url(url)
    assert parsed.drivername.startswith("postgresql") and parsed.database.endswith("_e2e")
    engine = create_engine(url)
    schema = "legacy_test_" + uuid4().hex
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32))"))
        connection.execute(text("INSERT INTO alembic_version VALUES ('423m1d347c29')"))
        for table in LEGACY_DROP_TABLES:
            connection.execute(text(f'CREATE TABLE "{table}" (id INTEGER, evidence TEXT)'))
    try:
        yield engine, schema
    finally:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose()


@pytest.mark.parametrize("table", LEGACY_DROP_TABLES)
def test_legacy_guard_preserves_populated_postgres_table(legacy_schema, table):
    engine, schema = legacy_schema
    with engine.begin() as connection:
        connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
        connection.execute(text(f'INSERT INTO "{table}" VALUES (1, \'Mock Data retained evidence\')'))
        with pytest.raises(RuntimeError, match="preserving conversion"):
            assert_legacy_upgrade_safe(connection, SCRIPT, "head")
        assert connection.execute(text(f'SELECT evidence FROM "{table}"')).scalar_one() == "Mock Data retained evidence"
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "423m1d347c29"


def test_empty_preflight_blocks_writes_until_migration_transaction_ends(legacy_schema):
    engine, schema = legacy_schema
    with engine.begin() as connection:
        connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
        assert_legacy_upgrade_safe(connection, SCRIPT, "head")
        with engine.connect() as writer:
            writer.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            writer.execute(text("SET LOCAL lock_timeout TO '150ms'"))
            with pytest.raises(DBAPIError) as error:
                writer.execute(text("INSERT INTO company_rd_history VALUES (2, 'Mock Data concurrent writer')"))
            assert error.value.orig.sqlstate == "55P03"

@pytest.fixture
def predecessor(monkeypatch):
    from types import SimpleNamespace
    from alembic import command
    from alembic.config import Config
    import app.core.config as settings

    url = os.getenv("INGESTION_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires a disposable PostgreSQL environment")
    parsed = make_url(url)
    assert parsed.drivername.startswith("postgresql") and parsed.database.endswith("_e2e")
    schema = "predecessor_" + uuid4().hex
    base = create_engine(parsed)
    with base.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    isolated = parsed.update_query_dict({"options": "-csearch_path=" + schema})
    monkeypatch.setattr(settings, "get_settings", lambda: SimpleNamespace(database_url=isolated.render_as_string(hide_password=False)))
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[2] / "alembic"))
    engine = create_engine(isolated)
    try:
        yield engine, lambda target: command.upgrade(config, target)
    finally:
        engine.dispose()
        with base.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        base.dispose()


@pytest.mark.parametrize("values", [(19.25, 14.5, 9.75), (19.25, None, None), (None, 14.5, None), (None, None, 9.75)])
def test_real_pricing_predecessor_preserves_each_multiple(predecessor, values):
    engine, upgrade = predecessor
    upgrade("76dd1d347c33")
    with engine.begin() as conn:
        conn.exec_driver_sql("INSERT INTO damodaran_dataset_files (id, uploaded_filename, dataset_code, source_file_type) VALUES (1, 'mock', 'pricing', 'xlsx')")
        conn.exec_driver_sql("INSERT INTO damodaran_industry_pricing_benchmarks (dataset_file_id, industry_name, pe_ratio, ev_to_ebit, ev_to_ebitda) VALUES (1, 'Mock Data', %s,%s,%s)", values)
    with pytest.raises(RuntimeError, match="Retained pricing multiples"):
        upgrade("8550649236ca")
    with engine.connect() as conn:
        assert tuple(conn.exec_driver_sql("SELECT pe_ratio, ev_to_ebit, ev_to_ebitda FROM damodaran_industry_pricing_benchmarks").one()) == values
        assert conn.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one() == "76dd1d347c33"


def test_private_data_requires_mapping_and_empty_pricing_lock_blocks_writers(predecessor):
    from sqlalchemy import inspect
    from app.db.migration_safety import assert_offline_upgrade_safe, fallback_owned_counts
    engine, upgrade = predecessor
    upgrade("76dd1d347c33")
    with pytest.raises(RuntimeError, match="online preflight"):
        assert_offline_upgrade_safe(SCRIPT, "8550649236ca", "76dd1d347c33")
    with engine.begin() as checking, engine.begin() as writer:
        assert_legacy_upgrade_safe(checking, SCRIPT, "8550649236ca")
        writer.exec_driver_sql("SET LOCAL lock_timeout = '150ms'")
        with pytest.raises(DBAPIError) as failure:
            writer.exec_driver_sql("UPDATE damodaran_industry_pricing_benchmarks SET pe_ratio = 1")
        assert failure.value.orig.sqlstate == "55P03"
    upgrade("8550649236ca")
    with engine.begin() as conn:
        conn.exec_driver_sql("INSERT INTO portfolios (id, name, base_currency) VALUES (1, 'Mock Data', 'USD')")
    with pytest.raises(RuntimeError, match="private ownership"):
        upgrade("head")
    with engine.begin() as conn:
        assert "user_id" not in {c["name"] for c in inspect(conn).get_columns("portfolios")}
        assert conn.exec_driver_sql("SELECT id, name FROM portfolios").one() == (1, "Mock Data")
        assert conn.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one() == "8550649236ca"
        conn.exec_driver_sql("DELETE FROM portfolios WHERE id = 1")
    upgrade("head")
    with engine.begin() as conn:
        assert fallback_owned_counts(conn) == {}
        conn.exec_driver_sql("INSERT INTO portfolios (name, base_currency, user_id) VALUES ('Mock Data', 'USD', 'admin_user_id_fallback')")
        assert fallback_owned_counts(conn) == {"portfolios": 1}
