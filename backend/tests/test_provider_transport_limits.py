"""No external requests: exercise transport limits with streamed responses."""
from contextlib import contextmanager
from io import BytesIO

import httpx
import pytest

from app.providers import ai_provider, fred_provider, safe_http


@pytest.mark.parametrize("headers,body", [
    ({"content-length": "5000001"}, b"{}"),
    ({"content-encoding": "gzip"}, b"{}"),
    ({"content-length": "-1"}, b"{}"),
    ({}, b"x" * 5_000_001),
])
def test_fred_bounds_body_and_encoding(headers, body):
    class Response(BytesIO):
        pass
    response = Response(body)
    response.headers = headers
    with pytest.raises(RuntimeError):
        fred_provider._read_json_response(response)


def test_fred_disables_redirects_and_proxies_and_sanitizes_errors(monkeypatch):
    import urllib.error
    import urllib.request
    captured = {}

    class Opener:
        def open(self, request, timeout):
            captured.update(request=request, timeout=timeout)
            raise urllib.error.HTTPError(request.full_url, 302, "private-key", {}, None)

    def opener(*handlers):
        captured["handlers"] = handlers
        return Opener()

    monkeypatch.setattr(urllib.request, "build_opener", opener)
    with pytest.raises(RuntimeError) as error:
        fred_provider.FredProvider("private-key").fetch_observations("NFCI")
    assert "private-key" not in str(error.value)
    assert error.value.__suppress_context__
    assert captured["timeout"] == 20
    assert any(isinstance(h, urllib.request.ProxyHandler) and h.proxies == {} for h in captured["handlers"])
    redirect = next(h for h in captured["handlers"] if isinstance(h, urllib.request.HTTPRedirectHandler))
    assert redirect.redirect_request(None, None, 302, "redirect", {}, "http://127.0.0.1/") is None


@pytest.mark.parametrize("url", ["http://api.stlouisfed.org/fred", "https://localhost/fred", "https://api.stlouisfed.org.evil/fred"])
def test_fred_cannot_be_redirected_through_configured_base(url):
    provider = fred_provider.FredProvider("private-key")
    provider.base_url = url
    with pytest.raises(ValueError, match="endpoint"):
        provider.fetch_observations("NFCI")


@pytest.mark.parametrize("case", ["oversized", "compressed", "redirect", "timeout"])
def test_gemini_stream_is_bounded_without_secret_logs(monkeypatch, caplog, case):
    captured = {}
    class Client:
        def __init__(self, **kwargs): captured.update(kwargs)
        def __enter__(self): return self
        def __exit__(self, *_args): pass
        @contextmanager
        def stream(self, method, url, **kwargs):
            captured.update(kwargs)
            headers = {"content-length": "99999999"} if case == "oversized" else {}
            if case == "compressed": headers["content-encoding"] = "gzip"
            if case == "timeout": raise httpx.ReadTimeout("private-key private-document")
            yield httpx.Response(302 if case == "redirect" else 200, headers=headers,
                request=httpx.Request(method, url), stream=httpx.ByteStream(b"{}"))
    monkeypatch.setattr(ai_provider.httpx, "Client", Client)
    with pytest.raises(ai_provider.GeminiRequestError) as error:
        ai_provider.GeminiAIProvider("private-key").generate_summary("private-document")
    assert not captured["trust_env"] and not captured["follow_redirects"]
    assert "private-key" not in str(error.value) + caplog.text
    assert "private-document" not in str(error.value) + caplog.text


def test_stream_deadline_and_chunked_limit(monkeypatch):
    request = httpx.Request("GET", "https://example.invalid")
    response = httpx.Response(200, request=request, stream=httpx.ByteStream(b"123456"))
    with pytest.raises(ValueError):
        safe_http.read_bounded_response(response, max_bytes=4, started=safe_http.time.monotonic())
    monkeypatch.setattr(safe_http.time, "monotonic", lambda: 100)
    response = httpx.Response(200, request=request, stream=httpx.ByteStream(b"{}"))
    with pytest.raises(ValueError, match="time"):
        safe_http.read_bounded_response(response, max_bytes=4, started=0)


def test_sec_default_json_paths_use_the_bounded_transport(monkeypatch):
    from app.services import sec_ingestion, sec_xbrl_extractor
    calls = []
    def fetch(url, **kwargs):
        calls.append((url, kwargs))
        if "companyfacts" in url: return {"cik": 320193}
        if "submissions" in url: return {"filings": {"recent": {}}}
        return {"0": {"ticker": "AAPL", "title": "Apple", "cik_str": 320193}}
    monkeypatch.setattr(sec_ingestion, "fetch_public_json", fetch)
    monkeypatch.setattr(sec_xbrl_extractor, "fetch_public_json", fetch)
    assert sec_ingestion.lookup_cik_for_ticker("AAPL", user_agent="Mock Data test@example.invalid") == "0000320193"
    assert sec_ingestion.fetch_recent_sec_filing_metadata("320193", user_agent="Mock Data test@example.invalid") == []
    assert sec_xbrl_extractor.fetch_company_facts("320193", user_agent="Mock Data test@example.invalid")["cik"] == 320193
    assert all(0 < kwargs["max_bytes"] <= 40 * 1024 * 1024 for _, kwargs in calls)
