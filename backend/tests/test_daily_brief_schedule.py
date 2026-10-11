from datetime import UTC, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DailyBrief, DailyBriefSchedule, ProcessingRun
from app.services.daily_brief_schedule import (
    compute_next_scheduled_run,
    configure_daily_brief_schedule,
    run_due_daily_brief_schedules,
)
from app.workers.daily_brief_scheduler import scheduler_interval_seconds


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def test_next_scheduled_run_converts_local_time_to_utc() -> None:
    after = datetime(2026, 8, 23, 0, 0, tzinfo=UTC)

    next_run = compute_next_scheduled_run(
        timezone_name="Asia/Kolkata",
        local_time=time(7, 0),
        days_of_week=[0, 1, 2, 3, 4, 5, 6],
        after_utc=after,
    )

    assert next_run == datetime(2026, 8, 23, 1, 30, tzinfo=UTC)


def test_next_scheduled_run_skips_disabled_weekdays() -> None:
    friday_after_close = datetime(2026, 8, 21, 20, 0, tzinfo=UTC)

    next_run = compute_next_scheduled_run(
        timezone_name="UTC",
        local_time=time(7, 0),
        days_of_week=[0, 1, 2, 3, 4],
        after_utc=friday_after_close,
    )

    assert next_run == datetime(2026, 8, 24, 7, 0, tzinfo=UTC)


def test_configure_schedule_recomputes_next_run_and_can_disable(db_session: Session) -> None:
    now = datetime(2026, 8, 23, 0, 0, tzinfo=UTC)
    schedule = configure_daily_brief_schedule(
        db_session,
        user_id="admin_user_id_fallback",
        enabled=True,
        timezone_name="UTC",
        local_time=time(7, 0),
        days_of_week=[0, 1, 2, 3, 4, 5, 6],
        now=now,
    )

    assert schedule.next_run_at is not None
    assert as_utc(schedule.next_run_at) == datetime(2026, 8, 23, 7, 0, tzinfo=UTC)
    disabled = configure_daily_brief_schedule(
        db_session,
        user_id="admin_user_id_fallback",
        enabled=False,
        timezone_name="UTC",
        local_time=time(7, 0),
        days_of_week=[0, 1, 2, 3, 4, 5, 6],
        now=now,
    )
    assert disabled.id == schedule.id
    assert disabled.next_run_at is None
    assert disabled.last_status == "disabled"


def test_due_runner_is_deterministic_and_idempotent(db_session: Session) -> None:
    now = datetime(2026, 8, 23, 8, 0, tzinfo=UTC)
    schedule = configure_daily_brief_schedule(
        db_session,
        user_id="admin_user_id_fallback",
        enabled=True,
        timezone_name="UTC",
        local_time=time(7, 0),
        days_of_week=[0, 1, 2, 3, 4, 5, 6],
        now=now - timedelta(days=1),
    )
    schedule.next_run_at = now - timedelta(minutes=1)
    db_session.commit()

    first = run_due_daily_brief_schedules(db_session, user_id=schedule.user_id, now=now)
    second = run_due_daily_brief_schedules(db_session, user_id=schedule.user_id, now=now)

    assert first["briefs_created"] == 1
    assert second["briefs_created"] == 0
    assert db_session.scalar(select(DailyBrief).where(DailyBrief.user_id == schedule.user_id)) is not None
    persisted = db_session.get(DailyBriefSchedule, schedule.id)
    assert persisted is not None
    assert persisted.last_status == "success"
    assert persisted.next_run_at is not None and as_utc(persisted.next_run_at) > now
    run = db_session.scalar(
        select(ProcessingRun).where(ProcessingRun.run_type == "daily_brief_schedule")
    )
    assert run is not None
    assert run.status == "success"
    assert run.metadata_json["generation_mode"] == "deterministic_no_external_ai"


def test_due_runner_advances_after_failure_without_leaking_exception(
    db_session: Session,
    monkeypatch,
) -> None:
    now = datetime(2026, 8, 23, 8, 0, tzinfo=UTC)
    schedule = configure_daily_brief_schedule(
        db_session,
        user_id="admin_user_id_fallback",
        enabled=True,
        timezone_name="UTC",
        local_time=time(7, 0),
        days_of_week=[0, 1, 2, 3, 4, 5, 6],
        now=now - timedelta(days=1),
    )
    schedule.next_run_at = now - timedelta(minutes=1)
    db_session.commit()

    def fail_generation(*_args, **_kwargs):
        raise RuntimeError("secret provider detail")

    monkeypatch.setattr(
        "app.services.daily_brief_schedule.MorningBriefingEngine.generate_briefing",
        fail_generation,
    )
    result = run_due_daily_brief_schedules(db_session, user_id=schedule.user_id, now=now)

    assert result["failures"] == 1
    assert "secret provider detail" not in str(result)
    persisted = db_session.get(DailyBriefSchedule, schedule.id)
    assert persisted is not None
    assert persisted.last_status == "failed"
    assert persisted.next_run_at is not None and as_utc(persisted.next_run_at) > now
    run = db_session.get(ProcessingRun, persisted.last_processing_run_id)
    assert run is not None
    assert run.error_details_json == {"error_type": "daily_brief_generation_failed"}


def test_due_runner_respects_active_lease(db_session: Session) -> None:
    now = datetime(2026, 8, 23, 8, 0, tzinfo=UTC)
    schedule = configure_daily_brief_schedule(
        db_session,
        user_id="admin_user_id_fallback",
        enabled=True,
        timezone_name="UTC",
        local_time=time(7, 0),
        days_of_week=[0, 1, 2, 3, 4, 5, 6],
        now=now - timedelta(days=1),
    )
    schedule.next_run_at = now - timedelta(minutes=1)
    schedule.lease_expires_at = now + timedelta(minutes=5)
    db_session.commit()

    result = run_due_daily_brief_schedules(db_session, user_id=schedule.user_id, now=now)

    assert result == {
        "schedules_checked": 0,
        "schedules_completed": 0,
        "briefs_created": 0,
        "failures": 0,
    }


def test_scheduler_poll_interval_has_a_safe_floor(monkeypatch) -> None:
    monkeypatch.setenv("DAILY_BRIEF_SCHEDULER_INTERVAL_SECONDS", "1")
    assert scheduler_interval_seconds() == 15

    monkeypatch.setenv("DAILY_BRIEF_SCHEDULER_INTERVAL_SECONDS", "invalid")
    assert scheduler_interval_seconds() == 60
