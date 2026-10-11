from __future__ import annotations

import csv
import ipaddress
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from io import StringIO
from typing import Any, Literal
from urllib.parse import urlsplit

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Company,
    FxRateObservation,
    MarketPrice,
    Portfolio,
    PortfolioBenchmarkConfig,
    PortfolioHolding,
)


MAX_EVIDENCE_BYTES = 2 * 1024 * 1024
MAX_EVIDENCE_ROWS = 5_000
EVIDENCE_COLUMNS = [
    "record_type",
    "ticker",
    "price",
    "currency",
    "base_currency",
    "quote_currency",
    "rate",
    "as_of_date",
    "provider_name",
    "provider_symbol",
    "source_url",
    "source_timestamp",
    "price_type",
]
ALLOWED_PRICE_TYPES = {"close", "adjusted_close", "official_close", "nav"}
GENERIC_PROVIDER_NAMES = {"manual", "unknown", "legacy_unknown", "n/a", "na"}
MOCK_MARKERS = ("mock data", "mock_fixture", "e2e_mock", "synthetic fixture")


@dataclass(frozen=True)
class EvidenceFile:
    filename: str
    content_sha256: str
    byte_size: int
    rows: list[dict[str, str]]


@dataclass(frozen=True)
class EvidenceScope:
    portfolio: Portfolio
    companies_by_ticker: dict[str, Company]
    price_currency_by_ticker: dict[str, str]
    allowed_fx_pairs: set[tuple[str, str]]
    holding_tickers: set[str]
    benchmark_ticker: str | None


@dataclass(frozen=True)
class NormalizedEvidenceRow:
    row_index: int
    record_type: Literal["market_price", "fx_rate"]
    values: dict[str, Any]
    identity: tuple[Any, ...]


def evidence_template_csv() -> str:
    output = StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(EVIDENCE_COLUMNS)
    writer.writerow(
        [
            "market_price",
            "HELD_TICKER",
            "100.25",
            "USD",
            "",
            "",
            "",
            "2026-08-21",
            "Named exchange or data provider",
            "PROVIDER_SYMBOL",
            "https://provider.example/history",
            "2026-08-21T21:00:00Z",
            "adjusted_close",
        ]
    )
    writer.writerow(
        [
            "fx_rate",
            "",
            "",
            "",
            "INR",
            "USD",
            "0.01145",
            "2026-08-21",
            "Named central bank or data provider",
            "INRUSD",
            "https://provider.example/fx-history",
            "2026-08-21T21:00:00Z",
            "",
        ]
    )
    return output.getvalue()


def read_evidence_file(file: UploadFile) -> EvidenceFile:
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Evidence bundle must be a CSV file")
    content = file.file.read(MAX_EVIDENCE_BYTES + 1)
    if len(content) > MAX_EVIDENCE_BYTES:
        raise HTTPException(status_code=413, detail="Evidence bundle exceeds the 2 MiB size limit")
    if not content:
        raise HTTPException(status_code=400, detail="Evidence bundle is empty")
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Evidence bundle must use UTF-8 encoding") from None

    reader = csv.DictReader(StringIO(decoded), strict=True)
    headers = reader.fieldnames or []
    if len(headers) != len(set(headers)):
        raise HTTPException(status_code=400, detail="Evidence bundle contains duplicate column names")
    missing = [column for column in EVIDENCE_COLUMNS if column not in headers]
    unexpected = [column for column in headers if column not in EVIDENCE_COLUMNS]
    if missing or unexpected:
        parts = []
        if missing:
            parts.append(f"missing columns: {', '.join(missing)}")
        if unexpected:
            parts.append(f"unexpected columns: {', '.join(unexpected)}")
        raise HTTPException(status_code=400, detail="Evidence bundle has invalid headers; " + "; ".join(parts))

    rows: list[dict[str, str]] = []
    try:
        for row in reader:
            if len(rows) >= MAX_EVIDENCE_ROWS:
                raise HTTPException(status_code=400, detail="Evidence bundle exceeds the 5000 row limit")
            normalized = {column: (row.get(column) or "").strip() for column in EVIDENCE_COLUMNS}
            if not any(normalized.values()):
                continue
            rows.append(normalized)
    except csv.Error:
        raise HTTPException(status_code=400, detail="Evidence bundle contains malformed CSV") from None
    if not rows:
        raise HTTPException(status_code=400, detail="Evidence bundle contains no data rows")
    return EvidenceFile(
        filename=filename,
        content_sha256=sha256(content).hexdigest(),
        byte_size=len(content),
        rows=rows,
    )


