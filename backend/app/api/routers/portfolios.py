from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
from app.api.errors import PublicApiError
from app.schemas.common import ApiResponse
from app.schemas.portfolio import (
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
    PortfolioValuationRead,
    PortfolioAnalyticsRead,
    PortfolioAttributionRead,
    PortfolioBenchmarkConfigCreate,
    PortfolioBenchmarkConfigRead,
    PortfolioBenchmarkConfigUpdate,
    PortfolioPerformanceRead,
    PortfolioPeriodAttributionRead,
    PortfolioOpportunityCostRead,
    PortfolioRealInputReadinessRead,
    PortfolioRiskReturnRead,
)
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import (
    Company,
    Portfolio,
    PortfolioBenchmarkConfig,
    PortfolioCashBalance,
    PortfolioHolding,
    PortfolioSnapshot,
    PortfolioTransaction,
)
from app.services.portfolio_holdings import apply_transaction_to_holding, apply_transaction_to_cash
from app.services.portfolio_valuation import calculate_portfolio_valuation
from app.services.portfolio_analytics import calculate_portfolio_analytics, record_daily_snapshot
from app.services.portfolio_attribution_engine import PortfolioAttributionEngine
from app.services.portfolio_performance import calculate_money_weighted_return, calculate_time_weighted_return
from app.services.portfolio_period_attribution import calculate_period_attribution
from app.services.portfolio_benchmark import calculate_benchmark_opportunity_cost
from app.services.portfolio_risk_return import calculate_portfolio_risk_return
from app.services.portfolio_real_input_readiness import audit_portfolio_real_input_readiness


router = APIRouter()


def normalize_portfolio_symbol_fields(payload: object) -> None:
    if hasattr(payload, "ticker") and getattr(payload, "ticker") is not None:
        setattr(payload, "ticker", getattr(payload, "ticker").upper())
    if hasattr(payload, "currency") and getattr(payload, "currency") is not None:
        setattr(payload, "currency", getattr(payload, "currency").upper())
    if hasattr(payload, "base_currency") and getattr(payload, "base_currency") is not None:
        setattr(payload, "base_currency", getattr(payload, "base_currency").upper())


def get_owned_portfolio(
    db: Session,
    portfolio_id: int,
    user_id: str,
) -> Portfolio:
    portfolio = db.scalar(
        select(Portfolio).where(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id,
        )
    )
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


