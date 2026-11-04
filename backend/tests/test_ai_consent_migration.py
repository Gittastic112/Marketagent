"""The additive consent migration must preserve old outputs and create no grants."""

import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
import sqlalchemy as sa


def test_consent_migration_preserves_history_without_auto_grants():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    metadata = sa.MetaData()
    users = sa.Table("users", metadata, sa.Column("id", sa.String(), primary_key=True))
    outputs = sa.Table("ai_outputs", metadata,
                       sa.Column("id", sa.Integer(), primary_key=True),
                       sa.Column("output_text", sa.Text(), nullable=False))
    metadata.create_all(engine)
    path = Path(__file__).resolve().parents[1] / "alembic/versions/u3u3u3u3u3u3_add_scoped_ai_consent.py"
    spec = importlib.util.spec_from_file_location("consent_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.down_revision == "t2t2t2t2t2t2"
    with engine.begin() as connection:
        connection.execute(users.insert().values(id="existing-owner"))
        connection.execute(outputs.insert().values(id=17, output_text="Existing reviewed output"))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        assert connection.execute(sa.text("SELECT id, output_text, consent_decision_id FROM ai_outputs")).all() == [
            (17, "Existing reviewed output", None)
        ]
        assert connection.execute(sa.text("SELECT COUNT(*) FROM ai_consent_decisions")).scalar_one() == 0
        inspector = sa.inspect(connection)
        assert any(fk["referred_table"] == "ai_consent_decisions"
                   for fk in inspector.get_foreign_keys("ai_outputs"))
        assert any(item["name"] == "uq_ai_consent_scope_revision"
                   for item in inspector.get_unique_constraints("ai_consent_decisions"))
    engine.dispose()
