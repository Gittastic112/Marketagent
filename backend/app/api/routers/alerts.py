from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import apply_alert_review_timestamp, commit_or_conflict, delete_record, get_or_404, update_record, validate_alert_refs
from app.api.schemas import ApiMeta, ApiResponse, AlertCreate, AlertRead, AlertUpdate, EvidenceTrailRead
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import Alert, Event, PortfolioHolding
from app.services.evidence_trail_service import build_evidence_trail


router = APIRouter()


@router.post("/alerts", response_model=ApiResponse[AlertRead], status_code=status.HTTP_201_CREATED)
def create_alert(payload: AlertCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> Alert:
    validate_alert_refs(db, payload)
    alert = Alert(**payload.model_dump(), user_id=current_user["id"])
    apply_alert_review_timestamp(alert, payload)
    db.add(alert)
    commit_or_conflict(db)
    db.refresh(alert)
    return ApiResponse(data=alert)


@router.get("/alerts", response_model=ApiResponse[list[AlertRead]])
def list_alerts(owned_only: bool = False, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> list[Alert]:
    stmt = select(Alert).where(Alert.user_id == current_user["id"])
    if owned_only:
        stmt = stmt.join(PortfolioHolding, Alert.company_id == PortfolioHolding.company_id)
    stmt = stmt.order_by(Alert.id)
    return ApiResponse(data=list(db.scalars(stmt)))


@router.get("/alerts/{alert_id}", response_model=ApiResponse[AlertRead])
def get_alert(alert_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> Alert:
    return ApiResponse(data=get_or_404(db, Alert, alert_id, user_id=current_user["id"]))


@router.get("/alerts/{alert_id}/evidence-trail", response_model=ApiResponse[EvidenceTrailRead])
def get_alert_evidence_trail(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[EvidenceTrailRead]:
    alert = get_or_404(db, Alert, alert_id, user_id=current_user["id"])
    event = db.get(Event, alert.event_id) if alert.event_id else None
    trail = build_evidence_trail(
        db,
        user_id=current_user["id"],
        event=event,
        alert=alert,
    )
    return ApiResponse(
        data=trail,
        meta=ApiMeta(
            source=trail.source.name if trail.source else "internal",
            last_updated=trail.source_timestamp,
            warnings=trail.warnings,
            confidence=trail.confidence,
        ),
    )


@router.patch("/alerts/{alert_id}", response_model=ApiResponse[AlertRead])
def update_alert(alert_id: int, payload: AlertUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> Alert:
    validate_alert_refs(db, payload)
    alert = get_or_404(db, Alert, alert_id, user_id=current_user["id"])
    apply_alert_review_timestamp(alert, payload)
    return ApiResponse(data=update_record(db, alert, payload))


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(alert_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> None:
    delete_record(db, get_or_404(db, Alert, alert_id, user_id=current_user["id"]))
