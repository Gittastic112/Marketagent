import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import Any

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Company,
    MarketPrice,
    Portfolio,
    PortfolioHolding,
    PortfolioTransaction,
)


MAX_CSV_BYTES = 2 * 1024 * 1024
MAX_CSV_ROWS = 5_000
ALLOWED_TRANSACTION_TYPES = {
    "buy",
    "sell",
    "dividend",
    "split",
    "bonus",
    "deposit",
    "withdrawal",
    "fee",
    "tax",
    "manual_adjustment",
}


def read_csv(
    file: UploadFile,
    *,
    required_fields: set[str],
) -> list[dict[str, str]]:
    filename = (file.filename or "").lower()
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Must be a CSV file")

    content = file.file.read(MAX_CSV_BYTES + 1)
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(status_code=413, detail="CSV file exceeds the size limit")
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV must use UTF-8 encoding") from None

    reader = csv.DictReader(StringIO(decoded))
    fieldnames = set(reader.fieldnames or [])
    missing_fields = sorted(required_fields - fieldnames)
    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail=f"CSV is missing required columns: {', '.join(missing_fields)}",
        )

    rows: list[dict[str, str]] = []
    for row in reader:
        if len(rows) >= MAX_CSV_ROWS:
            raise HTTPException(status_code=400, detail="CSV exceeds the row limit")
        rows.append({key: value or "" for key, value in row.items() if key is not None})
    return rows


def preview_payload(
    row_results: list[dict[str, Any]],
    valid_count: int,
) -> dict[str, Any]:
    return {
        "is_preview": True,
        "total_rows": len(row_results),
        "valid_count": valid_count,
        "error_count": len(row_results) - valid_count,
        "rows": row_results,
    }


def reject_invalid_rows(row_results: list[dict[str, Any]]) -> None:
    invalid = [row for row in row_results if not row["is_valid"]]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "CSV contains errors",
                "errors": invalid,
            },
        )


def _row_error(
    row_index: int,
    field: str,
    message: str,
) -> dict[str, Any]:
    return {
        "row_index": row_index,
        "field": field,
        "message": message,
    }


def _cell(row: dict[str, str], field: str) -> str:
    value = row.get(field, "").strip()
    if len(value) >= 2 and value[0] == "'" and value[1] in "=+-@\t\r":
        value = value[1:]
    return value


def _parse_int(
    row: dict[str, str],
    field: str,
    row_index: int,
    errors: list[dict[str, Any]],
    *,
    required: bool,
) -> int | None:
    value = _cell(row, field)
    if not value:
        if required:
            errors.append(_row_error(row_index, field, "Required field missing"))
        return None
    try:
        parsed = int(value)
    except ValueError:
        errors.append(_row_error(row_index, field, "Invalid integer"))
        return None
    if parsed <= 0:
        errors.append(_row_error(row_index, field, "Must be greater than zero"))
        return None
    return parsed


def _parse_decimal(
    row: dict[str, str],
    field: str,
    row_index: int,
    errors: list[dict[str, Any]],
    *,
    default: str | None = None,
    strictly_positive: bool = False,
) -> Decimal | None:
    value = _cell(row, field)
    if not value and default is not None:
        value = default
    if not value:
        errors.append(_row_error(row_index, field, "Required field missing"))
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        errors.append(_row_error(row_index, field, "Invalid decimal"))
        return None
    if not parsed.is_finite():
        errors.append(_row_error(row_index, field, "Decimal must be finite"))
        return None
    if strictly_positive and parsed <= 0:
        errors.append(_row_error(row_index, field, "Must be greater than zero"))
        return None
    if not strictly_positive and parsed < 0:
        errors.append(_row_error(row_index, field, "Must be zero or greater"))
        return None
    return parsed


def _parse_date(
    row: dict[str, str],
    field: str,
    row_index: int,
    errors: list[dict[str, Any]],
) -> date | None:
    value = _cell(row, field)
    if not value:
        errors.append(_row_error(row_index, field, "Required field missing"))
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(
            _row_error(
                row_index,
                field,
                "Invalid date format, expected YYYY-MM-DD",
            )
        )
        return None


