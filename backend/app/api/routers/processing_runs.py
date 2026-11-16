from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import ApiResponse, ProcessingRunRead
from app.db.session import get_db
from app.models import ProcessingRun
from app.api.dependencies import get_current_user
from app.services.processing_run_visibility import visible_processing_run_filter


router = APIRouter()


@router.get("/processing-runs", response_model=ApiResponse[list[ProcessingRunRead]])
def list_processing_runs(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> list[ProcessingRun]:
    return ApiResponse(data=list(db.scalars(select(ProcessingRun)
        .where(visible_processing_run_filter(current_user["id"]))
        .order_by(ProcessingRun.created_at.desc(), ProcessingRun.id.desc()).limit(100))))
