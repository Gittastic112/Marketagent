from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import (
    commit_or_conflict,
    create_record,
    delete_record,
    get_or_404,
    portfolio_has_linked_records,
    update_record,
    validate_portfolio_cash_balance_refs,
    validate_portfolio_holding_refs,
    validate_portfolio_snapshot_refs,
    validate_portfolio_transaction_refs,
)
from app.api.schemas import (
    ApiResponse,
    PortfolioCashBalanceCreate,
    PortfolioCashBalanceRead,
    PortfolioCashBalanceUpdate,
    PortfolioCreate,
    PortfolioHoldingCreate,
    PortfolioHoldingRead,
    PortfolioHoldingUpdate,
    PortfolioRead,
    PortfolioSnapshotCreate,
    PortfolioSnapshotRead,
    PortfolioSnapshotUpdate,
    PortfolioTransactionCreate,
    PortfolioTransactionRead,
    PortfolioTransactionUpdate,
    PortfolioUpdate,
)
from app.db.session import get_db
from app.models import Portfolio, PortfolioCashBalance, PortfolioHolding, PortfolioSnapshot, PortfolioTransaction
from app.services.portfolio_holdings import apply_transaction_to_holding, apply_transaction_to_cash


router = APIRouter()


def normalize_portfolio_symbol_fields(payload: object) -> ApiResponse[None]:
    if hasattr(payload, "ticker") and getattr(payload, "ticker") is not None:
        setattr(payload, "ticker", getattr(payload, "ticker").upper())
    if hasattr(payload, "currency") and getattr(payload, "currency") is not None:
        setattr(payload, "currency", getattr(payload, "currency").upper())
    if hasattr(payload, "base_currency") and getattr(payload, "base_currency") is not None:
        setattr(payload, "base_currency", getattr(payload, "base_currency").upper())


@router.post("/portfolios", response_model=ApiResponse[PortfolioRead], status_code=status.HTTP_201_CREATED)
def create_portfolio(payload: PortfolioCreate, db: Session = Depends(get_db)) -> Portfolio:
    normalize_portfolio_symbol_fields(payload)
    return ApiResponse(data=create_record(db, Portfolio, payload))


@router.get("/portfolios", response_model=ApiResponse[list[PortfolioRead]])
def list_portfolios(db: Session = Depends(get_db)) -> list[Portfolio]:
    return ApiResponse(data=list(db.scalars(select(Portfolio).order_by(Portfolio.id))))


@router.get("/portfolios/{portfolio_id}", response_model=ApiResponse[PortfolioRead])
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)) -> Portfolio:
    return ApiResponse(data=get_or_404(db, Portfolio, portfolio_id))


@router.patch("/portfolios/{portfolio_id}", response_model=ApiResponse[PortfolioRead])
def update_portfolio(portfolio_id: int, payload: PortfolioUpdate, db: Session = Depends(get_db)) -> Portfolio:
    normalize_portfolio_symbol_fields(payload)
    return ApiResponse(data=update_record(db, get_or_404(db, Portfolio, portfolio_id), payload))


