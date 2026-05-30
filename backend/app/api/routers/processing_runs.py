from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import ApiResponse, ProcessingRunRead
from app.db.session import get_db
from app.models import ProcessingRun


router = APIRouter()


@router.get("/processing-runs", response_model=ApiResponse[list[ProcessingRunRead]])
def list_processing_runs(db: Session = Depends(get_db)) -> list[ProcessingRun]:
    return ApiResponse(data=list(db.scalars(select(ProcessingRun).order_by(ProcessingRun.created_at.desc(), ProcessingRun.id.desc()).limit(100))))