def get_owned_portfolio_child(
    db: Session,
    model: type,
    record_id: int,
    user_id: str,
):
    record = db.scalar(
        select(model)
        .join(Portfolio, model.portfolio_id == Portfolio.id)
        .where(
            model.id == record_id,
            Portfolio.user_id == user_id,
        )
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


def require_owned_payload_portfolio(
    db: Session,
    payload: object,
    user_id: str,
) -> None:
    portfolio_id = getattr(payload, "portfolio_id", None)
    if portfolio_id is not None:
        get_owned_portfolio(db, portfolio_id, user_id)


def validate_benchmark_company(db: Session, company_id: int | None) -> None:
    if company_id is not None and db.get(Company, company_id) is None:
        raise HTTPException(status_code=422, detail="Benchmark company not found")


@router.post("/portfolios", response_model=ApiResponse[PortfolioRead], status_code=status.HTTP_201_CREATED)
def create_portfolio(payload: PortfolioCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> Portfolio:
    normalize_portfolio_symbol_fields(payload)
    return ApiResponse(data=create_record(db, Portfolio, payload, user_id=current_user["id"]))


@router.get("/portfolios", response_model=ApiResponse[list[PortfolioRead]])
def list_portfolios(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> list[Portfolio]:
    return ApiResponse(data=list(db.scalars(select(Portfolio).where(Portfolio.user_id == current_user["id"]).order_by(Portfolio.id))))


@router.get("/portfolios/{portfolio_id}", response_model=ApiResponse[PortfolioRead])
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> Portfolio:
    return ApiResponse(data=get_or_404(db, Portfolio, portfolio_id, user_id=current_user["id"]))


@router.patch("/portfolios/{portfolio_id}", response_model=ApiResponse[PortfolioRead])
def update_portfolio(portfolio_id: int, payload: PortfolioUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> Portfolio:
    normalize_portfolio_symbol_fields(payload)
    return ApiResponse(data=update_record(db, get_or_404(db, Portfolio, portfolio_id, user_id=current_user["id"]), payload))


@router.delete("/portfolios/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> None:
    portfolio = get_or_404(db, Portfolio, portfolio_id, user_id=current_user["id"])
    if portfolio_has_linked_records(db, portfolio_id):
        raise HTTPException(
            status_code=409,
            detail=(
                "Portfolio cannot be deleted while it has linked records. "
                "Delete holdings, transactions, cash balances, and snapshots first."
            ),
        )
    delete_record(db, portfolio)


@router.post(
    "/portfolio-benchmarks",
    response_model=ApiResponse[PortfolioBenchmarkConfigRead],
    status_code=status.HTTP_201_CREATED,
)
def create_portfolio_benchmark(
    payload: PortfolioBenchmarkConfigCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PortfolioBenchmarkConfig]:
    get_owned_portfolio(db, payload.portfolio_id, current_user["id"])
    validate_benchmark_company(db, payload.benchmark_company_id)
    return ApiResponse(data=create_record(db, PortfolioBenchmarkConfig, payload))


@router.get(
    "/portfolio-benchmarks",
    response_model=ApiResponse[list[PortfolioBenchmarkConfigRead]],
)
def list_portfolio_benchmarks(
    portfolio_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[list[PortfolioBenchmarkConfig]]:
    query = (
        select(PortfolioBenchmarkConfig)
        .join(Portfolio, PortfolioBenchmarkConfig.portfolio_id == Portfolio.id)
        .where(Portfolio.user_id == current_user["id"])
        .order_by(PortfolioBenchmarkConfig.id)
    )
    if portfolio_id is not None:
        query = query.where(PortfolioBenchmarkConfig.portfolio_id == portfolio_id)
    return ApiResponse(data=list(db.scalars(query)))


@router.get(
    "/portfolio-benchmarks/{benchmark_id}",
    response_model=ApiResponse[PortfolioBenchmarkConfigRead],
)
def get_portfolio_benchmark(
    benchmark_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PortfolioBenchmarkConfig]:
    return ApiResponse(
        data=get_owned_portfolio_child(
            db,
            PortfolioBenchmarkConfig,
            benchmark_id,
            current_user["id"],
        )
    )


@router.patch(
    "/portfolio-benchmarks/{benchmark_id}",
    response_model=ApiResponse[PortfolioBenchmarkConfigRead],
)
def update_portfolio_benchmark(
    benchmark_id: int,
    payload: PortfolioBenchmarkConfigUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PortfolioBenchmarkConfig]:
    benchmark = get_owned_portfolio_child(
        db,
        PortfolioBenchmarkConfig,
        benchmark_id,
        current_user["id"],
    )
    validate_benchmark_company(db, payload.benchmark_company_id)
    return ApiResponse(data=update_record(db, benchmark, payload))


@router.delete("/portfolio-benchmarks/{benchmark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_benchmark(
    benchmark_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> None:
    delete_record(
        db,
        get_owned_portfolio_child(
            db,
            PortfolioBenchmarkConfig,
            benchmark_id,
            current_user["id"],
        ),
    )


@router.post("/portfolio-holdings", response_model=ApiResponse[PortfolioHoldingRead], status_code=status.HTTP_201_CREATED)
def create_portfolio_holding(payload: PortfolioHoldingCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> PortfolioHolding:
    normalize_portfolio_symbol_fields(payload)
    require_owned_payload_portfolio(db, payload, current_user["id"])
    validate_portfolio_holding_refs(db, payload)
    return ApiResponse(data=create_record(db, PortfolioHolding, payload))


@router.get("/portfolio-holdings", response_model=ApiResponse[list[PortfolioHoldingRead]])
def list_portfolio_holdings(portfolio_id: int | None = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> list[PortfolioHolding]:
    query = (
        select(PortfolioHolding)
        .join(Portfolio, PortfolioHolding.portfolio_id == Portfolio.id)
        .where(Portfolio.user_id == current_user["id"])
        .order_by(PortfolioHolding.id)
    )
    if portfolio_id is not None:
        query = query.where(PortfolioHolding.portfolio_id == portfolio_id)
    return ApiResponse(data=list(db.scalars(query)))


@router.get("/portfolio-holdings/{holding_id}", response_model=ApiResponse[PortfolioHoldingRead])
def get_portfolio_holding(holding_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> PortfolioHolding:
    return ApiResponse(
        data=get_owned_portfolio_child(
            db,
            PortfolioHolding,
            holding_id,
            current_user["id"],
        )
    )


@router.patch("/portfolio-holdings/{holding_id}", response_model=ApiResponse[PortfolioHoldingRead])
def update_portfolio_holding(
    holding_id: int,
    payload: PortfolioHoldingUpdate,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
) -> PortfolioHolding:
    normalize_portfolio_symbol_fields(payload)
    holding = get_owned_portfolio_child(
        db,
        PortfolioHolding,
        holding_id,
        current_user["id"],
    )
    require_owned_payload_portfolio(db, payload, current_user["id"])
    validate_portfolio_holding_refs(db, payload)
    return ApiResponse(data=update_record(db, holding, payload))


@router.delete("/portfolio-holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_holding(holding_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> None:
    delete_record(
        db,
        get_owned_portfolio_child(
            db,
            PortfolioHolding,
            holding_id,
            current_user["id"],
        ),
    )


@router.post("/portfolio-transactions", response_model=ApiResponse[PortfolioTransactionRead], status_code=status.HTTP_201_CREATED)
def create_portfolio_transaction(
    payload: PortfolioTransactionCreate,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
) -> PortfolioTransaction:
    normalize_portfolio_symbol_fields(payload)
    require_owned_payload_portfolio(db, payload, current_user["id"])
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
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
) -> list[PortfolioTransaction]:
    query = (
        select(PortfolioTransaction)
        .join(Portfolio, PortfolioTransaction.portfolio_id == Portfolio.id)
        .where(Portfolio.user_id == current_user["id"])
        .order_by(PortfolioTransaction.id)
    )
    if portfolio_id is not None:
        query = query.where(PortfolioTransaction.portfolio_id == portfolio_id)
    return ApiResponse(data=list(db.scalars(query)))


@router.get("/portfolio-transactions/{transaction_id}", response_model=ApiResponse[PortfolioTransactionRead])
def get_portfolio_transaction(transaction_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> PortfolioTransaction:
    return ApiResponse(
        data=get_owned_portfolio_child(
            db,
            PortfolioTransaction,
            transaction_id,
            current_user["id"],
        )
    )


@router.patch("/portfolio-transactions/{transaction_id}", response_model=ApiResponse[PortfolioTransactionRead])
def update_portfolio_transaction(
    transaction_id: int,
    payload: PortfolioTransactionUpdate,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
) -> PortfolioTransaction:
    normalize_portfolio_symbol_fields(payload)
    transaction = get_owned_portfolio_child(
        db,
        PortfolioTransaction,
        transaction_id,
        current_user["id"],
    )
    require_owned_payload_portfolio(db, payload, current_user["id"])
    validate_portfolio_transaction_refs(db, payload)
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
def delete_portfolio_transaction(transaction_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> None:
    transaction = get_owned_portfolio_child(
        db,
        PortfolioTransaction,
        transaction_id,
        current_user["id"],
    )
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
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
) -> PortfolioCashBalance:
    normalize_portfolio_symbol_fields(payload)
    require_owned_payload_portfolio(db, payload, current_user["id"])
    validate_portfolio_cash_balance_refs(db, payload)
    return ApiResponse(data=create_record(db, PortfolioCashBalance, payload))


@router.get("/portfolio-cash-balances", response_model=ApiResponse[list[PortfolioCashBalanceRead]])
def list_portfolio_cash_balances(
    portfolio_id: int | None = None,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
) -> list[PortfolioCashBalance]:
    query = (
        select(PortfolioCashBalance)
        .join(Portfolio, PortfolioCashBalance.portfolio_id == Portfolio.id)
        .where(Portfolio.user_id == current_user["id"])
        .order_by(PortfolioCashBalance.id)
    )
    if portfolio_id is not None:
        query = query.where(PortfolioCashBalance.portfolio_id == portfolio_id)
    return ApiResponse(data=list(db.scalars(query)))


@router.get("/portfolio-cash-balances/{cash_balance_id}", response_model=ApiResponse[PortfolioCashBalanceRead])
def get_portfolio_cash_balance(cash_balance_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> PortfolioCashBalance:
    return ApiResponse(
        data=get_owned_portfolio_child(
            db,
            PortfolioCashBalance,
            cash_balance_id,
            current_user["id"],
        )
    )


@router.patch("/portfolio-cash-balances/{cash_balance_id}", response_model=ApiResponse[PortfolioCashBalanceRead])
def update_portfolio_cash_balance(
    cash_balance_id: int,
    payload: PortfolioCashBalanceUpdate,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
) -> PortfolioCashBalance:
    normalize_portfolio_symbol_fields(payload)
    cash_balance = get_owned_portfolio_child(
        db,
        PortfolioCashBalance,
        cash_balance_id,
        current_user["id"],
    )
    require_owned_payload_portfolio(db, payload, current_user["id"])
    validate_portfolio_cash_balance_refs(db, payload)
    return ApiResponse(data=update_record(db, cash_balance, payload))


@router.delete("/portfolio-cash-balances/{cash_balance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_cash_balance(cash_balance_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> None:
    delete_record(
        db,
        get_owned_portfolio_child(
            db,
            PortfolioCashBalance,
            cash_balance_id,
            current_user["id"],
        ),
    )


@router.post("/portfolio-snapshots", response_model=ApiResponse[PortfolioSnapshotRead], status_code=status.HTTP_201_CREATED)
def create_portfolio_snapshot(payload: PortfolioSnapshotCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> PortfolioSnapshot:
    require_owned_payload_portfolio(db, payload, current_user["id"])
    validate_portfolio_snapshot_refs(db, payload)
    return ApiResponse(data=create_record(db, PortfolioSnapshot, payload))


@router.get("/portfolio-snapshots", response_model=ApiResponse[list[PortfolioSnapshotRead]])
def list_portfolio_snapshots(
    portfolio_id: int | None = None,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
) -> list[PortfolioSnapshot]:
    query = (
        select(PortfolioSnapshot)
        .join(Portfolio, PortfolioSnapshot.portfolio_id == Portfolio.id)
        .where(Portfolio.user_id == current_user["id"])
        .order_by(PortfolioSnapshot.id)
    )
    if portfolio_id is not None:
        query = query.where(PortfolioSnapshot.portfolio_id == portfolio_id)
    return ApiResponse(data=list(db.scalars(query)))


@router.get("/portfolio-snapshots/{snapshot_id}", response_model=ApiResponse[PortfolioSnapshotRead])
def get_portfolio_snapshot(snapshot_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> PortfolioSnapshot:
    return ApiResponse(
        data=get_owned_portfolio_child(
            db,
            PortfolioSnapshot,
            snapshot_id,
            current_user["id"],
        )
    )


@router.patch("/portfolio-snapshots/{snapshot_id}", response_model=ApiResponse[PortfolioSnapshotRead])
def update_portfolio_snapshot(
    snapshot_id: int,
    payload: PortfolioSnapshotUpdate,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
) -> PortfolioSnapshot:
    snapshot = get_owned_portfolio_child(
        db,
        PortfolioSnapshot,
        snapshot_id,
        current_user["id"],
    )
    require_owned_payload_portfolio(db, payload, current_user["id"])
    validate_portfolio_snapshot_refs(db, payload)
    return ApiResponse(data=update_record(db, snapshot, payload))


@router.delete("/portfolio-snapshots/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_snapshot(snapshot_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> None:
    delete_record(
        db,
        get_owned_portfolio_child(
            db,
            PortfolioSnapshot,
            snapshot_id,
            current_user["id"],
        ),
    )


@router.post(
    "/portfolios/{portfolio_id}/snapshots/capture",
    response_model=ApiResponse[PortfolioSnapshotRead],
)
def capture_portfolio_snapshot(
    portfolio_id: int,
    as_of_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PortfolioSnapshot]:
    get_owned_portfolio(db, portfolio_id, current_user["id"])
    snapshot = record_daily_snapshot(db, portfolio_id, as_of_date)
    warnings = []
    if snapshot.calculation_status != "complete":
        warnings.append(
            "Snapshot is incomplete and cannot be used for precise performance calculations."
        )
    return ApiResponse(
        data=snapshot,
        meta={
            "source": "point_in_time_portfolio_capture",
            "last_updated": snapshot.created_at,
            "is_stale": snapshot.calculation_status != "complete",
            "warnings": warnings,
            "confidence": "high" if snapshot.calculation_status == "complete" else "low",
        },
    )


@router.get("/portfolios/{portfolio_id}/valuation", response_model=ApiResponse[PortfolioValuationRead])
def get_portfolio_valuation(
    portfolio_id: int,
    as_of_date: date | None = None,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
) -> dict:
    get_owned_portfolio(db, portfolio_id, current_user["id"])
    try:
        return ApiResponse(
            data=calculate_portfolio_valuation(
                db,
                portfolio_id,
                as_of_date,
                user_id=current_user["id"],
            )
        )
    except ValueError as exc:
        raise PublicApiError(
            status_code=404,
            code="PORTFOLIO_VALUATION_DATA_NOT_FOUND",
            message="Portfolio valuation data was not found for the requested date.",
        ) from exc


@router.get("/portfolios/{portfolio_id}/analytics", response_model=ApiResponse[PortfolioAnalyticsRead])
def get_portfolio_analytics(
    portfolio_id: int,
    as_of_date: date | None = None,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
) -> dict:
    get_owned_portfolio(db, portfolio_id, current_user["id"])
    try:
        return ApiResponse(
            data=calculate_portfolio_analytics(
                db,
                portfolio_id,
                as_of_date,
                user_id=current_user["id"],
            )
        )
    except ValueError as exc:
        raise PublicApiError(
            status_code=404,
            code="PORTFOLIO_ANALYTICS_DATA_NOT_FOUND",
            message="Portfolio analytics data was not found for the requested date.",
        ) from exc


@router.get("/portfolios/{portfolio_id}/attribution", response_model=ApiResponse[PortfolioAttributionRead])
def get_portfolio_attribution(
    portfolio_id: int,
    as_of_date: date | None = None,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
) -> dict:
    get_owned_portfolio(db, portfolio_id, current_user["id"])
    try:
        attribution_data = PortfolioAttributionEngine.decompose_performance(
            db,
            portfolio_id,
            as_of_date
        )
        return ApiResponse(data=attribution_data)
    except ValueError as exc:
        raise PublicApiError(
            status_code=404,
            code="PORTFOLIO_ATTRIBUTION_DATA_NOT_FOUND",
            message="Portfolio attribution data was not found for the requested date.",
        ) from exc


@router.get(
    "/portfolios/{portfolio_id}/performance",
    response_model=ApiResponse[PortfolioPerformanceRead],
)
def get_portfolio_performance(
    portfolio_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict]:
    get_owned_portfolio(db, portfolio_id, current_user["id"])
    if end_date <= start_date:
        raise HTTPException(status_code=422, detail="end_date must be after start_date")
    twr = calculate_time_weighted_return(db, portfolio_id, start_date, end_date)
    mwr = calculate_money_weighted_return(db, portfolio_id, end_date)
    return ApiResponse(
        data={
            "portfolio_id": portfolio_id,
            "requested_start_date": start_date,
            "requested_end_date": end_date,
            "time_weighted_return": twr,
            "money_weighted_return": mwr,
        }
    )


@router.get(
    "/portfolios/{portfolio_id}/period-attribution",
    response_model=ApiResponse[PortfolioPeriodAttributionRead],
)
def get_portfolio_period_attribution(
    portfolio_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict]:
    get_owned_portfolio(db, portfolio_id, current_user["id"])
    if end_date <= start_date:
        raise HTTPException(status_code=422, detail="end_date must be after start_date")
    return ApiResponse(data=calculate_period_attribution(db, portfolio_id, start_date, end_date))


@router.get(
    "/portfolios/{portfolio_id}/opportunity-cost",
    response_model=ApiResponse[PortfolioOpportunityCostRead],
)
def get_portfolio_opportunity_cost(
    portfolio_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict]:
    get_owned_portfolio(db, portfolio_id, current_user["id"])
    if end_date <= start_date:
        raise HTTPException(status_code=422, detail="end_date must be after start_date")
    result = calculate_benchmark_opportunity_cost(db, portfolio_id, start_date, end_date)
    return ApiResponse(
        data=result,
        meta={
            "source": "configured_portfolio_benchmark",
            "is_stale": result["calculation_status"] != "complete",
            "warnings": result["warnings"],
            "confidence": "high" if result["calculation_status"] == "complete" else "low",
        },
    )


@router.get(
    "/portfolios/{portfolio_id}/risk-return-comparison",
    response_model=ApiResponse[PortfolioRiskReturnRead],
)
def get_portfolio_risk_return_comparison(
    portfolio_id: int,
    as_of_date: date | None = None,
    lookback_days: int = Query(default=365, ge=30, le=3650),
    min_observations: int = Query(default=20, ge=2, le=2520),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict]:
    get_owned_portfolio(db, portfolio_id, current_user["id"])
    result = calculate_portfolio_risk_return(
        db,
        portfolio_id,
        as_of_date,
        lookback_days=lookback_days,
        min_observations=min_observations,
        user_id=current_user["id"],
    )
    return ApiResponse(
        data=result,
        meta={
            "source": "historical_market_prices_fx_and_trust_gated_dcf",
            "is_mock": result["contains_mock_data"],
            "is_stale": result["calculation_status"] != "complete",
            "warnings": [*result["warnings"], *result["blockers"]],
            "confidence": (
                "high"
                if result["calculation_status"] == "complete"
                else "medium"
                if result["calculation_status"] == "partial"
                else "low"
            ),
        },
    )


@router.get(
    "/portfolios/{portfolio_id}/real-input-readiness",
    response_model=ApiResponse[PortfolioRealInputReadinessRead],
)
def get_portfolio_real_input_readiness(
    portfolio_id: int,
    min_observations: int = Query(default=20, ge=2, le=2520),
    lookback_days: int = Query(default=365, ge=30, le=3650),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict]:
    get_owned_portfolio(db, portfolio_id, current_user["id"])
    result = audit_portfolio_real_input_readiness(
        db,
        portfolio_id,
        user_id=current_user["id"],
        min_observations=min_observations,
        lookback_days=lookback_days,
    )
    return ApiResponse(
        data=result,
        meta={
            "source": "persisted_portfolio_inputs",
            "is_mock": result["contains_mock_data"],
            "is_stale": False,
            "warnings": result["warnings"],
            "confidence": "high",
        },
    )
