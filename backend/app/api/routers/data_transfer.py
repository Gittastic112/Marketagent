import csv
import logging
from io import StringIO
from typing import Any, Iterable

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_current_user
from app.api.schemas import ApiResponse
from app.core.security import escape_csv_formula
from app.db.session import get_db
from app.models import (
    Event,
    MarketPrice,
    Portfolio,
    PortfolioHolding,
    PortfolioTransaction,
    RawDocument,
)
from app.services.data_transfer import (
    parse_market_price_rows,
    parse_portfolio_holding_rows,
    parse_portfolio_transaction_rows,
    preview_payload,
    read_csv,
    reject_invalid_rows,
)
from app.services.portfolio_holdings import (
    apply_transaction_to_cash,
    apply_transaction_to_holding,
)


router = APIRouter()
logger = logging.getLogger(__name__)


def _csv_response(
    filename: str,
    headers: list[str],
    rows: Iterable[Iterable[Any]],
) -> Response:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "no-store",
        },
    )


@router.get("/export/portfolio-holdings")
def export_portfolio_holdings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Response:
    holdings = db.scalars(
        select(PortfolioHolding)
        .join(Portfolio, PortfolioHolding.portfolio_id == Portfolio.id)
        .where(Portfolio.user_id == current_user["id"])
        .order_by(PortfolioHolding.id)
    ).all()
    return _csv_response(
        "portfolio_holdings.csv",
        [
            "portfolio_id",
            "company_id",
            "ticker",
            "quantity",
            "average_cost",
            "currency",
            "as_of_date",
        ],
        (
            (
                holding.portfolio_id,
                holding.company_id or "",
                escape_csv_formula(holding.ticker),
                holding.quantity,
                holding.average_cost,
                escape_csv_formula(holding.currency),
                holding.as_of_date.isoformat(),
            )
            for holding in holdings
        ),
    )


@router.get("/export/portfolio-transactions")
def export_portfolio_transactions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Response:
    transactions = db.scalars(
        select(PortfolioTransaction)
        .join(Portfolio, PortfolioTransaction.portfolio_id == Portfolio.id)
        .where(Portfolio.user_id == current_user["id"])
        .order_by(PortfolioTransaction.id)
    ).all()
    return _csv_response(
        "portfolio_transactions.csv",
        [
            "portfolio_id",
            "company_id",
            "ticker",
            "transaction_type",
            "quantity",
            "price",
            "fees",
            "currency",
            "transaction_date",
            "notes",
        ],
        (
            (
                transaction.portfolio_id,
                transaction.company_id or "",
                escape_csv_formula(transaction.ticker),
                escape_csv_formula(transaction.transaction_type),
                transaction.quantity,
                transaction.price,
                transaction.fees,
                escape_csv_formula(transaction.currency),
                transaction.transaction_date.isoformat(),
                escape_csv_formula(transaction.notes),
            )
            for transaction in transactions
        ),
    )


@router.get("/export/market-prices")
def export_market_prices(db: Session = Depends(get_db)) -> Response:
    prices = db.scalars(select(MarketPrice).order_by(MarketPrice.id)).all()
    return _csv_response(
        "market_prices.csv",
        [
            "company_id",
            "ticker",
            "price",
            "currency",
            "as_of_date",
            "source_name",
        ],
        (
            (
                price.company_id or "",
                escape_csv_formula(price.ticker),
                price.price,
                escape_csv_formula(price.currency),
                price.as_of_date.isoformat(),
                "manual",
            )
            for price in prices
        ),
    )