def _parse_symbol(
    row: dict[str, str],
    field: str,
    row_index: int,
    errors: list[dict[str, Any]],
    *,
    max_length: int,
) -> str | None:
    value = _cell(row, field).upper()
    if not value:
        errors.append(_row_error(row_index, field, "Required field missing"))
        return None
    if len(value) > max_length:
        errors.append(
            _row_error(
                row_index,
                field,
                f"Must be {max_length} characters or fewer",
            )
        )
        return None
    if value.startswith(("=", "+", "-", "@", "\t", "\r")):
        errors.append(_row_error(row_index, field, "Invalid leading character"))
        return None
    return value


def _parse_currency(
    row: dict[str, str],
    row_index: int,
    errors: list[dict[str, Any]],
) -> str | None:
    value = _cell(row, "currency").upper() or "USD"
    if not value.isalpha() or not 3 <= len(value) <= 10:
        errors.append(
            _row_error(
                row_index,
                "currency",
                "Currency must contain 3 to 10 letters",
            )
        )
        return None
    return value


def _validate_company(
    db: Session,
    company_id: int | None,
    row_index: int,
    errors: list[dict[str, Any]],
) -> None:
    if company_id is not None and db.get(Company, company_id) is None:
        errors.append(_row_error(row_index, "company_id", "Company not found"))


def _validate_owned_portfolio(
    db: Session,
    portfolio_id: int | None,
    user_id: str,
    row_index: int,
    errors: list[dict[str, Any]],
) -> None:
    if portfolio_id is None:
        return
    portfolio = db.scalar(
        select(Portfolio).where(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id,
        )
    )
    if portfolio is None:
        errors.append(_row_error(row_index, "portfolio_id", "Portfolio not found"))


def _row_result(
    row_index: int,
    row: dict[str, str],
    errors: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "row_index": row_index,
        "data": row,
        "is_valid": not errors,
        "errors": errors,
    }


def parse_market_price_rows(
    db: Session,
    rows: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[MarketPrice]]:
    row_results: list[dict[str, Any]] = []
    records: list[MarketPrice] = []
    seen: set[tuple[str, date]] = set()

    for row_index, row in enumerate(rows, start=2):
        errors: list[dict[str, Any]] = []
        company_id = _parse_int(
            row,
            "company_id",
            row_index,
            errors,
            required=False,
        )
        ticker = _parse_symbol(
            row,
            "ticker",
            row_index,
            errors,
            max_length=20,
        )
        price = _parse_decimal(
            row,
            "price",
            row_index,
            errors,
            strictly_positive=True,
        )
        currency = _parse_currency(row, row_index, errors)
        as_of_date = _parse_date(row, "as_of_date", row_index, errors)
        _validate_company(db, company_id, row_index, errors)

        if ticker is not None and as_of_date is not None:
            key = (ticker, as_of_date)
            duplicate = key in seen or db.scalar(
                select(MarketPrice.id).where(
                    MarketPrice.ticker == ticker,
                    MarketPrice.as_of_date == as_of_date,
                )
            )
            if duplicate:
                errors.append(_row_error(row_index, "duplicate", "Record already exists"))
            seen.add(key)

        if not errors:
            records.append(
                MarketPrice(
                    company_id=company_id,
                    ticker=ticker,
                    price=price,
                    currency=currency,
                    as_of_date=as_of_date,
                )
            )
        row_results.append(_row_result(row_index, row, errors))
    return row_results, records


