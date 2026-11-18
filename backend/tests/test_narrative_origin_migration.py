import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
import sqlalchemy as sa


def test_additive_origin_migration_preserves_existing_claims_and_does_not_guess():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    metadata = sa.MetaData()
    sa.Table("ai_outputs", metadata, sa.Column("id", sa.Integer(), primary_key=True))
    claims = sa.Table("narrative_claims", metadata, sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("claim_text", sa.Text(), nullable=False))
    metadata.create_all(engine)
    path = Path(__file__).resolve().parents[1] / "alembic/versions/v4v4v4v4v4v4_narrative_claim_origin.py"
    spec = importlib.util.spec_from_file_location("origin_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.down_revision == "u3u3u3u3u3u3"
    with engine.begin() as connection:
        connection.execute(claims.insert().values(id=17, claim_text="Existing reviewed claim"))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        assert connection.execute(sa.text("SELECT id, claim_text, origin, ai_output_id FROM narrative_claims")).all() == [
            (17, "Existing reviewed claim", None, None)]
        assert any(fk["referred_table"] == "ai_outputs" for fk in sa.inspect(connection).get_foreign_keys("narrative_claims"))
    engine.dispose()
