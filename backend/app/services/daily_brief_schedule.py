from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import DailyBrief, DailyBriefSchedule
from app.services.morning_briefing_engine import MorningBriefingEngine
from app.services.processing_runs import (
    complete_processing_run,
    fail_processing_run,
    start_processing_run,
)


SCHEDULE_LEASE_MINUTES = 10
GENERATION_MODE = "deterministic_no_external_ai"


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def compute_next_scheduled_run(
    *,
    timezone_name: str,
    local_time: time,
    days_of_week: list[int],
    after_utc: datetime,
) -> datetime:
    zone = ZoneInfo(timezone_name)
    after = _as_utc(after_utc)
    local_after = after.astimezone(zone)
    allowed_days = set(days_of_week)
    for offset in range(8):
        candidate_date = local_after.date() + timedelta(days=offset)
        if candidate_date.weekday() not in allowed_days:
            continue
        candidate_local = datetime.combine(candidate_date, local_time, tzinfo=zone)
        candidate_utc = candidate_local.astimezone(UTC)
        if candidate_utc > after:
            return candidate_utc
    raise ValueError("At least one valid schedule day is required")


def configure_daily_brief_schedule(
    db: Session,
    *,
    user_id: str,
    enabled: bool,
    timezone_name: str,
    local_time: time,
    days_of_week: list[int],
    now: datetime | None = None,
) -> DailyBriefSchedule:
    current_time = _as_utc(now or datetime.now(UTC))
    schedule = db.scalar(
        select(DailyBriefSchedule).where(DailyBriefSchedule.user_id == user_id)
    )
    if schedule is None:
        schedule = DailyBriefSchedule(user_id=user_id)
        db.add(schedule)
    schedule.enabled = enabled
    schedule.timezone = timezone_name
    schedule.local_time = local_time
    schedule.days_of_week = sorted(set(days_of_week))
    schedule.lease_expires_at = None
    schedule.next_run_at = (
        compute_next_scheduled_run(
            timezone_name=timezone_name,
            local_time=local_time,
            days_of_week=schedule.days_of_week,
            after_utc=current_time,
        )
        if enabled
        else None
    )
    schedule.last_status = "scheduled" if enabled else "disabled"
    db.commit()
    db.refresh(schedule)
    return schedule


def schedule_response(schedule: DailyBriefSchedule, *, now: datetime | None = None) -> dict:
    current_time = _as_utc(now or datetime.now(UTC))
    next_run_at = _as_utc(schedule.next_run_at) if schedule.next_run_at else None
    lease_expires_at = _as_utc(schedule.lease_expires_at) if schedule.lease_expires_at else None
    return {
        "id": schedule.id,
        "enabled": schedule.enabled,
        "timezone": schedule.timezone,
        "local_time": schedule.local_time,
        "days_of_week": schedule.days_of_week,
        "next_run_at": next_run_at,
        "due_now": bool(
            schedule.enabled
            and next_run_at is not None
            and next_run_at <= current_time
            and (lease_expires_at is None or lease_expires_at <= current_time)
        ),
        "last_attempted_at": schedule.last_attempted_at,
        "last_succeeded_at": schedule.last_succeeded_at,
        "last_status": schedule.last_status,
        "last_processing_run_id": schedule.last_processing_run_id,
        "last_brief_id": schedule.last_brief_id,
        "generation_mode": GENERATION_MODE,
        "created_at": schedule.created_at,
        "updated_at": schedule.updated_at,
    }


def run_due_daily_brief_schedules(
    db: Session,
    *,
    user_id: str | None = None,
    now: datetime | None = None,
) -> dict[str, int]:
    current_time = _as_utc(now or datetime.now(UTC))
    query = (
        select(DailyBriefSchedule)
        .where(
            DailyBriefSchedule.enabled.is_(True),
            DailyBriefSchedule.next_run_at.is_not(None),
            DailyBriefSchedule.next_run_at <= current_time,
            or_(
                DailyBriefSchedule.lease_expires_at.is_(None),
                DailyBriefSchedule.lease_expires_at <= current_time,
            ),
        )
        .order_by(DailyBriefSchedule.next_run_at, DailyBriefSchedule.id)
        .with_for_update(skip_locked=True)
    )
    if user_id is not None:
        query = query.where(DailyBriefSchedule.user_id == user_id)
    schedules = list(db.scalars(query))
    result = {
        "schedules_checked": len(schedules),
        "schedules_completed": 0,
        "briefs_created": 0,
        "failures": 0,
    }

    for candidate in schedules:
        due_at = _as_utc(candidate.next_run_at or current_time)
        candidate.lease_expires_at = current_time + timedelta(minutes=SCHEDULE_LEASE_MINUTES)
        candidate.last_attempted_at = current_time
        candidate.last_status = "running"
        db.commit()

        run = start_processing_run(
            db,
            run_type="daily_brief_schedule",
            source_type="internal",
            metadata={
                "schedule_id": candidate.id,
                "scheduled_for": due_at.isoformat(),
                "generation_mode": GENERATION_MODE,
            },
        )
        try:
            target_date = due_at.astimezone(ZoneInfo(candidate.timezone)).date()
            existing = db.scalar(
                select(DailyBrief).where(
                    DailyBrief.user_id == candidate.user_id,
                    DailyBrief.brief_date == target_date,
                )
            )
            brief = MorningBriefingEngine.get_or_generate_briefing(
                db,
                candidate.user_id,
                target_date,
            )
            created_count = 0 if existing is not None else 1
            completed_run = complete_processing_run(
                db,
                run,
                created_count=created_count,
                metadata_patch={"brief_id": brief.id},
            )
            schedule = db.get(DailyBriefSchedule, candidate.id)
            if schedule is None:
                continue
            schedule.last_status = "success"
            schedule.last_succeeded_at = current_time
            schedule.last_processing_run_id = completed_run.id
            schedule.last_brief_id = brief.id
            schedule.lease_expires_at = None
            schedule.next_run_at = compute_next_scheduled_run(
                timezone_name=schedule.timezone,
                local_time=schedule.local_time,
                days_of_week=schedule.days_of_week,
                after_utc=max(current_time, due_at),
            )
            db.commit()
            result["schedules_completed"] += 1
            result["briefs_created"] += created_count
        except Exception:
            db.rollback()
            persisted_run = db.get(type(run), run.id)
            if persisted_run is not None:
                failed_run = fail_processing_run(
                    db,
                    persisted_run,
                    error_type="daily_brief_generation_failed",
                )
            else:
                failed_run = None
            schedule = db.get(DailyBriefSchedule, candidate.id)
            if schedule is not None:
                schedule.last_status = "failed"
                schedule.last_processing_run_id = failed_run.id if failed_run else None
                schedule.lease_expires_at = None
                schedule.next_run_at = compute_next_scheduled_run(
                    timezone_name=schedule.timezone,
                    local_time=schedule.local_time,
                    days_of_week=schedule.days_of_week,
                    after_utc=max(current_time, due_at),
                )
                db.commit()
            result["failures"] += 1
    return result
