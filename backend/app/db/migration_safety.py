"""Preserve retained evidence and private ownership across legacy Alembic revisions."""
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from alembic.script.revision import RangeNotAncestorError
from sqlalchemy import column, func, inspect, literal, or_, select, table
from sqlalchemy.engine import Connection


LEGACY_DROP_REVISION = "2167b87f7054"
LEGACY_DROP_TABLES = (
    "company_rd_history", "industry_rd_benchmarks", "valuation_accounting_adjustments",
    "variant_perception", "evidence_ledger", "industry_goodwill_benchmarks", "decision_logs",
)


PRICING_REVISION = "8550649236ca"
PRICING_TABLE = "damodaran_industry_pricing_benchmarks"
PRICING_COLUMNS = ("pe_ratio", "ev_to_ebit", "ev_to_ebitda")
OWNERSHIP_REVISION = "a1a1a1a1a1a1"
PRIVATE_TABLES = ("portfolios", "valuation_models", "alerts", "thesis_notes", "daily_briefs",
                  "decision_logs", "research_sessions", "company_macro_inputs")
AI_OWNERSHIP_REVISION = "b8b8b8b8b8b8"
FALLBACK_OWNER = "admin_user_id_fallback"


def _crosses(script: ScriptDirectory, target, current, revision: str) -> bool:
    try:
        return any(step.revision == revision
                   for step in script.iterate_revisions(target, current))
    except RangeNotAncestorError:
        # Not an upgrade path; Alembic still validates the requested operation.
        return False


def crosses_legacy_drop(script: ScriptDirectory, target, current) -> bool:
    return _crosses(script, target, current, LEGACY_DROP_REVISION)


def fallback_owned_counts(connection: Connection) -> dict[str, int]:
    """Report only table names and counts. Reading this never changes ownership."""
    inspector = inspect(connection)
    counts = {}
    for name in (*PRIVATE_TABLES, "ai_outputs"):
        if inspector.has_table(name) and "user_id" in {c["name"] for c in inspector.get_columns(name)}:
            subject = table(name, column("user_id"))
            count = connection.scalar(select(func.count()).select_from(subject).where(subject.c.user_id == FALLBACK_OWNER))
            if count:
                counts[name] = count
    return counts


def assert_offline_upgrade_safe(script: ScriptDirectory, target, start) -> None:
    if crosses_legacy_drop(script, target, start):
        raise RuntimeError("Legacy table-drop migration requires an online preflight; offline SQL cannot establish data preservation.")

    if any(_crosses(script, target, start, rev) for rev in
           (PRICING_REVISION, OWNERSHIP_REVISION, AI_OWNERSHIP_REVISION)):
        raise RuntimeError("Legacy pricing and ownership migrations require an online preflight.")


def assert_legacy_upgrade_safe(connection: Connection, script: ScriptDirectory, target) -> None:
    current = MigrationContext.configure(connection).get_current_heads()
    drop = crosses_legacy_drop(script, target, current)
    pricing = _crosses(script, target, current, PRICING_REVISION)
    private = []
    if _crosses(script, target, current, OWNERSHIP_REVISION):
        private.extend(PRIVATE_TABLES)
    if _crosses(script, target, current, AI_OWNERSHIP_REVISION):
        private.append("ai_outputs")
    if not (drop or pricing or private):
        return
    existing = set(inspect(connection).get_table_names())
    dropped = set(LEGACY_DROP_TABLES if drop else ()) & existing
    private = sorted(set(private) & existing)
    affected = sorted(dropped | set(private) | ({PRICING_TABLE} & existing if pricing else set()))
    if affected and connection.dialect.name == "postgresql":
        # Held in Alembic's migration transaction through the destructive step:
        # a concurrent writer cannot fill a table between the check and its drop.
        quoted = ", ".join(connection.dialect.identifier_preparer.quote(name) for name in affected)
        connection.exec_driver_sql(f"LOCK TABLE {quoted} IN ACCESS EXCLUSIVE MODE")
    populated = [name for name in sorted(dropped) if connection.execute(
        select(literal(1)).select_from(table(name)).limit(1)).first() is not None]
    if populated:
        raise RuntimeError("Legacy migration would delete retained records. A reviewed preserving conversion is required before upgrade; no migration was applied. Affected tables: " + ", ".join(populated))
    if pricing and PRICING_TABLE in existing:
        legacy = table(PRICING_TABLE, *(column(name) for name in PRICING_COLUMNS))
        retained = select(literal(1)).select_from(legacy).where(or_(*(c.is_not(None) for c in legacy.c))).limit(1)
        if connection.execute(retained).first():
            raise RuntimeError("Retained pricing multiples require a reviewed preserving conversion before upgrade.")
    for name in private:
        if connection.execute(select(literal(1)).select_from(table(name)).limit(1)).first():
            raise RuntimeError(f"Legacy private ownership requires a reviewed mapping before upgrade. Affected table: {name}")


if __name__ == "__main__":
    import json
    from app.db.session import engine

    with engine.connect() as connection:
        print(json.dumps(fallback_owned_counts(connection), sort_keys=True))
