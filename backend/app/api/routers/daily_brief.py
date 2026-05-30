from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import ApiResponse, DailyBriefRead
from app.db.session import get_db
from app.models import DailyBrief
from app.services.daily_brief import generate_daily_brief, save_daily_brief


router = APIRouter()


@router.get("/daily-brief", response_model=ApiResponse[dict])
def get_daily_brief(db: Session = Depends(get_db)):
    return ApiResponse(data=generate_daily_brief(db))


@router.post("/daily-brief", response_model=ApiResponse[DailyBriefRead], status_code=status.HTTP_201_CREATED)
def create_daily_brief(db: Session = Depends(get_db)) -> DailyBrief:
    return ApiResponse(data=save_daily_brief(db))


@router.get("/daily-brief-history", response_model=ApiResponse[list[DailyBriefRead]])
def list_daily_brief_history(db: Session = Depends(get_db)) -> list[DailyBrief]:
    return ApiResponse(data=list(db.scalars(select(DailyBrief).order_by(DailyBrief.created_at.desc(), DailyBrief.id.desc()).limit(30))))
