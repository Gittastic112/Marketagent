from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.services.runtime_readiness import (
    EXPECTED_MIGRATION_HEAD,
    check_runtime_readiness,
)


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
