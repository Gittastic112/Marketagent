from datetime import UTC, datetime, timedelta

from app.models import ProcessingRun
from app.services.brief_public_coverage import count_public_inputs
from app.services.morning_briefing_engine import MorningBriefingEngine


def test_private_attempts_do_not_enter_public_counts_briefs_or_dashboard(client, db_session):
    now = datetime.now(UTC)
    public = ProcessingRun(run_type="sec_ingestion", source_type="sec", status="failed", error_count=1, started_at=now - timedelta(minutes=1))
    private = [ProcessingRun(run_type="brief_source_import", source_type="private_upload", status="failed",
        error_count=1, started_at=now - timedelta(minutes=1), metadata_json=metadata) for metadata in
        ({"user_id": "other"}, {"user_id": "admin_user_id_fallback"}, None)]
    legacy_child = ProcessingRun(run_type="sec_ingestion", source_type="sec", status="failed",
        error_count=1, started_at=now - timedelta(minutes=1), metadata_json={"parent_run_id": 99})
    db_session.add_all([public, *private, legacy_child])
    db_session.commit()
    assert count_public_inputs(db_session, None, now) == (0, 1)
    brief = MorningBriefingEngine.generate_briefing(db_session, "admin_user_id_fallback", allow_generation=False)
    assert brief.payload_json["public_coverage"]["failed_runs"]["eligible_count"] == 1
    overview = client.get("/dashboard/overview")
    assert overview.status_code == 200
    assert {row["id"] for row in overview.json()["data"]["processing_runs"]} == {public.id}
    runs = client.get("/processing-runs")
    assert runs.status_code == 200
    assert {row["id"] for row in runs.json()["data"]} == {public.id, private[1].id}


def test_owned_metadata_always_scopes_even_an_ordinary_ingestion_type(client, db_session):
    now = datetime.now(UTC)
    for owner in ("admin_user_id_fallback", "other"):
        db_session.add(ProcessingRun(run_type="sec_ingestion", source_type="sec", status="failed",
            error_count=1, started_at=now, metadata_json={"user_id": owner}))
    db_session.commit()
    rows = client.get("/processing-runs").json()["data"]
    assert len(rows) == 1
    assert rows[0]["metadata_json"]["user_id"] == "admin_user_id_fallback"
    assert count_public_inputs(db_session, None, now) == (0, 0)
