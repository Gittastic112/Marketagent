from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import apply_alert_review_timestamp, commit_or_conflict, delete_record, get_or_404, update_record, validate_alert_refs
from app.api.schemas import ApiResponse, AlertCreate, AlertRead, AlertUpdate
from app.db.session import get_db
from app.models import Alert, PortfolioHolding


router = APIRouter()


@router.post("/alerts", response_model=ApiResponse[AlertRead], status_code=status.HTTP_201_CREATED)
def create_alert(payload: AlertCreate, db: Session = Depends(get_db)) -> Alert:
    validate_alert_refs(db, payload)
    alert = Alert(**payload.model_dump())
    apply_alert_review_timestamp(alert, payload)
    db.add(alert)
    commit_or_conflict(db)
    db.refresh(alert)
    return ApiResponse(data=alert)


@router.get("/alerts", response_model=ApiResponse[list[AlertRead]])
def list_alerts(owned_only: bool = False, db: Session = Depends(get_db)) -> list[Alert]:
    stmt = select(Alert)
    if owned_only:
        stmt = stmt.join(PortfolioHolding, Alert.company_id == PortfolioHolding.company_id)
    stmt = stmt.order_by(Alert.id)
    return ApiResponse(data=list(db.scalars(stmt)))


@router.get("/alerts/{alert_id}", response_model=ApiResponse[AlertRead])
def get_alert(alert_id: int, db: Session = Depends(get_db)) -> Alert:
    return ApiResponse(data=get_or_404(db, Alert, alert_id))


@router.patch("/alerts/{alert_id}", response_model=ApiResponse[AlertRead])
def update_alert(alert_id: int, payload: AlertUpdate, db: Session = Depends(get_db)) -> Alert:
    validate_alert_refs(db, payload)
    alert = get_or_404(db, Alert, alert_id)
    apply_alert_review_timestamp(alert, payload)
    return ApiResponse(data=update_record(db, alert, payload))


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(alert_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, Alert, alert_id))
