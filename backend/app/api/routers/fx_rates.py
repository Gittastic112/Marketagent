from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import create_record, delete_record, get_or_404
from app.api.schemas import ApiMeta, ApiResponse, FxRateObservationCreate, FxRateObservationRead
from app.db.session import get_db
from app.models import FxRateObservation


router = APIRouter(prefix="/fx-rates", tags=["fx-rates"])


@router.post("", response_model=ApiResponse[FxRateObservationRead], status_code=status.HTTP_201_CREATED)
def create_fx_rate(
    payload: FxRateObservationCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[FxRateObservation]:
    observation = create_record(db, FxRateObservation, payload)
    return ApiResponse(
        data=observation,
        meta=ApiMeta(
            source=observation.provider_name,
            last_updated=observation.source_timestamp or observation.observed_at,
            confidence="medium" if observation.provider_name == "manual" else "high",
            warnings=(
                ["Manual FX observation. Verify the recorded source before material use."]
                if observation.provider_name == "manual"
                else []
            ),
        ),
    )


@router.get("", response_model=ApiResponse[list[FxRateObservationRead]])
def list_fx_rates(
    base_currency: str | None = None,
    quote_currency: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
) -> ApiResponse[list[FxRateObservation]]:
    query = select(FxRateObservation)
    if base_currency:
        query = query.where(FxRateObservation.base_currency == base_currency.strip().upper())
    if quote_currency:
        query = query.where(FxRateObservation.quote_currency == quote_currency.strip().upper())
    if start_date:
        query = query.where(FxRateObservation.as_of_date >= start_date)
    if end_date:
        query = query.where(FxRateObservation.as_of_date <= end_date)
    records = list(
        db.scalars(
            query.order_by(FxRateObservation.as_of_date.desc(), FxRateObservation.id.desc())
        )
    )
    return ApiResponse(data=records)


@router.get("/{observation_id}", response_model=ApiResponse[FxRateObservationRead])
def get_fx_rate(
    observation_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[FxRateObservation]:
    return ApiResponse(data=get_or_404(db, FxRateObservation, observation_id))


@router.delete("/{observation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fx_rate(observation_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, FxRateObservation, observation_id))
