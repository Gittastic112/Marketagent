"""Official Massive US equity endpoints; bounded pages, current action API."""
from datetime import timedelta
from urllib.parse import parse_qs, quote, urlsplit
from zoneinfo import ZoneInfo

from app.providers.market_data.parsing import (EXCHANGES, epoch_time, fail, integer, iso_date, number,
    prior_date_window, unique_points, validate_listing, validate_request)
from app.providers.market_data.transport import AdapterTransport, provider_error, response_hash
from app.schemas.data_adapters import (AdapterActionRequest, AdapterActionsResult, AdapterCoverageGap,
    AdapterHistoryRequest, AdapterHistoryResult, CorporateActionEvidence, SecurityReferenceResult)
from app.services.market_data.base import MarketDataProvider, MarketDataProviderError, MarketDataRequest, MarketHistoryResult, MarketQuoteResult
from app.services.market_data.sessions import history_window


class MassiveProvider(MarketDataProvider):
    provider_name = "massive"
    base_url = "https://api.massive.com"

    def __init__(self, api_key: str, *, transport=None):
        self.api_key = api_key
        self.transport = transport or AdapterTransport(self.provider_name)

    @property
    def captures(self):
        return self.transport.captures

    async def _get(self, path, params=None):
        if not self.api_key:
            raise provider_error(self.provider_name, "PROVIDER_NOT_CONFIGURED", "Massive API key is not configured.", status=503)
        result = await self.transport.request(self.base_url + path, params=params,
            headers={"Authorization": f"Bearer {self.api_key}"})
        data = result.payload
        if not isinstance(data, dict):
            fail(self.provider_name)
        if data.get("status") not in {"OK", "DELAYED"}:
            raise provider_error(self.provider_name, "PROVIDER_REJECTED_REQUEST", "Massive did not supply the requested dataset.")
        return data, result.observed_at

    async def get_reference(self, request: MarketDataRequest) -> SecurityReferenceResult:
        validate_request(request, self.provider_name, market="US")
        data, observed = await self._get("/v3/reference/tickers/" + quote(request.ticker, safe=""))
        row = data.get("results")
        if not isinstance(row, dict) or row.get("locale") != "us" or row.get("market") != "stocks":
            fail(self.provider_name, "PROVIDER_IDENTITY_UNRESOLVED")
        currency, exchange = validate_listing(request, self.provider_name, symbol=row.get("ticker"),
            currency=row.get("currency_name"), exchange=row.get("primary_exchange"))
        return SecurityReferenceResult(provider=self.provider_name, ticker=request.ticker, name=row.get("name"),
            market=request.market, exchange=exchange, currency=currency, active=row.get("active"),
            cik=row.get("cik"), composite_figi=row.get("composite_figi"), share_class_figi=row.get("share_class_figi"),
            observed_at=observed, warnings=["Current reference mapping is not a point-in-time security master."])

    async def get_quote(self, request: MarketDataRequest) -> MarketQuoteResult:
        reference = await self.get_reference(request)
        data, observed = await self._get("/v2/snapshot/locale/us/markets/stocks/tickers/" + quote(request.ticker, safe=""))
        row = data.get("ticker")
        if not isinstance(row, dict) or row.get("ticker") != request.ticker:
            fail(self.provider_name, "PROVIDER_IDENTITY_MISMATCH")
        trade = row.get("lastTrade")
        if not isinstance(trade, dict) or trade.get("p") is None or trade.get("t") is None:
            raise provider_error(self.provider_name, "PROVIDER_QUOTE_UNAVAILABLE",
                "This response has no last-trade quote. Prior-day bars are not substituted.", status=503)
        source_time = epoch_time(trade["t"], self.provider_name, divisor=1_000_000_000)
        warnings = ["Price is the last qualifying trade; exact subscription delay is not supplied."]
        if (observed-source_time).total_seconds() > 86400:
            warnings.append("The last-trade timestamp is more than 24 hours old.")
        return MarketQuoteResult(provider_name=self.provider_name, provider_symbol=request.ticker,
            market=request.market, exchange=reference.exchange, ticker=request.ticker, currency=reference.currency,
            current_price=number(trade["p"], self.provider_name, positive=True),
            change_percent=number(row.get("todaysChangePerc"), self.provider_name, optional=True),
            source_timestamp=source_time, observed_at=observed,
            price_type="delayed" if data.get("status") == "DELAYED" else "unknown",
            adjustment_state="not_applicable", warnings=warnings)

    def _cursor(self, next_url, path):
        parsed = urlsplit(next_url)
        if (parsed.scheme != "https" or parsed.hostname != "api.massive.com" or parsed.path != path
                or parsed.port not in {None, 443} or parsed.username or parsed.password or parsed.fragment):
            fail(self.provider_name, "PROVIDER_PAGINATION_REJECTED")
        query = parse_qs(parsed.query)
        if set(query) - {"cursor", "apiKey"} or len(query.get("cursor", [])) != 1:
            fail(self.provider_name, "PROVIDER_PAGINATION_REJECTED")
        cursor = query["cursor"][0]
        if not cursor or len(cursor) > 2048:
            fail(self.provider_name, "PROVIDER_PAGINATION_REJECTED")
        return cursor

    async def _pages(self, path, params):
        pages, cursors, gaps = [], set(), []
        for _ in range(8):
            try:
                data, observed = await self._get(path, params)
                if not isinstance(data.get("results", []), list):
                    fail(self.provider_name)
                pages.append((data, observed))
                next_url = data.get("next_url")
                if not next_url:
                    break
                cursor = self._cursor(next_url, path)
                if cursor in cursors:
                    fail(self.provider_name, "PROVIDER_PAGINATION_LOOP")
                cursors.add(cursor)
                params = {"cursor": cursor}
            except MarketDataProviderError as exc:
                if not pages:
                    raise
                gaps.append(AdapterCoverageGap(code=exc.code, retryable=exc.retryable))
                break
        else:
            gaps.append(AdapterCoverageGap(code="PROVIDER_PAGE_BUDGET"))
        return pages, gaps

    async def get_history(self, request: AdapterHistoryRequest) -> AdapterHistoryResult:
        prior_date_window(request, self.provider_name)
        ref = await self.get_reference(request)
        adjusted = request.adjustment == "split_adjusted"
        path = f"/v2/aggs/ticker/{quote(request.ticker, safe='')}/range/1/day/{request.start_date}/{request.end_date}"
        pages, gaps = await self._pages(path, {"adjusted": str(adjusted).lower(), "sort": "asc", "limit": 5000})
        points = []
        warnings = ["Split-adjusted prices exclude cash-dividend reinvestment." if adjusted else "Raw prices are unadjusted for splits and dividends.",
            "API coverage is not certified exchange-session or point-in-time feed coverage."]
        for data, observed in pages:
            if data.get("ticker") != request.ticker or data.get("adjusted") is not adjusted:
                fail(self.provider_name, "PROVIDER_HISTORY_BASIS_MISMATCH")
            for row in data.get("results", []):
                if not isinstance(row, dict):
                    fail(self.provider_name)
                day = epoch_time(row.get("t"), self.provider_name, divisor=1000).astimezone(ZoneInfo("America/New_York")).date()
                if request.start_date <= day <= request.end_date:
                    points.append(MarketHistoryResult(provider_name=self.provider_name, provider_symbol=request.ticker,
                        market=request.market, exchange=ref.exchange, ticker=request.ticker, currency=ref.currency,
                        date=day, close_price=number(row.get("c"), self.provider_name, positive=True), observed_at=observed,
                        adjustment_state="adjusted" if adjusted else "unadjusted", warnings=warnings))
        points = unique_points(points, self.provider_name)
        return AdapterHistoryResult(requested_start=request.start_date, requested_end=request.end_date,
            points=points, coverage="partial" if gaps else "complete" if points else "empty", gaps=gaps, warnings=warnings)

    async def get_historical_prices(self, request, days=365):
        window = history_window(request, days)
        result = await self.get_history(AdapterHistoryRequest(**request.model_dump(), start_date=window.start,
            end_date=window.end-timedelta(days=1)))
        if result.coverage == "partial":
            raise provider_error(self.provider_name, "PROVIDER_PARTIAL_HISTORY", "History is incomplete; use the dated adapter endpoint to inspect coverage.")
        return result.points

    async def get_actions(self, request: AdapterActionRequest) -> AdapterActionsResult:
        validate_request(request, self.provider_name, market="US")
        actions, gaps = [], []
        for action_type, path, date_key in (("split", "/stocks/v1/splits", "execution_date"),
                                          ("dividend", "/stocks/v1/dividends", "ex_dividend_date")):
            try:
                pages, failures = await self._pages(path, {"ticker": request.ticker,
                    date_key+".gte": request.start_date.isoformat(), date_key+".lte": request.end_date.isoformat(),
                    "limit": 1000, "sort": date_key+".asc"})
                gaps.extend(failures)
                for data, observed in pages:
                    for i, row in enumerate(data.get("results", [])):
                        if not isinstance(row, dict) or row.get("ticker") != request.ticker:
                            fail(self.provider_name, "PROVIDER_IDENTITY_MISMATCH")
                        day = iso_date(row.get(date_key), self.provider_name)
                        if not request.start_date <= day <= request.end_date:
                            fail(self.provider_name, "PROVIDER_DATE_MISMATCH")
                        venue = row.get("primary_exchange") or row.get("exchange")
                        if venue is not None:
                            venue = EXCHANGES.get(str(venue).upper())
                            expected = EXCHANGES.get(request.exchange) if request.exchange else None
                            if not venue or (expected and venue != expected):
                                fail(self.provider_name, "PROVIDER_IDENTITY_MISMATCH")
                        kind = "bonus" if action_type == "split" and row.get("adjustment_type") == "stock_dividend" else action_type
                        actions.append(CorporateActionEvidence(provider=self.provider_name, provider_record_id=row.get("id"),
                            ticker=request.ticker, market=request.market, exchange=venue, action_type=kind,
                            description=str(row.get("adjustment_type") or row.get("distribution_type") or action_type),
                            ex_date=day if action_type == "dividend" else None,
                            execution_date=day if action_type == "split" else None,
                            announcement_date=iso_date(row.get("declaration_date"), self.provider_name, optional=True),
                            record_date=iso_date(row.get("record_date"), self.provider_name, optional=True),
                            payment_date=iso_date(row.get("pay_date"), self.provider_name, optional=True),
                            cash_amount=number(row.get("cash_amount"), self.provider_name, optional=True, nonnegative=True),
                            currency=row.get("currency"), old_shares=number(row.get("split_from"), self.provider_name, optional=True, positive=True),
                            new_shares=number(row.get("split_to"), self.provider_name, optional=True, positive=True),
                            observed_at=observed, source_response_hash=response_hash(data), source_locator=f"$.results[{i}]",
                            warnings=["Declaration date is not proven provider-availability time. Action evidence is not applied to holdings.",
                                *(["The action record does not identify its historical listing venue."] if not venue else [])]))
            except MarketDataProviderError as exc:
                gaps.append(AdapterCoverageGap(start_date=request.start_date, end_date=request.end_date,
                    code=exc.code, retryable=exc.retryable))
        if len(gaps) == 2 and not actions:
            raise provider_error(self.provider_name, "PROVIDER_ACTIONS_UNAVAILABLE", "Neither corporate-action dataset was available.")
        # Stable records can repeat at page boundaries. Conflicts are retained as
        # separate evidence versions rather than replacing a previous payload.
        unique = {response_hash(a.model_dump(mode="json", exclude={"observed_at", "source_locator", "source_response_hash"})): a for a in actions}
        return AdapterActionsResult(actions=list(unique.values()), coverage="partial" if gaps else "complete" if actions else "empty", gaps=gaps,
            warnings=["Corporate-action evidence is not an adjusted-price or total-return series."])
