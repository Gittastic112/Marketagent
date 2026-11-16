"""Fail closed before the legacy table-drop revision can destroy retained records."""
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from alembic.script.revision import RangeNotAncestorError
from sqlalchemy import inspect, literal, select, table
from sqlalchemy.engine import Connection


LEGACY_DROP_REVISION = "2167b87f7054"
LEGACY_DROP_TABLES = (
    "company_rd_history", "industry_rd_benchmarks", "valuation_accounting_adjustments",
    "variant_perception", "evidence_ledger", "industry_goodwill_benchmarks", "decision_logs",
)


def crosses_legacy_drop(script: ScriptDirectory, target, current) -> bool:
    try:
        return any(step.revision == LEGACY_DROP_REVISION
                   for step in script.iterate_revisions(target, current))
    except RangeNotAncestorError:
        # Not an upgrade path; Alembic still validates the requested operation.
        return False


def assert_offline_upgrade_safe(script: ScriptDirectory, target, start) -> None:
    if crosses_legacy_drop(script, target, start):
        raise RuntimeError("Legacy table-drop migration requires an online preflight; offline SQL cannot establish data preservation.")


def assert_legacy_upgrade_safe(connection: Connection, script: ScriptDirectory, target) -> None:
    current = MigrationContext.configure(connection).get_current_heads()
    if not crosses_legacy_drop(script, target, current):
        return
    existing = set(inspect(connection).get_table_names())
    affected = [name for name in LEGACY_DROP_TABLES if name in existing]
    if affected and connection.dialect.name == "postgresql":
        # Held in Alembic's migration transaction through the destructive step:
        # a concurrent writer cannot fill a table between the check and its drop.
        quoted = ", ".join(connection.dialect.identifier_preparer.quote(name) for name in affected)
        connection.exec_driver_sql(f"LOCK TABLE {quoted} IN ACCESS EXCLUSIVE MODE")
    populated = [name for name in affected if connection.execute(
        select(literal(1)).select_from(table(name)).limit(1)).first() is not None]
    if populated:
        raise RuntimeError("Legacy migration would delete retained records. A reviewed preserving conversion is required before upgrade; no migration was applied. Affected tables: " + ", ".join(populated))
