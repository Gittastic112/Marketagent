"""Strict numerical and listing checks shared by the official adapters."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import re
from zoneinfo import ZoneInfo

from app.services.market_data.base import MarketDataProviderError
from app.providers.market_data.transport import provider_error

EXCHANGES = {"NASDAQ": "XNAS", "XNAS": "XNAS", "NASDAQGS": "XNAS", "NASDAQGM": "XNAS",
    "NASDAQCM": "XNAS", "NYSE": "XNYS", "XNYS": "XNYS", "AMEX": "XASE", "XASE": "XASE",
    "NYSE AMERICAN": "XASE", "ARCA": "ARCX", "ARCX": "ARCX", "NYSEARCA": "ARCX",
    "BATS": "BATS", "NSE": "XNSE", "XNSE": "XNSE", "BSE": "XBOM", "XBOM": "XBOM"}


def fail(provider, code="PROVIDER_INVALID_RESPONSE", message="Provider response does not match the requested financial contract."):
    raise provider_error(provider, code, message)


def validate_request(request, provider, *, market):
    if request.market != market or not re.fullmatch(r"[A-Z0-9][A-Z0-9.&_-]{0,39}", request.ticker):
        raise provider_error(provider, "PROVIDER_UNSUPPORTED_IDENTITY", "This adapter does not support the requested market or symbol.", status=422)


def validate_listing(request, provider, *, symbol, currency, exchange):
    if not isinstance(symbol, str) or symbol.upper() != request.ticker:
        fail(provider, "PROVIDER_IDENTITY_MISMATCH")
    if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency.upper()):
        fail(provider, "PROVIDER_CURRENCY_MISSING")
    currency = currency.upper()
    if request.currency and request.currency != currency:
        fail(provider, "PROVIDER_CURRENCY_MISMATCH")
    if not exchange or str(exchange).upper() not in EXCHANGES:
        fail(provider, "PROVIDER_EXCHANGE_UNVERIFIED")
    exchange = str(exchange).upper()
    if request.exchange and EXCHANGES.get(request.exchange, request.exchange) != EXCHANGES[exchange]:
        fail(provider, "PROVIDER_IDENTITY_MISMATCH")
    # Keep the requested, verified alias to preserve existing persistence identity.
    return currency, request.exchange or exchange


def number(value, provider, *, optional=False, positive=False, nonnegative=False):
    if value is None and optional:
        return None
    if isinstance(value, bool):
        fail(provider)
    try:
        result = Decimal(str(value))
        if not result.is_finite() or (positive and result <= 0) or (nonnegative and result < 0):
            fail(provider)
        return result
    except (InvalidOperation, ValueError, TypeError):
        fail(provider)


def integer(value, provider, *, optional=False):
    n = number(value, provider, optional=optional, nonnegative=True)
    if n is None:
        return None
    if n != n.to_integral_value():
        fail(provider)
    return int(n)


def iso_date(value, provider, *, optional=False):
    if value in (None, "") and optional:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        fail(provider)


def epoch_time(value, provider, *, divisor=1):
    n = number(value, provider, positive=True)
    try:
        result = datetime.fromtimestamp(float(n / divisor), tz=timezone.utc)
    except (ValueError, OverflowError, OSError):
        fail(provider)
    if result > datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=5):
        fail(provider, "PROVIDER_FUTURE_TIMESTAMP")
    return result


def prior_date_window(request, provider):
    zone = ZoneInfo("Asia/Kolkata" if request.market == "IN" else "America/New_York")
    if request.end_date >= datetime.now(zone).date():
        raise provider_error(provider, "PROVIDER_INVALID_REQUEST", "Daily history must end before the current market-local date.", status=422)


def unique_points(points, provider):
    by_date = {}
    for p in points:
        old = by_date.get(p.date)
        if old is not None and old.close_price != p.close_price:
            fail(provider, "PROVIDER_CONFLICTING_HISTORY")
        by_date[p.date] = p
    return [by_date[d] for d in sorted(by_date)]