@router.get("/export/raw-documents")
def export_raw_documents(db: Session = Depends(get_db)) -> Response:
    documents = db.scalars(
        select(RawDocument)
        .options(selectinload(RawDocument.source))
        .order_by(RawDocument.id)
    ).all()
    return _csv_response(
        "raw_documents.csv",
        [
            "id",
            "company_id",
            "source_name",
            "source_type",
            "url",
            "published_at",
            "ingested_at",
            "content_hash",
        ],
        (
            (
                document.id,
                document.company_id or "",
                escape_csv_formula(document.source.name if document.source else ""),
                escape_csv_formula(
                    document.source.source_type if document.source else ""
                ),
                escape_csv_formula(document.url),
                document.published_at.isoformat() if document.published_at else "",
                document.ingested_at.isoformat() if document.ingested_at else "",
                escape_csv_formula(document.content_hash),
            )
            for document in documents
        ),
    )


@router.get("/export/events")
def export_events(db: Session = Depends(get_db)) -> Response:
    events = db.scalars(select(Event).order_by(Event.id)).all()
    return _csv_response(
        "events.csv",
        [
            "id",
            "company_id",
            "raw_document_id",
            "event_type",
            "title",
            "description",
            "event_time",
            "credibility_score",
            "novelty_score",
            "impact_score",
            "priority_score",
        ],
        (
            (
                event.id,
                event.company_id or "",
                event.raw_document_id or "",
                escape_csv_formula(event.event_type),
                escape_csv_formula(event.title),
                escape_csv_formula(event.description),
                event.event_time.isoformat() if event.event_time else "",
                event.credibility_score if event.credibility_score is not None else "",
                event.novelty_score if event.novelty_score is not None else "",
                event.impact_score if event.impact_score is not None else "",
                event.priority_score if event.priority_score is not None else "",
            )
            for event in events
        ),
    )


@router.post("/import/market-prices")
def import_market_prices(
    preview: bool = False,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, Any]]:
    rows = read_csv(
        file,
        required_fields={"ticker", "price", "currency", "as_of_date"},
    )
    row_results, records = parse_market_price_rows(db, rows)
    if preview:
        return ApiResponse(data=preview_payload(row_results, len(records)))
    reject_invalid_rows(row_results)
    try:
        db.add_all(records)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Market price CSV import failed")
        raise HTTPException(
            status_code=400,
            detail="Market price import could not be applied",
        ) from None
    return ApiResponse(data={"status": "ok", "imported_count": len(records)})


@router.post("/import/portfolio-transactions")
def import_portfolio_transactions(
    preview: bool = False,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict[str, Any]]:
    rows = read_csv(
        file,
        required_fields={
            "portfolio_id",
            "ticker",
            "transaction_type",
            "quantity",
            "price",
            "currency",
            "transaction_date",
        },
    )
    row_results, records = parse_portfolio_transaction_rows(
        db,
        rows,
        user_id=current_user["id"],
    )
    if preview:
        return ApiResponse(data=preview_payload(row_results, len(records)))
    reject_invalid_rows(row_results)
    try:
        for transaction in records:
            db.add(transaction)
            db.flush()
            apply_transaction_to_holding(db, transaction)
            apply_transaction_to_cash(db, transaction)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Portfolio transaction CSV import failed")
        raise HTTPException(
            status_code=400,
            detail="Portfolio transaction import could not be applied",
        ) from None
    return ApiResponse(data={"status": "ok", "imported_count": len(records)})


@router.post("/import/portfolio-holdings")
def import_portfolio_holdings(
    preview: bool = False,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict[str, Any]]:
    rows = read_csv(
        file,
        required_fields={
            "portfolio_id",
            "ticker",
            "quantity",
            "average_cost",
            "currency",
            "as_of_date",
        },
    )
    row_results, records = parse_portfolio_holding_rows(
        db,
        rows,
        user_id=current_user["id"],
    )
    if preview:
        return ApiResponse(data=preview_payload(row_results, len(records)))
    reject_invalid_rows(row_results)
    try:
        db.add_all(records)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Portfolio holding CSV import failed")
        raise HTTPException(
            status_code=400,
            detail="Portfolio holding import could not be applied",
        ) from None
    return ApiResponse(data={"status": "ok", "imported_count": len(records)})
