"""Mock Data responses. No paid provider or key is used."""
import asyncio
from datetime import datetime, timezone
from io import BytesIO
import logging
import urllib.error
import urllib.request

import pytest

from app.providers import fixed_json
from app.services.market_data import alpha_vantage as module
from app.services.market_data.base import MarketDataProviderError, MarketDataRequest


@pytest.mark.parametrize("failure,code", [(302, "PROVIDER_UNAVAILABLE"), (429, "PROVIDER_RATE_LIMITED"),
    ("timeout", "PROVIDER_TIMEOUT"), ("oversized", "PROVIDER_UNAVAILABLE"), ("compressed", "PROVIDER_UNAVAILABLE")])
def test_query_key_never_enters_logs_or_public_errors_and_response_is_bounded(monkeypatch, caplog, failure, code):
    captured = {}
    class Response(BytesIO):
        headers = {"content-length": "5000001"} if failure == "oversized" else {"content-encoding": "gzip"}
    class Opener:
        def open(self, request, timeout):
            captured.update(request=request, timeout=timeout)
            if isinstance(failure, int):
                raise urllib.error.HTTPError(request.full_url, failure, "private-key", {}, None)
            if failure == "timeout":
                raise TimeoutError("private-key")
            return Response(b"{}")
    def opener(*handlers):
        captured["handlers"] = handlers
        return Opener()
    monkeypatch.setattr(urllib.request, "build_opener", opener)
    caplog.set_level(logging.INFO)
    with pytest.raises(MarketDataProviderError) as error:
        asyncio.run(module.AlphaVantageProvider("private-key").get_quote(MarketDataRequest(market="US", ticker="MOCK")))
    assert error.value.code == code
    assert error.value.__suppress_context__
    assert "private-key" not in str(error.value) + caplog.text
    assert captured["timeout"] == 10
    assert captured["request"].headers["Accept-encoding"] == "identity"
    assert any(isinstance(h, urllib.request.ProxyHandler) and not h.proxies for h in captured["handlers"])
    redirect = next(h for h in captured["handlers"] if isinstance(h, fixed_json.NoRedirect))
    assert redirect.redirect_request(None, None, 302, "", {}, "http://127.0.0.1/") is None


@pytest.mark.parametrize("url", ["http://www.alphavantage.co/query", "https://localhost/query", "https://www.alphavantage.co.evil/query"])
def test_changed_base_is_rejected_before_any_request(url, monkeypatch):
    monkeypatch.setattr(urllib.request, "build_opener", lambda *_: pytest.fail("Invalid endpoint reached transport"))
    provider = module.AlphaVantageProvider("Mock Data key")
    provider.base_url = url
    with pytest.raises(MarketDataProviderError):
        asyncio.run(provider.get_quote(MarketDataRequest(market="US", ticker="MOCK")))


def test_history_sorts_dates_filters_current_future_and_out_of_window_rows(monkeypatch):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 7, 1, 2, tzinfo=timezone.utc)
    monkeypatch.setattr(module, "datetime", Clock)
    async def response(*args, **kwargs):
        return {"Time Series (Daily)": {
            "2026-06-29": {"4. close": "101"}, "2026-07-01": {"4. close": "103"},
            "2026-06-01": {"4. close": "90"}, "2026-06-30": {"4. close": "102"},
            "2026-06-26": {"4. close": "100"}, "bad": {"4. close": "private-input"},
        }}
    provider = module.AlphaVantageProvider("Mock Data key")
    monkeypatch.setattr(provider, "_get_json", response)
    rows = asyncio.run(provider.get_historical_prices(MarketDataRequest(market="US", ticker="MOCK", currency="USD"), 7))
    assert [row.date.isoformat() for row in rows] == ["2026-06-26", "2026-06-29"]
    assert all(row.adjustment_state == "unadjusted" for row in rows)
    assert "America/New_York" in rows[0].warnings[-1]


def test_query_transport_checks_elapsed_time_between_network_reads(monkeypatch):
    class Response(BytesIO):
        headers = {}
        def read(self, *_args):
            pytest.fail("Must not wait for an entire buffered response")
    monkeypatch.setattr(fixed_json.time, "monotonic", lambda: 100)
    with pytest.raises(fixed_json.FixedJsonError) as error:
        fixed_json.read_json(Response(b"{}"), max_bytes=500, started=0)
    assert error.value.kind == "timeout"
