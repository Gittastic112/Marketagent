from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import ApiResponse, DailyBriefRead
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import DailyBrief
from app.services.morning_briefing_engine import MorningBriefingEngine


router = APIRouter()


def _brief_response(brief: DailyBrief) -> ApiResponse[DailyBrief]:
    payload = brief.payload_json or {}
    calculation_status = payload.get("calculation_status", "not_available")
    return ApiResponse(
        data=brief,
        meta={
            "source": "stored_events_alerts_holdings_prices_and_reviewed_ai_outputs",
            "is_mock": bool(payload.get("contains_mock_data", False)),
            "is_stale": bool(payload.get("contains_stale_data", False)),
            "warnings": payload.get("warnings", []),
            "confidence": "high" if calculation_status == "complete" else "medium",
        },
    )


@router.get("/daily-brief", response_model=ApiResponse[DailyBriefRead])
def get_daily_brief(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return _brief_response(
        MorningBriefingEngine.get_or_generate_briefing(
            db,
            user_id=current_user["id"],
        )
    )

@router.post("/daily-brief", response_model=ApiResponse[DailyBriefRead], status_code=status.HTTP_201_CREATED)
def create_daily_brief(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> DailyBrief:
    return _brief_response(
        MorningBriefingEngine.generate_briefing(db, user_id=current_user["id"])
    )


@router.get("/daily-brief-history", response_model=ApiResponse[list[DailyBriefRead]])
def list_daily_brief_history(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> list[DailyBrief]:
    return ApiResponse(data=list(db.scalars(select(DailyBrief).where(DailyBrief.user_id == current_user["id"]).order_by(DailyBrief.created_at.desc(), DailyBrief.id.desc()).limit(30))))


@router.patch("/daily-brief/{brief_id}/review", response_model=ApiResponse[DailyBriefRead])
def review_daily_brief(brief_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    brief = db.scalar(select(DailyBrief).where(DailyBrief.id == brief_id, DailyBrief.user_id == current_user["id"]))
    if not brief:
        raise HTTPException(status_code=404, detail="Daily brief not found")

    brief.review_status = "reviewed"
    brief.reviewed_at = datetime.now(UTC)
    db.commit()
    db.refresh(brief)

    return ApiResponse(data=brief)