def resolve_evidence_scope(db: Session, portfolio_id: int, *, user_id: str) -> EvidenceScope:
    portfolio = db.scalar(
        select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
    )
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    holdings = list(
        db.scalars(
            select(PortfolioHolding).where(
                PortfolioHolding.portfolio_id == portfolio_id,
                PortfolioHolding.quantity > 0,
            )
        )
    )
    benchmark = db.scalar(
        select(PortfolioBenchmarkConfig)
        .where(
            PortfolioBenchmarkConfig.portfolio_id == portfolio_id,
            PortfolioBenchmarkConfig.active.is_(True),
        )
        .order_by(PortfolioBenchmarkConfig.id)
    )
    companies_by_ticker: dict[str, Company] = {}
    price_currency_by_ticker: dict[str, str] = {}
    holding_tickers: set[str] = set()
    foreign_currencies: set[str] = set()
    portfolio_currency = portfolio.base_currency.strip().upper()

    for holding in holdings:
        ticker = holding.ticker.strip().upper()
        holding_tickers.add(ticker)
        currency = holding.currency.strip().upper()
        price_currency_by_ticker[ticker] = currency
        if currency != portfolio_currency:
            foreign_currencies.add(currency)
        if holding.company_id is not None:
            company = db.get(Company, holding.company_id)
            if company is not None:
                companies_by_ticker[ticker] = company

    benchmark_ticker: str | None = None
    if benchmark is not None:
        benchmark_ticker = benchmark.ticker.strip().upper()
        price_currency_by_ticker[benchmark_ticker] = benchmark.currency.strip().upper()
        if benchmark.currency.strip().upper() != portfolio_currency:
            foreign_currencies.add(benchmark.currency.strip().upper())
        company = (
            db.get(Company, benchmark.benchmark_company_id)
            if benchmark.benchmark_company_id is not None
            else db.scalar(
                select(Company).where(Company.ticker == benchmark_ticker).order_by(Company.id)
            )
        )
        if company is not None:
            companies_by_ticker[benchmark_ticker] = company

    allowed_fx_pairs = {
        pair
        for currency in foreign_currencies
        for pair in ((currency, portfolio_currency), (portfolio_currency, currency))
    }
    return EvidenceScope(
        portfolio=portfolio,
        companies_by_ticker=companies_by_ticker,
        price_currency_by_ticker=price_currency_by_ticker,
        allowed_fx_pairs=allowed_fx_pairs,
        holding_tickers=holding_tickers,
        benchmark_ticker=benchmark_ticker,
    )


def _error(row_index: int, field: str, message: str) -> dict[str, Any]:
    return {"row_index": row_index, "field": field, "message": message}


def _mock_marked(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in MOCK_MARKERS)


def _parse_positive_decimal(value: str, *, row_index: int, field: str, errors: list[dict[str, Any]]) -> Decimal | None:
    if not value:
        errors.append(_error(row_index, field, "Required field missing"))
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        errors.append(_error(row_index, field, "Invalid decimal"))
        return None
    if not parsed.is_finite() or parsed <= 0:
        errors.append(_error(row_index, field, "Must be a finite value greater than zero"))
        return None
    return parsed


def _parse_date(value: str, *, row_index: int, errors: list[dict[str, Any]]) -> date | None:
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        errors.append(_error(row_index, "as_of_date", "Expected an ISO date in YYYY-MM-DD format"))
        return None
    if parsed > date.today():
        errors.append(_error(row_index, "as_of_date", "Future-dated evidence is not allowed"))
        return None
    return parsed


def _parse_timestamp(value: str, *, row_index: int, errors: list[dict[str, Any]]) -> datetime | None:
    if not value:
        errors.append(_error(row_index, "source_timestamp", "Required field missing"))
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(_error(row_index, "source_timestamp", "Expected an ISO 8601 timestamp"))
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(_error(row_index, "source_timestamp", "Timestamp must include a timezone"))
        return None
    parsed = parsed.astimezone(UTC)
    if parsed > datetime.now(UTC) + timedelta(minutes=5):
        errors.append(_error(row_index, "source_timestamp", "Future source timestamps are not allowed"))
        return None
    return parsed


def _validate_currency(value: str, *, row_index: int, field: str, errors: list[dict[str, Any]]) -> str | None:
    normalized = value.upper()
    if len(normalized) != 3 or not normalized.isalpha():
        errors.append(_error(row_index, field, "Currency must be a three-letter alphabetic code"))
        return None
    return normalized


