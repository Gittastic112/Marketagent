"""Official NSE MCP adapters, mapped from inspected schemas and public samples.

Dated prices are derived from dated history: get_ltp_by_date returns only a
number and cannot establish the resolved session. Only EQ series is supported.
"""
from datetime import datetime, timedelta, timezone
import json
import re
from zoneinfo import ZoneInfo

from app.providers.market_data.parsing import fail, integer, iso_date, number, prior_date_window, unique_points, validate_listing, validate_request
from app.providers.market_data.transport import AdapterTransport, provider_error, response_hash
from app.schemas.data_adapters import (AdapterActionRequest, AdapterActionsResult, AdapterCoverageGap,
    AdapterDatedQuoteRequest, AdapterDatedQuoteResult, AdapterHistoryRequest, AdapterHistoryResult,
    CorporateActionEvidence)
from app.services.market_data.base import MarketDataProvider, MarketDataProviderError, MarketHistoryResult, MarketQuoteResult
from app.services.market_data.sessions import history_window

BHAVCOPY = "https://mcp.nseindia.in/bhavcopy/cm/mcp"
CURRENT = "https://mcp.nseindia.in/cmmkt/mcp"
TOOL_ARGUMENTS = {
    "get_stock_history": {"symbol": "string", "months": "integer", "endDate": "string"},
    "get_corporate_actions": {"symbol": "string", "fromDate": "string", "toDate": "string"},
    "cm_get_stock_quote": {"symbol": "string"},
}


