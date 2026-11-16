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
