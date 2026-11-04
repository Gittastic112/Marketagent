from copy import deepcopy
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select

from app.models import DailyBrief, Event, ProcessingRun
from app.schemas.brief import DailyBriefPayload
from app.services.brief_public_coverage import selection_counts
from app.services.morning_briefing_engine import MorningBriefingEngine


OWNER = "admin_user_id_fallback"


def test_saved_brief_counts_eligible_inputs_and_all_three_caps(db_session, monkeypatch):
    now = datetime.now(UTC)
    reviewed_at = now - timedelta(hours=2)
    previous = DailyBrief(user_id=OWNER, brief_date=date.today() - timedelta(days=1),
        title="Previous", summary="Previous", payload_json={}, review_status="reviewed",
        reviewed_at=reviewed_at)
    db_session.add(previous)
    for index in range(55):
        db_session.add(Event(event_type="manual", information_speed="slow", title=f"Event {index}",
            priority_score=90, created_at=now - timedelta(minutes=30, seconds=index)))
    for timestamp in (reviewed_at, now + timedelta(days=1)):
        db_session.add(Event(event_type="manual", information_speed="slow", title="Outside window",
            priority_score=100, created_at=timestamp))
    for index in range(13):
        db_session.add(ProcessingRun(run_type="recorded_test", status="partial" if index % 2 else "failed",
            error_count=1, started_at=now - timedelta(minutes=20, seconds=index)))
    db_session.add(ProcessingRun(run_type="outside_window", status="failed", error_count=1,
        started_at=reviewed_at))
    db_session.add(ProcessingRun(run_type="future", status="failed", error_count=1,
        started_at=now + timedelta(days=1)))
    db_session.commit()

    def forbidden(**_kwargs):
        raise AssertionError("Coverage must not invoke AI")
    monkeypatch.setattr("app.services.morning_briefing_engine.map_event_to_dcf_variables", forbidden)
    monkeypatch.setattr("app.services.morning_briefing_engine.detect_thesis_contradiction", forbidden)
    brief = MorningBriefingEngine.generate_briefing(db_session, OWNER, allow_generation=False)
    coverage = brief.payload_json["public_coverage"]
    assert coverage["status"] == "partial"
    assert coverage["selection_basis"] == "since_last_review"
    assert coverage["events"] == {"eligible_count": 55, "included_count": 50, "excluded_count": 5,
        "cap": 50, "status": "partial", "exclusion_reasons": {"event_cap": 5}}
    assert coverage["failed_runs"]["eligible_count"] == 13
    assert coverage["failed_runs"]["included_count"] == 10
    assert coverage["failed_runs"]["excluded_count"] == 3
    assert coverage["failed_runs"]["exclusion_reasons"] == {"failed_run_cap": 3}
    assert coverage["inspection_actions"]["eligible_count"] == 60
    assert coverage["inspection_actions"]["included_count"] == 20
    assert coverage["inspection_actions"]["excluded_count"] == 40
    assert coverage["inspection_actions"]["exclusion_reasons"] == {"inspection_action_cap": 40}
    assert coverage["provider_coverage"] == "not_assessed"
    assert coverage["source_verification"] == "not_assessed"
    assert coverage["window_start_exclusive"].startswith(reviewed_at.isoformat()[:19])
    assert len(brief.payload_json["source_event_ids"]) == 50
    assert len(brief.payload_json["processing_failures"]) == 10
    assert len(brief.payload_json["inspection_queue"]) == 20
    assert brief.payload_json["calculation_status"] == "partial"
    assert DailyBriefPayload.model_validate(brief.payload_json).public_coverage is not None


def test_zero_measured_coverage_differs_from_unknown_caller_coverage(db_session):
    brief = MorningBriefingEngine.generate_briefing(db_session, OWNER, allow_generation=False)
    coverage = brief.payload_json["public_coverage"]
    assert coverage["status"] == "complete"
    assert coverage["events"]["eligible_count"] == coverage["events"]["excluded_count"] == 0
    assert coverage["failed_runs"]["eligible_count"] == 0
    assert coverage["provider_coverage"] == "not_assessed"
    payload = MorningBriefingEngine.build_briefing_payload(db_session, OWNER, [], [], allow_generation=False)
    unknown = payload["public_coverage"]
    assert unknown["status"] == "unknown"
    assert unknown["events"]["eligible_count"] is None
    assert unknown["events"]["excluded_count"] is None
    assert unknown["events"]["included_count"] == 0
    assert unknown["window_end_inclusive"] is None
    assert selection_counts(None, 2, None, "not_counted")["status"] == "unknown"
    # A concurrent change must not create negative or falsely complete accounting.
    assert selection_counts(1, 2, 10, "cap")["eligible_count"] is None


def test_saved_coverage_is_as_generated_and_brief_date_is_not_a_backtest(db_session):
    now = datetime.now(UTC)
    event = Event(event_type="manual", information_speed="slow", title="Currently stored event",
        priority_score=10, created_at=now - timedelta(minutes=1))
    db_session.add(event)
    db_session.commit()
    brief = MorningBriefingEngine.generate_briefing(db_session, OWNER, date(2020, 1, 1), allow_generation=False)
    assert brief.payload_json["source_event_ids"] == [event.id]
    snapshot = deepcopy(brief.payload_json)
    coverage = snapshot["public_coverage"]
    assert coverage["window_end_inclusive"].startswith(now.date().isoformat())
    db_session.add(Event(event_type="manual", information_speed="slow", title="Later stored event", priority_score=95))
    db_session.commit()
    before_count = len(list(db_session.scalars(select(DailyBrief))))
    reread = MorningBriefingEngine.get_or_generate_briefing(db_session, OWNER, date(2020, 1, 1))
    assert reread.payload_json == snapshot
    assert len(list(db_session.scalars(select(DailyBrief)))) == before_count
    assert not db_session.new and not db_session.dirty and not db_session.deleted


def test_legacy_payload_does_not_invent_coverage_or_rewrite_input():
    original = {"summary": "Historical saved output", "calculation_status": "complete"}
    before = deepcopy(original)
    assert DailyBriefPayload.model_validate(original).public_coverage is None
    assert original == before
