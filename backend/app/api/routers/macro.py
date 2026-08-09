from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import (
    ApiResponse,
    MacroObservationCreate,
    MacroObservationRead,
    MacroSeriesCreate,
    MacroSeriesRead,
)
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.macro import MacroObservation, MacroSeries
from app.schemas.macro import MacroTopDownRequest, MacroBottomUpRequest, MacroSensitivityResult
from app.services.macro_sensitivity_service import (
    run_top_down_macro_sensitivity,
    run_bottom_up_macro_sensitivity
)
router = APIRouter()

@router.get("/macro", response_model=ApiResponse[list[MacroSeriesRead]])
def list_macro_series(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return ApiResponse(data=list(db.scalars(select(MacroSeries).order_by(MacroSeries.name))))

@router.post("/macro", response_model=ApiResponse[MacroSeriesRead])
def create_macro_series(payload: MacroSeriesCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    series = MacroSeries(**payload.model_dump())
    db.add(series)
    db.commit()
    db.refresh(series)
    return ApiResponse(data=series)

@router.get("/macro/{series_id}", response_model=ApiResponse[MacroSeriesRead])
def get_macro_series(series_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    series = db.get(MacroSeries, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return ApiResponse(data=series)

@router.post("/macro/{series_id}/observations", response_model=ApiResponse[MacroObservationRead])
def create_macro_observation(series_id: int, payload: MacroObservationCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    series = db.get(MacroSeries, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    observation = MacroObservation(series_id=series_id, **payload.model_dump())
    db.add(observation)
    db.commit()
    db.refresh(observation)
    return ApiResponse(data=observation)

@router.delete("/macro/{series_id}", response_model=ApiResponse[dict[str, str]])
def delete_macro_series(series_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    series = db.get(MacroSeries, series_id)
    if series:
        db.delete(series)
        db.commit()
    return ApiResponse(data={"status": "ok"})


@router.post("/valuation/macro/top-down", response_model=ApiResponse[MacroSensitivityResult])
def calculate_top_down_macro(
    request: MacroTopDownRequest,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    """
    Run top-down regression of company history vs macro variables.
    """
    result = run_top_down_macro_sensitivity(db, request)
    return ApiResponse(data=result)


@router.post("/valuation/macro/bottom-up", response_model=ApiResponse[MacroSensitivityResult])
def calculate_bottom_up_macro(
    request: MacroBottomUpRequest,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    """
    Run bottom-up calculation of company macro sensitivity using segment weights.
    """
    result = run_bottom_up_macro_sensitivity(db, request)
    return ApiResponse(data=result)
