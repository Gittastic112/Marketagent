from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.evaluation import EvaluationRun
from app.schemas.evaluation import EvaluationDocumentBasis, EvaluationRunRead, FinancialEvaluationCreate
from app.services.extraction_evaluation import document_basis, execute_financial_evaluation

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/runs", response_model=ApiResponse[list[EvaluationRunRead]])
def get_evaluation_runs(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    runs = list(db.scalars(select(EvaluationRun).where(EvaluationRun.user_id == user["id"])
        .order_by(EvaluationRun.created_at.desc(), EvaluationRun.id.desc()).limit(10)))
    return ApiResponse(data=runs)


@router.get("/runs/{run_id}", response_model=ApiResponse[EvaluationRunRead])
def get_evaluation_run(run_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    run = db.scalar(select(EvaluationRun).where(EvaluationRun.id == run_id, EvaluationRun.user_id == user["id"]))
    if run is None:
        raise HTTPException(404, "Evaluation run not found.")
    return ApiResponse(data=run, meta={"is_mock": bool((run.report_json or {}).get("is_mock"))})


@router.get("/documents/{document_id}/basis", response_model=ApiResponse[EvaluationDocumentBasis])
def get_evaluation_basis(document_id: int, db: Session = Depends(get_db)):
    _, basis = document_basis(db, document_id)
    return ApiResponse(data=basis, meta={"is_mock": basis["is_mock"]})

@router.post(
    "/runs",
    response_model=ApiResponse[EvaluationRunRead],
    status_code=status.HTTP_201_CREATED,
)
def create_evaluation_run(payload: FinancialEvaluationCreate | None = None,
    db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if payload is not None:
        run = execute_financial_evaluation(db, user["id"], payload)
        return ApiResponse(data=run, meta={"is_mock": run.report_json["is_mock"],
            "source": "local_text_extractor", "warnings": run.report_json["limitations"]})
    # Preserve empty-body creation without falsely claiming execution.
    created_at = datetime.now(UTC)
    run = EvaluationRun(
        user_id=user["id"],
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
            "warnings": ["No reviewed reference dataset supplied; this record has not been run."],
            "confidence": "none",
        },
    )
