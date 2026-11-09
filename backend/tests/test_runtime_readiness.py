import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from app.services.runtime_readiness import (
    EXPECTED_MIGRATION_HEAD,
    check_runtime_readiness,
)
import app.services.runtime_readiness as readiness_service


def stamp_current_head(db: Session) -> None:
    db.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
    db.execute(
        text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
        {"revision": EXPECTED_MIGRATION_HEAD},
    )
    db.commit()


def test_runtime_readiness_accepts_current_schema(db_session: Session) -> None:
    stamp_current_head(db_session)

    report = check_runtime_readiness(db_session)

    assert report["status"] == "ready"
    assert report["database_status"] == "ready"
    assert report["schema_status"] == "ready"
    assert report["expected_migration_head"] == EXPECTED_MIGRATION_HEAD
    assert report["current_migration_heads"] == [EXPECTED_MIGRATION_HEAD]
    assert report["missing_tables"] == []
    assert report["missing_columns"] == []
    assert report["missing_constraints"] == []
    assert report["recovery_steps"] == []


@pytest.mark.parametrize("missing", [None, "column", "constraint"])
def test_readiness_batches_metadata_without_hiding_gaps(db_session: Session, monkeypatch, missing) -> None:
    stamp_current_head(db_session)
    actual = inspect(db_session.get_bind())
    calls = []

    class BatchedInspector:
        def get_table_names(self):
            return actual.get_table_names()

        def get_multi_columns(self, *, filter_names):
            calls.append("columns")
            assert set(filter_names) == set(readiness_service.REQUIRED_SCHEMA)
            result = actual.get_multi_columns(filter_names=filter_names)
            if missing == "column":
                key = (None, "daily_briefs")
                result[key] = [row for row in result[key] if row["name"] != "user_id"]
            return result

        def get_multi_unique_constraints(self, *, filter_names):
            calls.append("constraints")
            assert set(filter_names) == set(readiness_service.REQUIRED_UNIQUE_CONSTRAINTS)
            result = actual.get_multi_unique_constraints(filter_names=filter_names)
            if missing == "constraint":
                result[(None, "ai_consent_decisions")] = []
            return result

    monkeypatch.setattr(readiness_service, "inspect", lambda bind: BatchedInspector())
    report = check_runtime_readiness(db_session)
    assert calls == ["columns", "constraints"]
    assert report["status"] == ("ready" if missing is None else "blocked")
    assert report["missing_columns"] == (["daily_briefs.user_id"] if missing == "column" else [])
    assert report["missing_constraints"] == (["ai_consent_decisions.uq_ai_consent_scope_revision"] if missing == "constraint" else [])


def test_runtime_readiness_reports_migration_and_schema_gaps_without_exception_text() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with Session(engine) as db:
        db.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        db.execute(text("INSERT INTO alembic_version (version_num) VALUES ('old-head')"))
        db.execute(text("CREATE TABLE daily_briefs (id INTEGER PRIMARY KEY)"))
        db.commit()

        report = check_runtime_readiness(db)

    assert report["status"] == "blocked"
    assert report["database_status"] == "ready"
    assert report["schema_status"] == "blocked"
    assert report["current_migration_heads"] == ["old-head"]
    assert "daily_brief_schedules" in report["missing_tables"]
    assert "ai_consent_decisions" in report["missing_tables"]
    assert "ai_outputs" in report["missing_tables"]
    assert "daily_briefs.reviewed_at" in report["missing_columns"]
    assert (
        "peer_valuation_sets.uq_peer_valuation_sets_owner_company_import_sha256"
        not in report["missing_constraints"]
    )
    assert report["recovery_steps"] == ["docker compose exec backend alembic upgrade head"]
    assert "OperationalError" not in str(report)


def test_readiness_endpoint_is_public_and_health_gates_schema(client, db_session: Session) -> None:
    blocked = client.get("/api/readiness")

    assert blocked.status_code == 503
    assert blocked.json()["data"]["status"] == "blocked"
    assert blocked.json()["errors"][0]["code"] == "SCHEMA_NOT_READY"

    stamp_current_head(db_session)
    ready = client.get("/api/readiness")

    assert ready.status_code == 200
    assert ready.json()["data"]["status"] == "ready"
    assert ready.json()["errors"] == []