@router.delete("/portfolios/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)) -> None:
    portfolio = get_or_404(db, Portfolio, portfolio_id)
    if portfolio_has_linked_records(db, portfolio_id):
        raise HTTPException(
            status_code=409,
            detail=(
                "Portfolio cannot be deleted while it has linked records. "
                "Delete holdings, transactions, cash balances, and snapshots first."
            ),
        )
    delete_record(db, portfolio)


@router.post("/portfolio-holdings", response_model=ApiResponse[PortfolioHoldingRead], status_code=status.HTTP_201_CREATED)
def create_portfolio_holding(payload: PortfolioHoldingCreate, db: Session = Depends(get_db)) -> PortfolioHolding:
    normalize_portfolio_symbol_fields(payload)
    validate_portfolio_holding_refs(db, payload)
    return ApiResponse(data=create_record(db, PortfolioHolding, payload))


@router.get("/portfolio-holdings", response_model=ApiResponse[list[PortfolioHoldingRead]])
def list_portfolio_holdings(portfolio_id: int | None = None, db: Session = Depends(get_db)) -> list[PortfolioHolding]:
    query = select(PortfolioHolding).order_by(PortfolioHolding.id)
    if portfolio_id is not None:
        query = query.where(PortfolioHolding.portfolio_id == portfolio_id)
    return ApiResponse(data=list(db.scalars(query)))


@router.get("/portfolio-holdings/{holding_id}", response_model=ApiResponse[PortfolioHoldingRead])
def get_portfolio_holding(holding_id: int, db: Session = Depends(get_db)) -> PortfolioHolding:
    return ApiResponse(data=get_or_404(db, PortfolioHolding, holding_id))


@router.patch("/portfolio-holdings/{holding_id}", response_model=ApiResponse[PortfolioHoldingRead])
def update_portfolio_holding(
    holding_id: int,
    payload: PortfolioHoldingUpdate,
    db: Session = Depends(get_db),
) -> PortfolioHolding:
    normalize_portfolio_symbol_fields(payload)
    validate_portfolio_holding_refs(db, payload)
    return ApiResponse(data=update_record(db, get_or_404(db, PortfolioHolding, holding_id), payload))


@router.delete("/portfolio-holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_holding(holding_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, PortfolioHolding, holding_id))


@router.post("/portfolio-transactions", response_model=ApiResponse[PortfolioTransactionRead], status_code=status.HTTP_201_CREATED)
def create_portfolio_transaction(
    payload: PortfolioTransactionCreate,
    db: Session = Depends(get_db),
) -> PortfolioTransaction:
    normalize_portfolio_symbol_fields(payload)
    validate_portfolio_transaction_refs(db, payload)
    transaction = PortfolioTransaction(**payload.model_dump())
    db.add(transaction)
    try:
        apply_transaction_to_holding(db, transaction)
        apply_transaction_to_cash(db, transaction)
        commit_or_conflict(db)
    except HTTPException:
        db.rollback()
        raise
    db.refresh(transaction)
    return ApiResponse(data=transaction)


@router.get("/portfolio-transactions", response_model=ApiResponse[list[PortfolioTransactionRead]])
def list_portfolio_transactions(
    portfolio_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[PortfolioTransaction]:
    query = select(PortfolioTransaction).order_by(PortfolioTransaction.id)
    if portfolio_id is not None:
        query = query.where(PortfolioTransaction.portfolio_id == portfolio_id)
    return ApiResponse(data=list(db.scalars(query)))


@router.get("/portfolio-transactions/{transaction_id}", response_model=ApiResponse[PortfolioTransactionRead])
def get_portfolio_transaction(transaction_id: int, db: Session = Depends(get_db)) -> PortfolioTransaction:
    return ApiResponse(data=get_or_404(db, PortfolioTransaction, transaction_id))


@router.patch("/portfolio-transactions/{transaction_id}", response_model=ApiResponse[PortfolioTransactionRead])
def update_portfolio_transaction(
    transaction_id: int,
    payload: PortfolioTransactionUpdate,
    db: Session = Depends(get_db),
) -> PortfolioTransaction:
    normalize_portfolio_symbol_fields(payload)
    validate_portfolio_transaction_refs(db, payload)
    transaction = get_or_404(db, PortfolioTransaction, transaction_id)
    try:
        apply_transaction_to_holding(db, transaction, direction=-1)
        apply_transaction_to_cash(db, transaction, direction=-1)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(transaction, field, value)
        apply_transaction_to_holding(db, transaction)
        apply_transaction_to_cash(db, transaction)
        commit_or_conflict(db)
    except HTTPException:
        db.rollback()
        raise
    db.refresh(transaction)
    return ApiResponse(data=transaction)


@router.delete("/portfolio-transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_transaction(transaction_id: int, db: Session = Depends(get_db)) -> None:
    transaction = get_or_404(db, PortfolioTransaction, transaction_id)
    try:
        apply_transaction_to_holding(db, transaction, direction=-1)
        apply_transaction_to_cash(db, transaction, direction=-1)
        db.delete(transaction)
        commit_or_conflict(db)
    except HTTPException:
        db.rollback()
        raise


@router.post("/portfolio-cash-balances", response_model=ApiResponse[PortfolioCashBalanceRead], status_code=status.HTTP_201_CREATED)
def create_portfolio_cash_balance(
    payload: PortfolioCashBalanceCreate,
    db: Session = Depends(get_db),
) -> PortfolioCashBalance:
    normalize_portfolio_symbol_fields(payload)
    validate_portfolio_cash_balance_refs(db, payload)
    return ApiResponse(data=create_record(db, PortfolioCashBalance, payload))


@router.get("/portfolio-cash-balances", response_model=ApiResponse[list[PortfolioCashBalanceRead]])
def list_portfolio_cash_balances(
    portfolio_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[PortfolioCashBalance]:
    query = select(PortfolioCashBalance).order_by(PortfolioCashBalance.id)
    if portfolio_id is not None:
        query = query.where(PortfolioCashBalance.portfolio_id == portfolio_id)
    return ApiResponse(data=list(db.scalars(query)))


@router.get("/portfolio-cash-balances/{cash_balance_id}", response_model=ApiResponse[PortfolioCashBalanceRead])
def get_portfolio_cash_balance(cash_balance_id: int, db: Session = Depends(get_db)) -> PortfolioCashBalance:
    return ApiResponse(data=get_or_404(db, PortfolioCashBalance, cash_balance_id))


@router.patch("/portfolio-cash-balances/{cash_balance_id}", response_model=ApiResponse[PortfolioCashBalanceRead])
def update_portfolio_cash_balance(
    cash_balance_id: int,
    payload: PortfolioCashBalanceUpdate,
    db: Session = Depends(get_db),
) -> PortfolioCashBalance:
    normalize_portfolio_symbol_fields(payload)
    validate_portfolio_cash_balance_refs(db, payload)
    return ApiResponse(data=update_record(db, get_or_404(db, PortfolioCashBalance, cash_balance_id), payload))


@router.delete("/portfolio-cash-balances/{cash_balance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_cash_balance(cash_balance_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, PortfolioCashBalance, cash_balance_id))


@router.post("/portfolio-snapshots", response_model=ApiResponse[PortfolioSnapshotRead], status_code=status.HTTP_201_CREATED)
def create_portfolio_snapshot(payload: PortfolioSnapshotCreate, db: Session = Depends(get_db)) -> PortfolioSnapshot:
    validate_portfolio_snapshot_refs(db, payload)
    return ApiResponse(data=create_record(db, PortfolioSnapshot, payload))


@router.get("/portfolio-snapshots", response_model=ApiResponse[list[PortfolioSnapshotRead]])
def list_portfolio_snapshots(
    portfolio_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[PortfolioSnapshot]:
    query = select(PortfolioSnapshot).order_by(PortfolioSnapshot.id)
    if portfolio_id is not None:
        query = query.where(PortfolioSnapshot.portfolio_id == portfolio_id)
    return ApiResponse(data=list(db.scalars(query)))


@router.get("/portfolio-snapshots/{snapshot_id}", response_model=ApiResponse[PortfolioSnapshotRead])
def get_portfolio_snapshot(snapshot_id: int, db: Session = Depends(get_db)) -> PortfolioSnapshot:
    return ApiResponse(data=get_or_404(db, PortfolioSnapshot, snapshot_id))


@router.patch("/portfolio-snapshots/{snapshot_id}", response_model=ApiResponse[PortfolioSnapshotRead])
def update_portfolio_snapshot(
    snapshot_id: int,
    payload: PortfolioSnapshotUpdate,
    db: Session = Depends(get_db),
) -> PortfolioSnapshot:
    validate_portfolio_snapshot_refs(db, payload)
    return ApiResponse(data=update_record(db, get_or_404(db, PortfolioSnapshot, snapshot_id), payload))


@router.delete("/portfolio-snapshots/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_snapshot(snapshot_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, PortfolioSnapshot, snapshot_id))


from datetime import date
from app.api.schemas import PortfolioValuationRead, PortfolioAnalyticsRead
from app.services.portfolio_valuation import calculate_portfolio_valuation
from app.services.portfolio_analytics import calculate_portfolio_analytics

@router.get("/portfolios/{portfolio_id}/valuation", response_model=ApiResponse[PortfolioValuationRead])
def get_portfolio_valuation(
    portfolio_id: int,
    as_of_date: date | None = None,
    db: Session = Depends(get_db)
) -> dict:
    try:
        return ApiResponse(data=calculate_portfolio_valuation(db, portfolio_id, as_of_date))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/portfolios/{portfolio_id}/analytics", response_model=ApiResponse[PortfolioAnalyticsRead])
def get_portfolio_analytics(
    portfolio_id: int,
    as_of_date: date | None = None,
    db: Session = Depends(get_db)
) -> dict:
    try:
        return ApiResponse(data=calculate_portfolio_analytics(db, portfolio_id, as_of_date))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

