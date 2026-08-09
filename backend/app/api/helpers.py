from datetime import UTC, datetime
from typing import TypeVar

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas import (
    AlertCreate,
    AlertUpdate,
    EventCreate,
    EventUpdate,
    PortfolioCashBalanceCreate,
    PortfolioCashBalanceUpdate,
    PortfolioHoldingCreate,
    PortfolioHoldingUpdate,
    PortfolioSnapshotCreate,
    PortfolioSnapshotUpdate,
    PortfolioTransactionCreate,
    PortfolioTransactionUpdate,
    RawDocumentCreate,
    RawDocumentUpdate,
    ThesisNoteCreate,
    ThesisNoteUpdate,
)
from app.models import (
    Alert,
    Company,
    Event,
    Portfolio,
    PortfolioCashBalance,
    PortfolioHolding,
    PortfolioSnapshot,
    PortfolioTransaction,
    RawDocument,
    Source,
    ThesisNote,
)


ModelT = TypeVar("ModelT")


def get_or_404(db: Session, model: type[ModelT], item_id: int, **kwargs) -> ModelT:
    if kwargs:
        from sqlalchemy import select
        query = select(model).where(model.id == item_id)
        for k, v in kwargs.items():
            query = query.where(getattr(model, k) == v)
        item = db.scalar(query)
    else:
        item = db.get(model, item_id)

    if item is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return item


def create_record(db: Session, model: type[ModelT], payload: object, **kwargs) -> ModelT:
    data = payload.model_dump()
    data.update(kwargs)
    record = model(**data)
    db.add(record)
    commit_or_conflict(db)
    db.refresh(record)
    return record


def update_record(db: Session, record: ModelT, payload: object) -> ModelT:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    commit_or_conflict(db)
    db.refresh(record)
    return record


def delete_record(db: Session, record: object) -> None:
    db.delete(record)
    commit_or_conflict(db)


def commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Record already exists") from exc


def require_reference(db: Session, model: type[ModelT], item_id: int | None, name: str) -> None:
    if item_id is not None and db.get(model, item_id) is None:
        raise HTTPException(status_code=404, detail=f"{name} not found")


def validate_raw_document_refs(db: Session, payload: RawDocumentCreate | RawDocumentUpdate) -> None:
    require_reference(db, Company, payload.company_id, "Company")
    require_reference(db, Source, payload.source_id, "Source")


def validate_event_refs(db: Session, payload: EventCreate | EventUpdate) -> None:
    require_reference(db, Company, payload.company_id, "Company")
    require_reference(db, RawDocument, payload.raw_document_id, "Raw document")


def validate_alert_refs(db: Session, payload: AlertCreate | AlertUpdate) -> None:
    require_reference(db, Event, payload.event_id, "Event")
    require_reference(db, Company, payload.company_id, "Company")


def apply_alert_review_timestamp(alert: Alert, payload: AlertCreate | AlertUpdate) -> None:
    changes = payload.model_dump(exclude_unset=True)
    status_changed_from_unreviewed = (
        "review_status" in changes
        and alert.review_status == "unreviewed"
        and changes["review_status"] != "unreviewed"
    )
    notes_updated = "review_notes" in changes
    if status_changed_from_unreviewed or notes_updated:
        alert.reviewed_at = datetime.now(UTC)


def validate_thesis_note_refs(db: Session, payload: ThesisNoteCreate | ThesisNoteUpdate) -> None:
    require_reference(db, Company, payload.company_id, "Company")


def validate_portfolio_holding_refs(db: Session, payload: PortfolioHoldingCreate | PortfolioHoldingUpdate) -> None:
    require_reference(db, Portfolio, payload.portfolio_id, "Portfolio")
    require_reference(db, Company, payload.company_id, "Company")


def validate_portfolio_transaction_refs(
    db: Session,
    payload: PortfolioTransactionCreate | PortfolioTransactionUpdate,
) -> None:
    require_reference(db, Portfolio, payload.portfolio_id, "Portfolio")
    require_reference(db, Company, payload.company_id, "Company")


def validate_portfolio_cash_balance_refs(
    db: Session,
    payload: PortfolioCashBalanceCreate | PortfolioCashBalanceUpdate,
) -> None:
    require_reference(db, Portfolio, payload.portfolio_id, "Portfolio")


def validate_portfolio_snapshot_refs(db: Session, payload: PortfolioSnapshotCreate | PortfolioSnapshotUpdate) -> None:
    require_reference(db, Portfolio, payload.portfolio_id, "Portfolio")


def company_has_linked_records(db: Session, company_id: int) -> bool:
    linked_queries = (
        select(RawDocument.id).where(RawDocument.company_id == company_id),
        select(Event.id).where(Event.company_id == company_id),
        select(Alert.id).where(Alert.company_id == company_id),
        select(ThesisNote.id).where(ThesisNote.company_id == company_id),
        select(PortfolioHolding.id).where(PortfolioHolding.company_id == company_id),
        select(PortfolioTransaction.id).where(PortfolioTransaction.company_id == company_id),
    )
    return any(db.scalar(query.limit(1)) is not None for query in linked_queries)


def portfolio_has_linked_records(db: Session, portfolio_id: int) -> bool:
    linked_queries = (
        select(PortfolioHolding.id).where(PortfolioHolding.portfolio_id == portfolio_id),
        select(PortfolioTransaction.id).where(PortfolioTransaction.portfolio_id == portfolio_id),
        select(PortfolioCashBalance.id).where(PortfolioCashBalance.portfolio_id == portfolio_id),
        select(PortfolioSnapshot.id).where(PortfolioSnapshot.portfolio_id == portfolio_id),
    )
    return any(db.scalar(query.limit(1)) is not None for query in linked_queries)


def has_matching_record(db: Session, query) -> bool:
    return db.scalar(query.limit(1)) is not None
