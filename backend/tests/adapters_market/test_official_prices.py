import asyncio
from datetime import datetime, timezone
import json
from types import SimpleNamespace

import pytest

from app.providers.market_data import transport
from app.providers.market_data.massive import MassiveProvider
from app.providers.market_data.transport import AdapterTransport, CapturedResponse, WireResponse, provider_error
from app.schemas.data_adapters import AdapterActionRequest, AdapterHistoryRequest, MarketDataRequest
from app.services.market_data.fmp import FMPProvider
from app.services.market_data.base import MarketDataProviderError

NOW = datetime(2026, 11, 17, 20, tzinfo=timezone.utc)
IDENTITY = dict(market="US", exchange="NASDAQ", ticker="MOCK", currency="USD")


class MockTransport:
    def __init__(self, responses):
        self.responses, self.captures, self.calls, self.request_count = list(responses), [], [], 0
    async def request(self, endpoint, **kwargs):
        self.calls.append((endpoint, kwargs)); self.request_count += 1
        payload = self.responses.pop(0)
        if isinstance(payload, Exception):
            raise payload
        raw = json.dumps(payload)
        self.captures.append(CapturedResponse(endpoint, {}, payload, raw, NOW))
        return WireResponse(payload, raw, {}, NOW)


def profile():
    return [{"symbol": "MOCK", "currency": "USD", "exchange": "NASDAQ"}]


def reference():
    return {"status": "OK", "results": {"ticker": "MOCK", "market": "stocks", "locale": "us",
        "currency_name": "usd", "primary_exchange": "XNAS", "active": True, "name": "Mock Data"}}


def history_request(**changes):
    return AdapterHistoryRequest(**{**IDENTITY, "start_date": "2025-01-02", "end_date": "2025-01-03", **changes})


def test_fmp_real_quote_mapping_and_profile_currency():
    client = MockTransport([profile(), [{"symbol":"MOCK", "price":125.5, "timestamp":1767373200,
        "changePercentage":1.5, "volume":100, "yearHigh":150, "yearLow":100}]])
    result = asyncio.run(FMPProvider("key", transport=client).get_quote(MarketDataRequest(**IDENTITY)))
    assert str(result.current_price) == "125.5" and result.currency == "USD"
    assert result.price_type == "unknown" and result.source_timestamp != result.observed_at
    assert len(client.calls) == 2 and client.calls[0][0].endswith("/profile")


def test_fmp_history_split_basis_missing_optional_fields_and_sorting():
    client = MockTransport([profile(), [{"symbol":"MOCK","date":"2025-01-03","close":12},
        {"symbol":"MOCK","date":"2025-01-02","close":11}]])
    result = asyncio.run(FMPProvider("key", transport=client).get_history(history_request()))
    assert [p.date.isoformat() for p in result.points] == ["2025-01-02","2025-01-03"]
    assert all(p.adjustment_state == "adjusted" for p in result.points)
    assert "dividend" in result.warnings[0]
    assert client.calls[1][1]["params"]["from"] == "2025-01-02"


@pytest.mark.parametrize("bad", [{"symbol":"OTHER","currency":"USD","exchange":"NASDAQ"},
    {"symbol":"MOCK","currency":"EUR","exchange":"NASDAQ"},
    {"symbol":"MOCK","exchange":"NASDAQ"},
    {"symbol":"MOCK","currency":"USD","exchange":"NYSE"}])
def test_fmp_rejects_identity_currency_and_venue_mismatch(bad):
    with pytest.raises(MarketDataProviderError):
        asyncio.run(FMPProvider("key", transport=MockTransport([[bad]])).get_quote(MarketDataRequest(**IDENTITY)))


def test_fmp_unadjusted_request_does_not_silently_use_adjusted():
    client = MockTransport([])
    with pytest.raises(MarketDataProviderError) as exc:
        asyncio.run(FMPProvider("key", transport=client).get_history(history_request(adjustment="unadjusted")))
    assert exc.value.code == "PROVIDER_UNSUPPORTED_BASIS" and not client.calls


def test_massive_quote_never_substitutes_prior_day_price():
    client = MockTransport([reference(), {"status":"OK","ticker":{"ticker":"MOCK","prevDay":{"c":10}}}])
    with pytest.raises(MarketDataProviderError) as exc:
        asyncio.run(MassiveProvider("key",transport=client).get_quote(MarketDataRequest(**IDENTITY)))
    assert exc.value.code == "PROVIDER_QUOTE_UNAVAILABLE"


def test_massive_history_partial_pagination_and_no_untrusted_next_url_fetch():
    # January 2, 2025 midnight America/New_York.
    client = MockTransport([reference(), {"status":"OK","ticker":"MOCK","adjusted":False,
        "results":[{"c":10,"t":1735794000000}], "next_url":"https://evil.test/steal"}])
    result = asyncio.run(MassiveProvider("key",transport=client).get_history(history_request()))
    assert result.coverage == "partial" and len(result.points) == 1
    assert result.gaps[0].code == "PROVIDER_PAGINATION_REJECTED"
    assert len(client.calls) == 2
    assert result.points[0].date.isoformat() == "2025-01-02"


def test_massive_rejects_undeclared_adjustment_state():
    client = MockTransport([reference(), {"status":"OK","ticker":"MOCK","adjusted":True,"results":[]}])
    with pytest.raises(MarketDataProviderError) as exc:
        asyncio.run(MassiveProvider("key",transport=client).get_history(history_request()))
    assert exc.value.code == "PROVIDER_HISTORY_BASIS_MISMATCH"


def test_massive_actions_current_endpoint_and_distinct_dates():
    split={"ticker":"MOCK","id":"split1","execution_date":"2025-01-02","split_from":1,"split_to":4,"adjustment_type":"forward_split"}
    dividend={"ticker":"MOCK","id":"div1","ex_dividend_date":"2025-01-03","declaration_date":"2024-12-01",
        "pay_date":"2025-01-20","cash_amount":0.5,"currency":"USD","distribution_type":"recurring"}
    client=MockTransport([{"status":"OK","results":[split]}, {"status":"OK","results":[dividend]}])
    result=asyncio.run(MassiveProvider("key",transport=client).get_actions(AdapterActionRequest(**IDENTITY,
        start_date="2025-01-01",end_date="2025-01-05")))
    assert result.coverage=="complete" and len(result.actions)==2
    assert client.calls[0][0].endswith("/stocks/v1/splits")
    assert result.actions[0].new_shares==4
    assert result.actions[1].announcement_date != result.actions[1].ex_date
    assert result.actions[1].publication_time is None


def test_factory_explicit_configuration_has_no_fallback(monkeypatch):
    from app.services.market_data import factory
    monkeypatch.setattr(factory,"get_settings",lambda: SimpleNamespace(market_data_provider="massive",massive_api_key=None,
        fmp_api_key="configured-other-key",alpha_vantage_api_key=None))
    with pytest.raises(MarketDataProviderError) as exc:
        factory.get_market_data_provider()
    assert exc.value.code == "PROVIDER_NOT_CONFIGURED"
    assert isinstance(factory.get_market_data_provider("fmp"),FMPProvider)
