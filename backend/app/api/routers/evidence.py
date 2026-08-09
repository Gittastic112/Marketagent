from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import create_record, delete_record, get_or_404, update_record
from app.api.schemas import (
    ApiResponse,
    EvidenceLedgerItemCreate, EvidenceLedgerItemRead, EvidenceLedgerItemUpdate
)
from app.db.session import get_db
from app.models.evidence import EvidenceLedgerItem


router = APIRouter()


@router.post("/evidence", response_model=ApiResponse[EvidenceLedgerItemRead], status_code=status.HTTP_201_CREATED)
def create_evidence(payload: EvidenceLedgerItemCreate, db: Session = Depends(get_db)) -> EvidenceLedgerItem:
    return ApiResponse(data=create_record(db, EvidenceLedgerItem, payload))


@router.get("/evidence", response_model=ApiResponse[list[EvidenceLedgerItemRead]])
def list_evidence(company_id: int | None = None, db: Session = Depends(get_db)) -> list[EvidenceLedgerItem]:
    query = select(EvidenceLedgerItem)
    if company_id:
        query = query.where(EvidenceLedgerItem.company_id == company_id)
    return ApiResponse(data=list(db.scalars(query.order_by(EvidenceLedgerItem.date_discovered.desc()))))


@router.get("/evidence/{evidence_id}", response_model=ApiResponse[EvidenceLedgerItemRead])
def get_evidence(evidence_id: int, db: Session = Depends(get_db)) -> EvidenceLedgerItem:
    return ApiResponse(data=get_or_404(db, EvidenceLedgerItem, evidence_id))


@router.patch("/evidence/{evidence_id}", response_model=ApiResponse[EvidenceLedgerItemRead])
def update_evidence(
    evidence_id: int,
    payload: EvidenceLedgerItemUpdate,
    db: Session = Depends(get_db),
) -> EvidenceLedgerItem:
    return ApiResponse(data=update_record(db, get_or_404(db, EvidenceLedgerItem, evidence_id), payload))


@router.delete("/evidence/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evidence(evidence_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, EvidenceLedgerItem, evidence_id))
