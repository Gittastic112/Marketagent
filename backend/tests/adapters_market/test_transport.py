import io
import json
from urllib.error import HTTPError

import pytest

from app.providers.market_data import transport
from app.services.market_data.base import MarketDataProviderError


class Response:
    def __init__(self, body=b'{}', headers=None, status=200):
        self.body = io.BytesIO(body)
        self.headers = {"content-type": "application/json", **(headers or {})}
        self.status = status
    def read1(self, n):
        return self.body.read(n)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass


def opener(monkeypatch, response):
    seen = {}
    class Opener:
        def open(self, req, timeout):
            seen["request"], seen["timeout"] = req, timeout
            if isinstance(response, Exception):
                raise response
            return response
    def build(*handlers):
        seen["handlers"] = handlers
        return Opener()
    monkeypatch.setattr(transport.request, "build_opener", build)
    return seen


def test_actual_fixed_request_boundary_has_no_proxies_redirects_and_bounded_timeout(monkeypatch):
    seen = opener(monkeypatch, Response(b'[{"symbol":"MOCK"}]'))
    result = transport.fetch_fixed("fmp", "https://financialmodelingprep.com/stable/quote", params={"symbol": "MOCK", "apikey": "secret"})
    assert result.payload == [{"symbol": "MOCK"}]
    assert seen["timeout"] == 15
    assert seen["handlers"][0].proxies == {}
    assert isinstance(seen["handlers"][1], transport.NoRedirect)
    assert seen["request"].get_header("Accept-encoding") == "identity"


@pytest.mark.parametrize("url", ["http://financialmodelingprep.com/stable/quote", "https://127.0.0.1/x",
    "https://financialmodelingprep.com@evil.test/x", "https://financialmodelingprep.com:8443/x",
    "https://financialmodelingprep.com/x?apikey=secret"])
def test_unallowlisted_urls_never_reach_transport(url):
    with pytest.raises(MarketDataProviderError, match="allowlisted"):
        transport.fetch_fixed("fmp", url)


@pytest.mark.parametrize("body,headers,code", [(b'{}', {"content-encoding": "gzip"}, "PROVIDER_RESPONSE_LIMIT"),
    (b'{}', {"content-length": "6000000"}, "PROVIDER_RESPONSE_LIMIT"),
    (b'{"value":NaN}', {}, "PROVIDER_INVALID_RESPONSE"),
    (b'not json', {}, "PROVIDER_INVALID_RESPONSE")])
def test_response_limits_and_invalid_json(monkeypatch, body, headers, code):
    opener(monkeypatch, Response(body, headers))
    with pytest.raises(MarketDataProviderError) as exc:
        transport.fetch_fixed("fmp", "https://financialmodelingprep.com/stable/quote")
    assert exc.value.code == code


def test_actual_stream_parser_ignores_notification_and_matches_rpc_id(monkeypatch):
    body = b': keepalive\n\ndata: {"jsonrpc":"2.0","method":"notifications/progress"}\n\nevent: message\ndata: {"jsonrpc":"2.0","id":9,\ndata: "result":{"ok":true}}\n\n'
    opener(monkeypatch, Response(body, {"content-type": "text/event-stream;charset=UTF-8"}))
    result = transport.fetch_fixed("nse_mcp", "https://mcp.nseindia.in/bhavcopy/cm/mcp", payload={"id": 9}, rpc_id=9)
    assert result.payload["result"] == {"ok": True}


def test_dropped_sse_stream_is_not_empty_success(monkeypatch):
    opener(monkeypatch, Response(b'data: {"jsonrpc":"2.0","id":1', {"content-type": "text/event-stream"}))
    with pytest.raises(MarketDataProviderError) as exc:
        transport.fetch_fixed("nse_mcp", "https://mcp.nseindia.in/bhavcopy/cm/mcp", rpc_id=1)
    assert exc.value.code == "PROVIDER_INCOMPLETE_STREAM" and exc.value.retryable


def test_rate_limit_is_sanitized_and_does_not_retry(monkeypatch):
    seen = opener(monkeypatch, HTTPError("https://financialmodelingprep.com/?apikey=secret", 429, "secret", {}, None))
    with pytest.raises(MarketDataProviderError) as exc:
        transport.fetch_fixed("fmp", "https://financialmodelingprep.com/stable/quote")
    assert exc.value.code == "PROVIDER_RATE_LIMITED" and exc.value.retryable
    assert "secret" not in str(exc.value)


def test_successful_credential_echo_is_rejected_before_source_capture(monkeypatch):
    import asyncio
    from datetime import datetime, timezone
    def fetch(*args,**kwargs):
        return transport.WireResponse({'echo':'sensitive-token'},'{"echo":"sensitive-token"}',{},datetime.now(timezone.utc))
    monkeypatch.setattr(transport,'fetch_fixed',fetch)
    client=transport.AdapterTransport('fmp')
    with pytest.raises(MarketDataProviderError) as exc:
        asyncio.run(client.request('https://financialmodelingprep.com/stable/quote',params={'apikey':'sensitive-token'}))
    assert exc.value.code=='PROVIDER_CREDENTIAL_ECHO' and client.captures==[]
