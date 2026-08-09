from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.schemas import ApiResponse
from app.db.session import get_db
from app.models.evaluation import EvaluationRun

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


class EvaluationRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_name: str
    evaluation_type: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None


@router.get("/runs", response_model=ApiResponse[list[EvaluationRunRead]])
def get_evaluation_runs(db: Session = Depends(get_db)) -> ApiResponse[list[EvaluationRun]]:
    """Returns recent evaluation runs and their aggregate scores."""
    runs = db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(10).all()
    return ApiResponse(data=runs)

@router.post(
    "/runs",
    response_model=ApiResponse[EvaluationRunRead],
    status_code=status.HTTP_201_CREATED,
)
def create_evaluation_run(db: Session = Depends(get_db)) -> ApiResponse[EvaluationRun]:
    """Creates an explicitly unexecuted evaluation run record."""
    created_at = datetime.now(UTC)
    run = EvaluationRun(
        run_name=f"Manual financial extraction evaluation {created_at.isoformat()}",
        evaluation_type="financial_extraction",
        status="created",
        created_at=created_at,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return ApiResponse(
        data=run,
        meta={
            "status": "created",
            "warnings": ["Evaluation execution is not implemented; this record has not been run."],
            "confidence": "none",
        },
    )
