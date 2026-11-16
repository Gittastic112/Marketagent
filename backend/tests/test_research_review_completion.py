from copy import deepcopy
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.models import Company, Event, ProcessingRun, ThesisNote, ThesisAssumption, ThesisChange
from app.models.thesis_note import EventThesisImpact
from app.services.morning_briefing_engine import MorningBriefingEngine
from app.services.review_queue import build_review_queue
from app.api.dependencies import get_current_user
from app.main import app
from conftest import TEST_USER_ID


def test_brief_review_cannot_dismiss_events_or_failures_after_snapshot(client, db):
    old = MorningBriefingEngine.generate_briefing(db, TEST_USER_ID, allow_generation=False)
    cutoff = datetime.now(UTC) - timedelta(hours=2)
    old.created_at = cutoff
    old.payload_json = {**old.payload_json, "public_coverage": {**old.payload_json["public_coverage"],
        "captured_at": cutoff.isoformat(), "window_end_inclusive": cutoff.isoformat()}}
    baseline = deepcopy(old.payload_json)
    event = Event(title="Mock Data after capture", event_type="manual", information_speed="slow", created_at=cutoff + timedelta(hours=1))
    failure = ProcessingRun(run_type="rss_ingestion", source_type="rss", status="failed", error_count=1,
        started_at=cutoff + timedelta(hours=1), finished_at=cutoff + timedelta(hours=1))
    db.add_all([event, failure]); db.commit()
    assert client.patch(f"/daily-brief/{old.id}/review").status_code == 200
    new = MorningBriefingEngine.generate_briefing(db, TEST_USER_ID, allow_generation=False)
    assert event.id in new.payload_json["source_event_ids"]
    assert failure.id in {row["processing_run_id"] for row in new.payload_json["processing_failures"]}
    assert old.payload_json == baseline


def test_thesis_review_is_owned_preserves_evidence_and_keeps_blockers_pending(client, db):
    company = Company(ticker="REVIEW", name="Mock Data review")
    db.add(company); db.flush()
    note = ThesisNote(user_id=TEST_USER_ID, company_id=company.id, title="Mock Data thesis", thesis_text="Original thesis")
    event = Event(company_id=company.id, title="Mock Data evidence", event_type="manual", information_speed="slow")
    db.add_all([note, event]); db.flush()
    assumption = ThesisAssumption(thesis_note_id=note.id, description="Original assumption", current_confidence="medium")
    db.add(assumption); db.flush()
    impact = EventThesisImpact(event_id=event.id, thesis_assumption_id=assumption.id,
        impact_classification="Weakens", rationale="Original evidence interpretation")
    db.add(impact); db.commit()
    url = f"/thesis-impacts/{impact.id}/review"
    blocked = {"decision":"blocked", "reason":"Need the complete original filing", "expected_status":"unreviewed"}
    assert client.post(url, json={**blocked,"reason":"  "}).status_code == 422
    assert client.post(url, json=blocked).json()["data"]["review_status"] == "needs_review"
    assert client.post(url, json=blocked).status_code == 409
    assert any(row["record_id"] == impact.id and row["domain"] == "thesis" for row in build_review_queue(db, TEST_USER_ID)["items"])
    payload = {"decision":"no_change", "reason":"Evidence reviewed; retain the thesis with this counterevidence", "expected_status":"needs_review"}
    saved_user = app.dependency_overrides[get_current_user]
    app.dependency_overrides[get_current_user] = lambda: {"id":"other-review-owner"}
    assert client.post(url, json=payload).status_code == 404
    app.dependency_overrides[get_current_user] = saved_user
    assert client.post(url, json=payload).json()["data"]["review_status"] == "reviewed"
    assert not any(row["record_id"] == impact.id and row["domain"] == "thesis" for row in build_review_queue(db, TEST_USER_ID)["items"])
    assert impact.rationale == "Original evidence interpretation" and note.thesis_text == "Original thesis"
    assert assumption.current_confidence == "medium"
    history = list(db.scalars(select(ThesisChange).where(ThesisChange.thesis_note_id == note.id)))
    assert len(history) == 2 and all(row.drift_score == 0 for row in history)
    assert "Need the complete original filing" in history[0].change_summary