def _validate_source(row: dict[str, str], *, row_index: int, errors: list[dict[str, Any]]) -> tuple[str | None, str | None, datetime | None]:
    provider = row["provider_name"].strip()
    if not provider:
        errors.append(_error(row_index, "provider_name", "Required field missing"))
    elif len(provider) > 80:
        errors.append(_error(row_index, "provider_name", "Must be 80 characters or fewer"))
    elif provider.lower() in GENERIC_PROVIDER_NAMES:
        errors.append(_error(row_index, "provider_name", "Name the actual exchange, central bank, or data provider"))
    elif provider.startswith(("=", "+", "-", "@", "\t", "\r")):
        errors.append(_error(row_index, "provider_name", "Invalid leading character"))

    source_url = row["source_url"].strip()
    if not source_url:
        errors.append(_error(row_index, "source_url", "A source URL is required for traceability"))
    elif len(source_url) > 1000:
        errors.append(_error(row_index, "source_url", "Must be 1000 characters or fewer"))
    else:
        parsed_url = urlsplit(source_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
            errors.append(_error(row_index, "source_url", "Source URL must use http or https and include a host"))
        elif parsed_url.username or parsed_url.password:
            errors.append(_error(row_index, "source_url", "Source URL must not contain credentials"))
        elif parsed_url.hostname.lower() == "localhost" or parsed_url.hostname.lower().endswith(".localhost"):
            errors.append(_error(row_index, "source_url", "Localhost source URLs are not allowed"))
        else:
            try:
                address = ipaddress.ip_address(parsed_url.hostname)
            except ValueError:
                address = None
            if address is not None and not address.is_global:
                errors.append(_error(row_index, "source_url", "Private or non-global source addresses are not allowed"))

    timestamp = _parse_timestamp(row["source_timestamp"], row_index=row_index, errors=errors)
    for field in ("provider_name", "provider_symbol", "source_url", "price_type"):
        if _mock_marked(row[field]):
            errors.append(_error(row_index, field, "Mock Data markers are not allowed in real-input evidence"))
    return provider or None, source_url or None, timestamp


def _unused_fields(row: dict[str, str], fields: set[str], *, row_index: int, errors: list[dict[str, Any]]) -> None:
    for field in fields:
        if row[field]:
            errors.append(_error(row_index, field, f"Field must be empty for {row['record_type']} rows"))


def _normalize_market_price(
    row: dict[str, str], row_index: int, scope: EvidenceScope, errors: list[dict[str, Any]]
) -> NormalizedEvidenceRow | None:
    _unused_fields(row, {"base_currency", "quote_currency", "rate"}, row_index=row_index, errors=errors)
    ticker = row["ticker"].upper()
    if not ticker:
        errors.append(_error(row_index, "ticker", "Required field missing"))
    elif len(ticker) > 20:
        errors.append(_error(row_index, "ticker", "Must be 20 characters or fewer"))
    elif any(character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_^" for character in ticker):
        errors.append(_error(row_index, "ticker", "Contains unsupported characters"))
    company = scope.companies_by_ticker.get(ticker)
    if ticker not in scope.price_currency_by_ticker:
        errors.append(_error(row_index, "ticker", "Ticker is not a positive holding or the active benchmark"))
    elif company is None:
        errors.append(_error(row_index, "ticker", "Ticker must resolve to a linked company before price import"))
    currency = _validate_currency(row["currency"], row_index=row_index, field="currency", errors=errors)
    expected_currency = scope.price_currency_by_ticker.get(ticker)
    if currency and expected_currency and currency != expected_currency:
        errors.append(_error(row_index, "currency", f"Expected {expected_currency} for {ticker}"))
    price = _parse_positive_decimal(row["price"], row_index=row_index, field="price", errors=errors)
    as_of = _parse_date(row["as_of_date"], row_index=row_index, errors=errors)
    provider, source_url, source_timestamp = _validate_source(row, row_index=row_index, errors=errors)
    if as_of and source_timestamp and source_timestamp.date() < as_of:
        errors.append(_error(row_index, "source_timestamp", "Source timestamp cannot precede the observation date"))
    provider_symbol = row["provider_symbol"] or None
    if provider_symbol and len(provider_symbol) > 50:
        errors.append(_error(row_index, "provider_symbol", "Must be 50 characters or fewer"))
    elif provider_symbol and provider_symbol.startswith(("=", "+", "-", "@", "\t", "\r")):
        errors.append(_error(row_index, "provider_symbol", "Invalid leading character"))
    price_type = row["price_type"].lower()
    if price_type not in ALLOWED_PRICE_TYPES:
        errors.append(_error(row_index, "price_type", f"Must be one of: {', '.join(sorted(ALLOWED_PRICE_TYPES))}"))
    if errors or company is None or not all((currency, price, as_of, provider, source_url, source_timestamp)):
        return None
    values = {
        "company_id": company.id,
        "ticker": ticker,
        "price": price,
        "currency": currency,
        "as_of_date": as_of,
        "provider_name": provider,
        "provider_symbol": provider_symbol,
        "source_url": source_url,
        "source_timestamp": source_timestamp,
        "price_type": price_type,
        "adjustment_state": "adjusted" if price_type == "adjusted_close" else "not_applicable",
        "claim_type": "Fact",
        "warnings_json": [],
    }
    return NormalizedEvidenceRow(
        row_index=row_index,
        record_type="market_price",
        values=values,
        identity=("market_price", company.id, as_of, provider.lower(), price_type),
    )


def _normalize_fx_rate(
    row: dict[str, str], row_index: int, scope: EvidenceScope, errors: list[dict[str, Any]]
) -> NormalizedEvidenceRow | None:
    _unused_fields(row, {"ticker", "price", "currency", "price_type"}, row_index=row_index, errors=errors)
    base = _validate_currency(row["base_currency"], row_index=row_index, field="base_currency", errors=errors)
    quote = _validate_currency(row["quote_currency"], row_index=row_index, field="quote_currency", errors=errors)
    if base and quote and base == quote:
        errors.append(_error(row_index, "quote_currency", "FX currencies must differ"))
    if base and quote and (base, quote) not in scope.allowed_fx_pairs:
        errors.append(_error(row_index, "base_currency", "FX pair is not required by this portfolio or benchmark"))
    rate = _parse_positive_decimal(row["rate"], row_index=row_index, field="rate", errors=errors)
    as_of = _parse_date(row["as_of_date"], row_index=row_index, errors=errors)
    provider, source_url, source_timestamp = _validate_source(row, row_index=row_index, errors=errors)
    if as_of and source_timestamp and source_timestamp.date() < as_of:
        errors.append(_error(row_index, "source_timestamp", "Source timestamp cannot precede the observation date"))
    provider_symbol = row["provider_symbol"] or None
    if provider_symbol and len(provider_symbol) > 80:
        errors.append(_error(row_index, "provider_symbol", "Must be 80 characters or fewer"))
    elif provider_symbol and provider_symbol.startswith(("=", "+", "-", "@", "\t", "\r")):
        errors.append(_error(row_index, "provider_symbol", "Invalid leading character"))
    if errors or not all((base, quote, rate, as_of, provider, source_url, source_timestamp)):
        return None
    values = {
        "base_currency": base,
        "quote_currency": quote,
        "rate": rate,
        "as_of_date": as_of,
        "provider_name": provider,
        "provider_symbol": provider_symbol,
        "source_url": source_url,
        "source_timestamp": source_timestamp,
        "claim_type": "Fact",
    }
    return NormalizedEvidenceRow(
        row_index=row_index,
        record_type="fx_rate",
        values=values,
        identity=("fx_rate", base, quote, as_of, provider.lower()),
    )


def _same_timestamp(existing: datetime | None, incoming: datetime | None) -> bool:
    if existing is None or incoming is None:
        return existing is incoming
    existing_utc = existing.replace(tzinfo=UTC) if existing.tzinfo is None else existing.astimezone(UTC)
    incoming_utc = incoming.replace(tzinfo=UTC) if incoming.tzinfo is None else incoming.astimezone(UTC)
    return existing_utc == incoming_utc


def _same_price(existing: MarketPrice, values: dict[str, Any]) -> bool:
    return all(
        (
            Decimal(existing.price) == values["price"],
            existing.currency == values["currency"],
            existing.provider_symbol == values["provider_symbol"],
            existing.source_url == values["source_url"],
            _same_timestamp(existing.source_timestamp, values["source_timestamp"]),
            existing.claim_type == values["claim_type"],
        )
    )


def _same_fx(existing: FxRateObservation, values: dict[str, Any]) -> bool:
    return all(
        (
            Decimal(existing.rate) == values["rate"],
            existing.provider_symbol == values["provider_symbol"],
            existing.source_url == values["source_url"],
            _same_timestamp(existing.source_timestamp, values["source_timestamp"]),
            existing.claim_type == values["claim_type"],
        )
    )


def preview_evidence_bundle(db: Session, evidence_file: EvidenceFile, scope: EvidenceScope) -> tuple[dict[str, Any], list[NormalizedEvidenceRow]]:
    results: list[dict[str, Any]] = []
    accepted: list[NormalizedEvidenceRow] = []
    seen: dict[tuple[Any, ...], NormalizedEvidenceRow] = {}
    counts = {"create": 0, "skip": 0, "error": 0, "market_price": 0, "fx_rate": 0}

    for row_index, row in enumerate(evidence_file.rows, start=2):
        errors: list[dict[str, Any]] = []
        record_type = row["record_type"].lower()
        if record_type == "market_price":
            normalized = _normalize_market_price(row, row_index, scope, errors)
        elif record_type == "fx_rate":
            normalized = _normalize_fx_rate(row, row_index, scope, errors)
        else:
            errors.append(_error(row_index, "record_type", "Must be market_price or fx_rate"))
            normalized = None

        action = "error"
        message = errors[0]["message"] if errors else ""
        if normalized is not None and not errors:
            prior = seen.get(normalized.identity)
            if prior is not None:
                if prior.values == normalized.values:
                    action = "skip"
                    message = f"Exact duplicate of row {prior.row_index}"
                else:
                    errors.append(_error(row_index, "conflict", f"Conflicts with row {prior.row_index}"))
                    message = errors[-1]["message"]
            elif normalized.record_type == "market_price":
                values = normalized.values
                existing = db.scalar(
                    select(MarketPrice)
                    .where(
                        MarketPrice.company_id == values["company_id"],
                        MarketPrice.as_of_date == values["as_of_date"],
                        func.lower(MarketPrice.provider_name) == values["provider_name"].lower(),
                        MarketPrice.price_type == values["price_type"],
                    )
                    .order_by(MarketPrice.id)
                )
                if existing is None:
                    action = "create"
                    accepted.append(normalized)
                elif _same_price(existing, values):
                    action = "skip"
                    message = f"Exact stored duplicate, market price {existing.id}"
                else:
                    errors.append(_error(row_index, "conflict", f"Conflicts with stored market price {existing.id}"))
                    message = errors[-1]["message"]
            else:
                values = normalized.values
                existing = db.scalar(
                    select(FxRateObservation)
                    .where(
                        FxRateObservation.base_currency == values["base_currency"],
                        FxRateObservation.quote_currency == values["quote_currency"],
                        FxRateObservation.as_of_date == values["as_of_date"],
                        func.lower(FxRateObservation.provider_name) == values["provider_name"].lower(),
                    )
                    .order_by(FxRateObservation.id)
                )
                if existing is None:
                    action = "create"
                    accepted.append(normalized)
                elif _same_fx(existing, values):
                    action = "skip"
                    message = f"Exact stored duplicate, FX observation {existing.id}"
                else:
                    errors.append(_error(row_index, "conflict", f"Conflicts with stored FX observation {existing.id}"))
                    message = errors[-1]["message"]
            seen[normalized.identity] = normalized

        counts[action] += 1
        if record_type in {"market_price", "fx_rate"}:
            counts[record_type] += 1
        results.append(
            {
                "row_index": row_index,
                "record_type": record_type or None,
                "action": action,
                "message": message or ("Ready to create" if action == "create" else "Blocked"),
                "errors": errors,
            }
        )

    payload = {
        "is_preview": True,
        "filename": evidence_file.filename,
        "content_sha256": evidence_file.content_sha256,
        "byte_size": evidence_file.byte_size,
        "total_rows": len(results),
        "create_count": counts["create"],
        "skip_count": counts["skip"],
        "error_count": counts["error"],
        "market_price_count": counts["market_price"],
        "fx_rate_count": counts["fx_rate"],
        "can_apply": counts["error"] == 0 and counts["create"] > 0,
        "claim_type": "Fact",
        "contains_mock_data": False,
        "scope": {
            "portfolio_id": scope.portfolio.id,
            "portfolio_name": scope.portfolio.name,
            "holding_tickers": sorted(scope.holding_tickers),
            "benchmark_ticker": scope.benchmark_ticker,
            "allowed_fx_pairs": [f"{base}/{quote}" for base, quote in sorted(scope.allowed_fx_pairs)],
        },
        "rows": results,
    }
    return payload, accepted


def materialize_evidence_rows(rows: list[NormalizedEvidenceRow], *, processing_run_id: int) -> tuple[list[MarketPrice], list[FxRateObservation]]:
    prices: list[MarketPrice] = []
    fx_rates: list[FxRateObservation] = []
    for row in rows:
        values = {**row.values, "import_run_id": processing_run_id}
        if row.record_type == "market_price":
            prices.append(MarketPrice(**values))
        else:
            fx_rates.append(FxRateObservation(**values))
    return prices, fx_rates
