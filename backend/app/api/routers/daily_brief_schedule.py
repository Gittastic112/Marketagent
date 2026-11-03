from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.schemas import (
    ApiResponse,
    DailyBriefScheduleRead,
    DailyBriefScheduleRunResult,
    DailyBriefScheduleUpdate,
)
from app.db.session import get_db
from app.models import DailyBriefSchedule
from app.services.daily_brief_schedule import (
    configure_daily_brief_schedule,
    run_due_daily_brief_schedules,
    schedule_response,
)


router = APIRouter()


def _schedule_meta() -> dict:
    return {
        "source": "local_schedule",
        "is_stale": False,
        "is_mock": False,
        "warnings": [],
        "confidence": "high",
    }


@router.get(
    "/daily-brief-schedule",
    response_model=ApiResponse[DailyBriefScheduleRead | None],
)
def get_daily_brief_schedule(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    schedule = db.scalar(
        select(DailyBriefSchedule).where(DailyBriefSchedule.user_id == current_user["id"])
    )
    return ApiResponse(
        data=schedule_response(schedule) if schedule else None,
        meta=_schedule_meta(),
    )


@router.put(
    "/daily-brief-schedule",
    response_model=ApiResponse[DailyBriefScheduleRead],
)
def put_daily_brief_schedule(
    payload: DailyBriefScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    schedule = configure_daily_brief_schedule(
        db,
        user_id=current_user["id"],
        enabled=payload.enabled,
        timezone_name=payload.timezone,
        local_time=payload.local_time,
        days_of_week=payload.days_of_week,
    )
    return ApiResponse(data=schedule_response(schedule), meta=_schedule_meta())


@router.post(
    "/daily-brief-schedule/run-due",
    response_model=ApiResponse[DailyBriefScheduleRunResult],
)
def run_owned_due_daily_brief_schedule(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = run_due_daily_brief_schedules(db, user_id=current_user["id"])
    return ApiResponse(data=result, meta=_schedule_meta())
