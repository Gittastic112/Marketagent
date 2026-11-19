"""Mock Data preflight checks. Never run a destructive historical migration."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
import pytest
from sqlalchemy import create_engine, text

from app.db.migration_safety import assert_legacy_upgrade_safe, assert_offline_upgrade_safe, crosses_legacy_drop
from app.core.config import get_settings


SCRIPT = ScriptDirectory(str(Path(__file__).resolve().parents[1] / "alembic"))


@pytest.mark.parametrize("table", ["company_rd_history", "industry_rd_benchmarks",
    "valuation_accounting_adjustments", "variant_perception", "evidence_ledger",
    "industry_goodwill_benchmarks", "decision_logs"])
def test_populated_predecessor_is_rejected_without_changes(table):
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32))"))
        connection.execute(text("INSERT INTO alembic_version VALUES ('423m1d347c29')"))
        connection.execute(text(f'CREATE TABLE "{table}" (id INTEGER, evidence TEXT)'))
        connection.execute(text(f'INSERT INTO "{table}" VALUES (1, \'Mock Data retained evidence\')'))
        with pytest.raises(RuntimeError, match="preserving conversion"):
            assert_legacy_upgrade_safe(connection, SCRIPT, "head")
        assert connection.execute(text(f'SELECT evidence FROM "{table}"')).scalar_one() == "Mock Data retained evidence"
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "423m1d347c29"
    engine.dispose()


def test_fresh_empty_and_already_migrated_databases_are_allowed():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        assert_legacy_upgrade_safe(connection, SCRIPT, "head")
        connection.execute(text("CREATE TABLE evidence_ledger (id INTEGER)"))
        assert_legacy_upgrade_safe(connection, SCRIPT, "head")
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32))"))
        connection.execute(text("INSERT INTO alembic_version VALUES (:head)"), {"head": SCRIPT.get_current_head()})
        connection.execute(text("INSERT INTO evidence_ledger VALUES (42)"))
        assert_legacy_upgrade_safe(connection, SCRIPT, "head")
        assert connection.execute(text("SELECT id FROM evidence_ledger")).scalar_one() == 42
    engine.dispose()


def test_partial_target_before_drop_is_allowed_and_offline_crossing_is_rejected():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE evidence_ledger (id INTEGER)"))
        connection.execute(text("INSERT INTO evidence_ledger VALUES (42)"))
        assert_legacy_upgrade_safe(connection, SCRIPT, "423m1d347c29")
    with pytest.raises(RuntimeError, match="online preflight"):
        assert_offline_upgrade_safe(SCRIPT, "head", None)
    assert_offline_upgrade_safe(SCRIPT, "423m1d347c29", None)
    with pytest.raises(RuntimeError, match="online preflight"):
        assert_offline_upgrade_safe(SCRIPT, "head", "2167b87f7054")
    assert_offline_upgrade_safe(SCRIPT, "head", "b8b8b8b8b8b8")


def test_preflight_does_not_misclassify_downgrade_or_relative_upgrade():
    assert crosses_legacy_drop(SCRIPT, "423m1d347c29", (SCRIPT.get_current_head(),)) is False
    assert crosses_legacy_drop(SCRIPT, "+1", ("423m1d347c29",)) is True


@pytest.mark.parametrize("revision", [None, "423m1d347c29", SCRIPT.get_current_head()])
def test_current_command_remains_read_only_without_a_migration_target(tmp_path, monkeypatch, revision):
    url = f"sqlite:///{tmp_path / 'inspection.sqlite'}"
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE evidence_ledger (id INTEGER, evidence TEXT)"))
        connection.execute(text("INSERT INTO evidence_ledger VALUES (1, 'Mock Data retained evidence')"))
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32))"))
        if revision:
            connection.execute(text("INSERT INTO alembic_version VALUES (:revision)"), {"revision": revision})
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    config.set_main_option("script_location", str(SCRIPT.dir))
    command.current(config)
    if revision == "423m1d347c29":
        with pytest.raises(RuntimeError, match="preserving conversion"):
            command.upgrade(config, "head")
    with engine.connect() as connection:
        assert connection.execute(text("SELECT evidence FROM evidence_ledger")).scalar_one() == "Mock Data retained evidence"
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none() == revision
    engine.dispose()
