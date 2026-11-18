"""Financial Modeling Prep stable endpoints with explicit split-adjusted history."""
from datetime import datetime, timedelta, timezone

from app.providers.market_data.parsing import (epoch_time, fail, integer, iso_date, number,
    prior_date_window, unique_points, validate_listing, validate_request)
from app.providers.market_data.transport import AdapterTransport, provider_error
from app.schemas.data_adapters import AdapterHistoryRequest, AdapterHistoryResult
from app.services.market_data.base import MarketDataProvider, MarketDataRequest, MarketHistoryResult, MarketQuoteResult
from app.services.market_data.sessions import history_window


class FMPProvider(MarketDataProvider):
    provider_name = "fmp"
    base_url = "https://financialmodelingprep.com/stable"

    def __init__(self, api_key: str, *, transport=None):
        self.api_key = api_key
        self.transport = transport or AdapterTransport(self.provider_name)

    @property
    def captures(self):
        return self.transport.captures

    async def _get(self, path, params):
        if not self.api_key:
            raise provider_error(self.provider_name, "PROVIDER_NOT_CONFIGURED", "FMP API key is not configured.", status=503)
        result = await self.transport.request(self.base_url + path, params={**params, "apikey": self.api_key})
        data = result.payload
        if isinstance(data, dict) and any(k in data for k in ("Error Message", "error", "message")):
            raise provider_error(self.provider_name, "PROVIDER_REJECTED_REQUEST", "FMP did not provide the requested dataset.", status=502)
        if not isinstance(data, list):
            fail(self.provider_name)
        return data, result.observed_at

    async def _profile(self, request):
        validate_request(request, self.provider_name, market="US")
        rows, _ = await self._get("/profile", {"symbol": request.ticker})
        if len(rows) != 1 or not isinstance(rows[0], dict):
            fail(self.provider_name, "PROVIDER_IDENTITY_UNRESOLVED")
        profile = rows[0]
        currency, exchange = validate_listing(request, self.provider_name, symbol=profile.get("symbol"),
            currency=profile.get("currency"), exchange=profile.get("exchange") or profile.get("exchangeShortName"))
        return currency, exchange

    async def get_quote(self, request: MarketDataRequest) -> MarketQuoteResult:
        currency, exchange = await self._profile(request)
        rows, observed = await self._get("/quote", {"symbol": request.ticker})
        if len(rows) != 1 or not isinstance(rows[0], dict):
            fail(self.provider_name, "PROVIDER_EMPTY_RESPONSE")
        row = rows[0]
        validate_listing(request, self.provider_name, symbol=row.get("symbol"), currency=currency,
                         exchange=row.get("exchange") or exchange)
        source_time = epoch_time(row.get("timestamp"), self.provider_name)
        warnings = ["FMP subscription delay is not established by this response; price type remains unknown."]
        if (observed - source_time).total_seconds() > 86400:
            warnings.append("The provider quote timestamp is more than 24 hours old.")
        return MarketQuoteResult(provider_name=self.provider_name, provider_symbol=row["symbol"],
            market=request.market, exchange=exchange, ticker=request.ticker, currency=currency,
            current_price=number(row.get("price"), self.provider_name, positive=True),
            change_percent=number(row.get("changePercentage"), self.provider_name, optional=True),
            volume=integer(row.get("volume"), self.provider_name, optional=True),
            market_cap=number(row.get("marketCap"), self.provider_name, optional=True, nonnegative=True),
            fifty_two_week_high=number(row.get("yearHigh"), self.provider_name, optional=True, positive=True),
            fifty_two_week_low=number(row.get("yearLow"), self.provider_name, optional=True, positive=True),
            source_timestamp=source_time, observed_at=observed, price_type="unknown",
            adjustment_state="not_applicable", warnings=warnings)

    async def get_history(self, request: AdapterHistoryRequest) -> AdapterHistoryResult:
        prior_date_window(request, self.provider_name)
        if request.adjustment == "unadjusted":
            raise provider_error(self.provider_name, "PROVIDER_UNSUPPORTED_BASIS",
                "This FMP adapter uses documented split-adjusted close prices; unadjusted history is not enabled.", status=422)
        currency, exchange = await self._profile(request)
        rows, observed = await self._get("/historical-price-eod/full", {"symbol": request.ticker,
            "from": request.start_date.isoformat(), "to": request.end_date.isoformat()})
        points = []
        warnings = ["Close prices are adjusted for stock splits only, not dividend-inclusive total returns.",
                    "Complete denotes retrieved API windows, not independently certified exchange-session coverage."]
        for row in rows:
            if not isinstance(row, dict) or row.get("symbol") != request.ticker:
                fail(self.provider_name, "PROVIDER_IDENTITY_MISMATCH")
            day = iso_date(row.get("date"), self.provider_name)
            if not request.start_date <= day <= request.end_date:
                continue
            points.append(MarketHistoryResult(provider_name=self.provider_name, provider_symbol=request.ticker,
                market=request.market, exchange=exchange, ticker=request.ticker, currency=currency,
                date=day, close_price=number(row.get("close"), self.provider_name, positive=True), observed_at=observed,
                adjustment_state="adjusted", warnings=warnings))
        points = unique_points(points, self.provider_name)
        return AdapterHistoryResult(requested_start=request.start_date, requested_end=request.end_date,
            points=points, coverage="complete" if points else "empty", warnings=warnings)

    async def get_historical_prices(self, request: MarketDataRequest, days=365) -> list[MarketHistoryResult]:
        window = history_window(request, days)
        result = await self.get_history(AdapterHistoryRequest(**request.model_dump(),
            start_date=window.start, end_date=window.end-timedelta(days=1)))
        return result.points