def parse_portfolio_transaction_rows(
    db: Session,
    rows: list[dict[str, str]],
    *,
    user_id: str,
) -> tuple[list[dict[str, Any]], list[PortfolioTransaction]]:
    row_results: list[dict[str, Any]] = []
    records: list[PortfolioTransaction] = []
    seen: set[tuple[Any, ...]] = set()

    for row_index, row in enumerate(rows, start=2):
        errors: list[dict[str, Any]] = []
        portfolio_id = _parse_int(
            row,
            "portfolio_id",
            row_index,
            errors,
            required=True,
        )
        company_id = _parse_int(
            row,
            "company_id",
            row_index,
            errors,
            required=False,
        )
        ticker = _parse_symbol(
            row,
            "ticker",
            row_index,
            errors,
            max_length=20,
        )
        transaction_type = _cell(row, "transaction_type").lower()
        if transaction_type not in ALLOWED_TRANSACTION_TYPES:
            errors.append(
                _row_error(
                    row_index,
                    "transaction_type",
                    "Unsupported transaction type",
                )
            )
        quantity = _parse_decimal(
            row,
            "quantity",
            row_index,
            errors,
            default="0",
        )
        price = _parse_decimal(
            row,
            "price",
            row_index,
            errors,
            default="0",
        )
        fees = _parse_decimal(
            row,
            "fees",
            row_index,
            errors,
            default="0",
        )
        currency = _parse_currency(row, row_index, errors)
        transaction_date = _parse_date(
            row,
            "transaction_date",
            row_index,
            errors,
        )
        notes = _cell(row, "notes") or None
        if notes is not None and len(notes) > 10_000:
            errors.append(
                _row_error(
                    row_index,
                    "notes",
                    "Must be 10000 characters or fewer",
                )
            )

        _validate_owned_portfolio(db, portfolio_id, user_id, row_index, errors)
        _validate_company(db, company_id, row_index, errors)

        if (
            portfolio_id is not None
            and ticker is not None
            and transaction_date is not None
            and quantity is not None
            and price is not None
        ):
            key = (
                portfolio_id,
                ticker,
                transaction_type,
                transaction_date,
                quantity,
                price,
            )
            duplicate = key in seen or db.scalar(
                select(PortfolioTransaction.id).where(
                    PortfolioTransaction.portfolio_id == portfolio_id,
                    PortfolioTransaction.ticker == ticker,
                    PortfolioTransaction.transaction_type == transaction_type,
                    PortfolioTransaction.transaction_date == transaction_date,
                    PortfolioTransaction.quantity == quantity,
                    PortfolioTransaction.price == price,
                )
            )
            if duplicate:
                errors.append(_row_error(row_index, "duplicate", "Record already exists"))
            seen.add(key)

        if not errors:
            records.append(
                PortfolioTransaction(
                    portfolio_id=portfolio_id,
                    company_id=company_id,
                    ticker=ticker,
                    transaction_type=transaction_type,
                    quantity=quantity,
                    price=price,
                    fees=fees,
                    currency=currency,
                    transaction_date=transaction_date,
                    notes=notes,
                )
            )
        row_results.append(_row_result(row_index, row, errors))
    return row_results, records


def parse_portfolio_holding_rows(
    db: Session,
    rows: list[dict[str, str]],
    *,
    user_id: str,
) -> tuple[list[dict[str, Any]], list[PortfolioHolding]]:
    row_results: list[dict[str, Any]] = []
    records: list[PortfolioHolding] = []
    seen: set[tuple[int, str, date]] = set()

    for row_index, row in enumerate(rows, start=2):
        errors: list[dict[str, Any]] = []
        portfolio_id = _parse_int(
            row,
            "portfolio_id",
            row_index,
            errors,
            required=True,
        )
        company_id = _parse_int(
            row,
            "company_id",
            row_index,
            errors,
            required=False,
        )
        ticker = _parse_symbol(
            row,
            "ticker",
            row_index,
            errors,
            max_length=20,
        )
        quantity = _parse_decimal(
            row,
            "quantity",
            row_index,
            errors,
            default="0",
        )
        average_cost = _parse_decimal(
            row,
            "average_cost",
            row_index,
            errors,
            default="0",
        )
        currency = _parse_currency(row, row_index, errors)
        as_of_date = _parse_date(row, "as_of_date", row_index, errors)
        _validate_owned_portfolio(db, portfolio_id, user_id, row_index, errors)
        _validate_company(db, company_id, row_index, errors)

        if (
            portfolio_id is not None
            and ticker is not None
            and as_of_date is not None
        ):
            key = (portfolio_id, ticker, as_of_date)
            duplicate = key in seen or db.scalar(
                select(PortfolioHolding.id).where(
                    PortfolioHolding.portfolio_id == portfolio_id,
                    PortfolioHolding.ticker == ticker,
                    PortfolioHolding.as_of_date == as_of_date,
                )
            )
            if duplicate:
                errors.append(_row_error(row_index, "duplicate", "Record already exists"))
            seen.add(key)

        if not errors:
            records.append(
                PortfolioHolding(
                    portfolio_id=portfolio_id,
                    company_id=company_id,
                    ticker=ticker,
                    quantity=quantity,
                    average_cost=average_cost,
                    currency=currency,
                    as_of_date=as_of_date,
                )
            )
        row_results.append(_row_result(row_index, row, errors))
    return row_results, records