class NSEMCPClient:
    def __init__(self, endpoint, transport):
        if endpoint not in {BHAVCOPY, CURRENT}:
            raise ValueError("Only official NSE MCP endpoints are supported")
        self.endpoint, self.transport = endpoint, transport
        self.session = None
        self.request_id = 0
        self.tools = None

    async def _rpc(self, method, params=None, *, notification=False, capture=False):
        self.request_id += 1
        payload = {"jsonrpc": "2.0", "method": method}
        if not notification:
            payload["id"] = self.request_id
        if params is not None:
            payload["params"] = params
        headers = {"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2025-03-26"}
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        wire = await self.transport.request(self.endpoint, payload=payload, headers=headers,
            rpc_id=None if notification else self.request_id, notification=notification, capture=capture)
        session = wire.headers.get("mcp-session-id")
        if session:
            if not re.fullmatch(r"[\x21-\x7e]{1,1024}", session):
                fail("nse_mcp", "PROVIDER_SESSION_INVALID")
            self.session = session
        if notification:
            return None, wire.observed_at
        data = wire.payload
        if not isinstance(data, dict) or data.get("jsonrpc") != "2.0" or data.get("id") != self.request_id:
            fail("nse_mcp", "PROVIDER_PROTOCOL_MISMATCH")
        if "error" in data or not isinstance(data.get("result"), dict):
            fail("nse_mcp", "PROVIDER_TOOL_FAILED")
        return data["result"], wire.observed_at

    async def _initialize(self):
        if self.tools is not None:
            return
        result, _ = await self._rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
            "clientInfo": {"name": "Marketagent", "version": "1"}})
        if result.get("protocolVersion") != "2025-03-26":
            fail("nse_mcp", "PROVIDER_PROTOCOL_UNSUPPORTED")
        await self._rpc("notifications/initialized", notification=True)
        result, _ = await self._rpc("tools/list", {})
        if not isinstance(result.get("tools"), list) or result.get("nextCursor"):
            fail("nse_mcp", "PROVIDER_TOOL_SCHEMA_CHANGED")
        self.tools = {t.get("name"): t for t in result["tools"] if isinstance(t, dict)}

    async def call(self, name, arguments):
        allowed = {"get_stock_history", "get_corporate_actions"} if self.endpoint == BHAVCOPY else {"cm_get_stock_quote"}
        if name not in allowed:
            raise provider_error("nse_mcp", "PROVIDER_TOOL_REJECTED", "This tool is not allowlisted.")
        await self._initialize()
        tool = self.tools.get(name, {})
        schema = tool.get("inputSchema", {})
        expected = TOOL_ARGUMENTS[name]
        properties = schema.get("properties", {})
        if (schema.get("type") != "object" or set(schema.get("required", [])) != set(expected)
                or set(properties) != set(expected) or set(arguments) != set(expected)
                or any(properties[k].get("type") != v for k, v in expected.items())):
            fail("nse_mcp", "PROVIDER_TOOL_SCHEMA_CHANGED")
        result, observed = await self._rpc("tools/call", {"name": name, "arguments": arguments}, capture=True)
        if result.get("isError"):
            fail("nse_mcp", "PROVIDER_TOOL_FAILED")
        value = result.get("structuredContent")
        if value is None:
            content = result.get("content")
            if not isinstance(content, list) or len(content) != 1 or content[0].get("type") != "text":
                fail("nse_mcp", "PROVIDER_TOOL_SCHEMA_CHANGED")
            try:
                value = json.loads(content[0]["text"], parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            except (ValueError, KeyError, TypeError):
                fail("nse_mcp", "PROVIDER_TOOL_SCHEMA_CHANGED")
        if not isinstance(value, dict):
            fail("nse_mcp", "PROVIDER_TOOL_SCHEMA_CHANGED")
        if value.get("error"):
            fail("nse_mcp", "PROVIDER_TOOL_FAILED")
        return value, observed


class NSEMarketProvider(MarketDataProvider):
    provider_name = "nse_mcp"

    def __init__(self, *, transport=None):
        self.transport = transport or AdapterTransport(self.provider_name)
        self.bhavcopy = NSEMCPClient(BHAVCOPY, self.transport)
        self.current = NSEMCPClient(CURRENT, self.transport)

    @property
    def captures(self):
        return self.transport.captures

    def _identity(self, request):
        validate_request(request, self.provider_name, market="IN")
        return validate_listing(request, self.provider_name, symbol=request.ticker, currency="INR", exchange="NSE")

    async def get_quote(self, request):
        currency, exchange = self._identity(request)
        data, observed = await self.current.call("cm_get_stock_quote", {"symbol": request.ticker})
        row = data.get("stock")
        if not isinstance(row, dict) or row.get("symbol") != request.ticker or row.get("series") != "EQ":
            fail(self.provider_name, "PROVIDER_IDENTITY_MISMATCH")
        raw_time = row.get("latestTimestamp")
        try:
            source_time = datetime.fromisoformat(raw_time)
            if source_time.tzinfo is None:
                source_time = source_time.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            source_time = source_time.astimezone(timezone.utc)
            if source_time > observed + timedelta(minutes=5):
                raise ValueError("future timestamp")
        except (TypeError, ValueError):
            fail(self.provider_name, "PROVIDER_TIMESTAMP_UNAVAILABLE")
        warnings = ["NSE MCP quotes have a documented approximate 1-3 minute delay, not guaranteed real-time delivery.",
                    "Source latestTimestamp is interpreted in Asia/Kolkata when no offset is supplied; updatedAt is retrieval refresh metadata."]
        if (observed-source_time).total_seconds() > 1200:
            warnings.append("Source quote is older than 20 minutes; this may be the last published value outside trading hours.")
        return MarketQuoteResult(provider_name=self.provider_name, provider_symbol=request.ticker,
            market="IN", exchange=exchange, ticker=request.ticker, currency=currency,
            current_price=number(row.get("lastTradedPrice"), self.provider_name, positive=True),
            change_percent=number(row.get("perChange"), self.provider_name, optional=True),
            volume=integer(row.get("volume"), self.provider_name, optional=True),
            fifty_two_week_high=number(row.get("fiftyTwoWeekHigh") or None, self.provider_name, optional=True, positive=True),
            fifty_two_week_low=number(row.get("fiftyTwoWeekLow") or None, self.provider_name, optional=True, positive=True),
            source_timestamp=source_time, observed_at=observed, price_type="delayed", delay_minutes=None,
            adjustment_state="not_applicable", warnings=warnings)

    async def get_actions(self, request: AdapterActionRequest) -> AdapterActionsResult:
        self._identity(request)
        data, observed = await self.bhavcopy.call("get_corporate_actions", {"symbol": request.ticker,
            "fromDate": request.start_date.isoformat(), "toDate": request.end_date.isoformat()})
        rows = data.get("actions")
        if data.get("symbol") != request.ticker or not isinstance(rows, list):
            fail(self.provider_name, "PROVIDER_TOOL_SCHEMA_CHANGED")
        actions = []
        digest = self.captures[-1].sha256
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                fail(self.provider_name)
            day = iso_date(row.get("exDate"), self.provider_name)
            if not request.start_date <= day <= request.end_date:
                fail(self.provider_name, "PROVIDER_DATE_MISMATCH")
            kind = str(row.get("actionType", "OTHER")).lower()
            actions.append(CorporateActionEvidence(provider=self.provider_name, ticker=request.ticker,
                market="IN", exchange=request.exchange or "NSE", action_type=kind if kind in {"split", "bonus", "dividend"} else "other",
                description=str(row.get("purpose") or "Unspecified action"), ex_date=day, observed_at=observed,
                source_response_hash=digest, source_locator=f"$.result.content[0].text::actions[{i}]",
                warnings=["Cash amount and share ratio are not inferred from prose or adjustmentFactor.",
                          "Public availability time is unknown; action evidence is not applied to holdings."]))
        partial = bool(data.get("warning"))
        return AdapterActionsResult(actions=actions, coverage="partial" if partial else "complete" if actions else "empty",
            gaps=[AdapterCoverageGap(code="PROVIDER_ACTION_WARNING")] if partial else [],
            warnings=["Provider reported incomplete corporate-action coverage."] if partial else [])

    async def get_history(self, request: AdapterHistoryRequest) -> AdapterHistoryResult:
        currency, exchange = self._identity(request)
        prior_date_window(request, self.provider_name)
        if request.adjustment == "split_adjusted":
            raise provider_error(self.provider_name, "PROVIDER_UNSUPPORTED_BASIS", "NSE MCP history is unadjusted.", status=422)
        if (request.end_date-request.start_date).days > 1830:
            raise provider_error(self.provider_name, "PROVIDER_INVALID_REQUEST", "NSE history windows are limited to five years.", status=422)
        warnings = ["NSE bhavcopy prices are unadjusted for corporate actions and are not total returns.",
                    "Only the EQ settlement series is accepted; API completion does not certify every exchange session."]
        gaps, points = [], []
        try:
            action_result = await self.get_actions(AdapterActionRequest(**request.model_dump(exclude={"adjustment"})))
            if action_result.coverage == "partial":
                warnings.append("Corporate-action coverage is incomplete.")
            if action_result.actions:
                warnings.append(f"The requested range has {len(action_result.actions)} corporate-action records; raw prices remain unadjusted.")
        except MarketDataProviderError:
            warnings.append("Corporate-action lookup was unavailable; discontinuities remain unverified.")
        end = request.end_date
        for _ in range(22):
            try:
                data, observed = await self.bhavcopy.call("get_stock_history",
                    {"symbol": request.ticker, "months": 3, "endDate": end.isoformat()})
                if data.get("symbol") != request.ticker or not isinstance(data.get("data"), list):
                    fail(self.provider_name, "PROVIDER_TOOL_SCHEMA_CHANGED")
                window_start = iso_date(data.get("from_date"), self.provider_name)
                window_end = iso_date(data.get("to_date"), self.provider_name)
                if window_start > window_end or window_end > end:
                    fail(self.provider_name, "PROVIDER_DATE_MISMATCH")
                for row in data["data"]:
                    if not isinstance(row, dict) or row.get("symbol") != request.ticker:
                        fail(self.provider_name, "PROVIDER_IDENTITY_MISMATCH")
                    day = iso_date(row.get("date"), self.provider_name)
                    if not request.start_date <= day <= request.end_date:
                        continue
                    if row.get("series") != "EQ":
                        gaps.append(AdapterCoverageGap(start_date=day, end_date=day, code="PROVIDER_UNSUPPORTED_SERIES"))
                        continue
                    points.append(MarketHistoryResult(provider_name=self.provider_name, provider_symbol=request.ticker,
                        market="IN", exchange=exchange, ticker=request.ticker, currency=currency, date=day,
                        close_price=number(row.get("close"), self.provider_name, positive=True), observed_at=observed,
                        adjustment_state="unadjusted", warnings=warnings))
                if data.get("warning"):
                    gaps.append(AdapterCoverageGap(start_date=max(window_start, request.start_date), end_date=end,
                        code="PROVIDER_HISTORY_WARNING"))
                if window_start <= request.start_date:
                    break
                next_end = iso_date(data.get("next_end_date"), self.provider_name)
                if next_end >= end or next_end < window_start-timedelta(days=1):
                    fail(self.provider_name, "PROVIDER_PAGINATION_LOOP")
                end = next_end
            except MarketDataProviderError as exc:
                if not points:
                    raise
                gaps.append(AdapterCoverageGap(start_date=request.start_date, end_date=end,
                    code=exc.code, retryable=exc.retryable))
                break
        else:
            gaps.append(AdapterCoverageGap(start_date=request.start_date, end_date=end, code="PROVIDER_PAGE_BUDGET"))
        points = unique_points(points, self.provider_name)
        return AdapterHistoryResult(requested_start=request.start_date, requested_end=request.end_date,
            points=points, coverage="partial" if gaps else "complete" if points else "empty", gaps=gaps, warnings=warnings)

    async def get_dated_quote(self, request: AdapterDatedQuoteRequest) -> AdapterDatedQuoteResult:
        result = await self.get_history(AdapterHistoryRequest(**request.model_dump(exclude={"requested_date"}),
            start_date=request.requested_date-timedelta(days=31), end_date=request.requested_date))
        if not result.points:
            fail(self.provider_name, "PROVIDER_EMPTY_RESPONSE")
        point = result.points[-1]
        # A skipped newer series or failed newest chunk would make the selected
        # previous session unknowable. Do not silently choose an older close.
        if any(g.end_date is None or g.end_date >= point.date for g in result.gaps):
            fail(self.provider_name, "PROVIDER_DATE_UNRESOLVED")
        return AdapterDatedQuoteResult(requested_date=request.requested_date, actual_date=point.date,
            point=point, previous_session_substitution=point.date != request.requested_date)

    async def get_historical_prices(self, request, days=365):
        window = history_window(request, days)
        result = await self.get_history(AdapterHistoryRequest(**request.model_dump(),
            start_date=window.start, end_date=window.end-timedelta(days=1)))
        if result.coverage == "partial":
            raise provider_error(self.provider_name, "PROVIDER_PARTIAL_HISTORY", "NSE history has gaps; use the dated adapter endpoint to inspect coverage.")
        return result.points
