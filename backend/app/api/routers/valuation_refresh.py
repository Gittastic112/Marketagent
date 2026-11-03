from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.schemas.common import ApiResponse
from app.db.session import get_db
from app.models import Company, ProcessingRun
from app.schemas.valuation_refresh import ValuationSourceRefreshRead, ValuationRefreshStatusRead
from app.services.valuation_source_refresh import RUN_TYPE, cancel_queued_refresh, enqueue_company_refresh, refresh_status, run_response

router = APIRouter(tags=["valuation source refresh"])


@router.post("/companies/{company_id}/valuation-source-refresh", status_code=202,
    response_model=ApiResponse[ValuationSourceRefreshRead])
def queue_refresh(company_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return ApiResponse(data=run_response(enqueue_company_refresh(db, company_id, user["id"])))


@router.get("/companies/{company_id}/valuation-source-refresh",
    response_model=ApiResponse[ValuationRefreshStatusRead])
def company_refresh_status(company_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if db.get(Company, company_id) is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return ApiResponse(data=refresh_status(db, user["id"], company_id))


@router.get("/valuation-source-refresh/{run_id}", response_model=ApiResponse[ValuationSourceRefreshRead])
def get_refresh(run_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    run = db.get(ProcessingRun, run_id)
    if run is None or run.run_type != RUN_TYPE or (run.metadata_json or {}).get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Source refresh not found")
    return ApiResponse(data=run_response(run))


@router.post("/valuation-source-refresh/{run_id}/cancel", response_model=ApiResponse[ValuationSourceRefreshRead])
def cancel_refresh(run_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return ApiResponse(data=run_response(cancel_queued_refresh(db, run_id, user["id"])))
