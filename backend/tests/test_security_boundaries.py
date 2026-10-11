import asyncio
import socket
from contextlib import contextmanager
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import httpx
import pytest
from fastapi import HTTPException

from app.core.security import validate_safe_url
from app.core.request_limits import RequestLimitMiddleware
from app.providers import safe_http
from app.services.workbook_safety import validate_workbook_bytes


@pytest.mark.parametrize("url", ["http://[::1]/", "http://[::ffff:127.0.0.1]/", "http://169.254.169.254/",
    "http://100.64.0.1/", "http://224.0.0.1/", "http://user:password@example.com/", "http://example.com\\@localhost/",
    "http://example.com/\n", "http://localhost./", "http://host.docker.internal/"])
def test_unsafe_urls_rejected_without_fetch(url):
    with pytest.raises(ValueError): validate_safe_url(url)


def test_all_dns_answers_checked_and_resolution_failure_is_closed(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *_a, **_k: [(2, 1, 6, "", ("8.8.8.8", 80)), (10, 1, 6, "", ("::1", 80, 0, 0))])
    with pytest.raises(ValueError): validate_safe_url("https://mixed.example/")
    def fail(*_a, **_k): raise socket.gaierror()
    monkeypatch.setattr(socket, "getaddrinfo", fail)
    with pytest.raises(ValueError, match="could not be resolved"): validate_safe_url("https://missing.example/")


@pytest.mark.parametrize("case", ["ok", "redirect", "declared_large", "chunked_large", "compressed"])
def test_fetch_pins_socket_and_tls_name_and_bounds_responses(monkeypatch, case):
    monkeypatch.setattr(safe_http, "public_url_addresses", lambda _u: ("93.184.216.34",))
    captured = {}
    class Client:
        def __init__(self, **kwargs): captured.update(kwargs)
        def __enter__(self): return self
        def __exit__(self, *_a): pass
        @contextmanager
        def stream(self, method, url, **kwargs):
            captured.update(kwargs, url=url, method=method)
            headers = {"content-length": "999"} if case == "declared_large" else {}
            if case == "compressed": headers["content-encoding"] = "gzip"
            response = httpx.Response(302 if case == "redirect" else 200, headers=headers,
                stream=httpx.ByteStream(b"123456" if case == "chunked_large" else b"ok"), request=httpx.Request(method, url))
            yield response
    monkeypatch.setattr(safe_http.httpx, "Client", Client)
    if case == "ok": assert safe_http.fetch_public_text("https://evidence.example/report", max_bytes=4) == "ok"
    else:
        with pytest.raises((ValueError, httpx.HTTPStatusError)):
            safe_http.fetch_public_text("https://evidence.example/report", max_bytes=4)
    assert captured["url"].host == "93.184.216.34"
    assert captured["headers"]["Host"] == "evidence.example"
    assert captured["extensions"]["sni_hostname"] == "evidence.example"
    assert not captured["trust_env"] and not captured["follow_redirects"]


@pytest.mark.parametrize("declared,chunks,allowed", [(b"999", [b"small"], False), (None, [b"1234", b"5678"], False),
    (b"1", [b"1234", b"5678"], False), (None, [b"12", b"34"], True), (b"-1", [b""], False)])
def test_request_limit_applies_before_application(declared, chunks, allowed):
    sent, called = [], []
    async def app(_scope, receive, _send):
        called.append((await receive())["body"])
    async def receive():
        return {"type": "http.request", "body": chunks.pop(0), "more_body": len(chunks) > 0}
    async def send(message): sent.append(message)
    asyncio.run(RequestLimitMiddleware(app, max_bytes=4)({"type": "http", "headers": [] if declared is None else [(b"content-length", declared)]}, receive, send))
    if allowed: assert called == [b"1234"]
    else: assert not called and sent[0]["status"] == 413


def test_validation_does_not_echo_private_request_payload(client):
    response = client.post("/companies", json={"name": "private-should-not-echo", "ticker": {"password": "private-should-not-echo"}})
    assert response.status_code == 422
    assert "private-should-not-echo" not in response.text
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_rate_limits_cover_nested_routes_and_keep_structured_errors(client):
    from app.main import app
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    original = app.state.limiter
    app.state.limiter = Limiter(key_func=get_remote_address, default_limits=["2/minute"])
    try:
        assert client.get("/companies").status_code == 200
        assert client.get("/companies").status_code == 200
        response = client.get("/companies")
        assert response.status_code == 429
        assert response.json()["errors"][0]["code"] == "RATE_LIMITED"
        assert client.get("/api/health").status_code == 200
    finally:
        app.state.limiter = original


def test_legacy_token_storage_cannot_accept_credentials(client, db):
    from sqlalchemy import func, select
    from app.models.oauth_token import OAuthToken
    response = client.post("/oauth/store-token", json={"provider_name": "mock", "access_token": "test-not-a-real-token"})
    assert response.status_code == 503 and "test-not-a-real-token" not in response.text
    assert db.scalar(select(func.count()).select_from(OAuthToken)) == 0
    assert client.get("/oauth/status").json()["data"] == []


def test_workbook_expansion_and_invalid_archive_rejected():
    with pytest.raises(HTTPException): validate_workbook_bytes(b"not a workbook")
    body = BytesIO()
    with ZipFile(body, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/worksheets/sheet1.xml", b"x" * (17 * 1024 * 1024))
    with pytest.raises(HTTPException, match="oversized"):
        validate_workbook_bytes(body.getvalue())


def test_rss_dtd_entities_and_oversized_inline_payloads_are_rejected():
    from app.services.rss_ingestion import parse_rss_items
    from defusedxml.common import DefusedXmlException
    from xml.etree.ElementTree import ParseError
    with pytest.raises(DefusedXmlException):
        parse_rss_items('<!DOCTYPE rss [<!ENTITY content "expanded">]><rss>&content;</rss>')
    with pytest.raises(ParseError):
        parse_rss_items("x" * (4 * 1024 * 1024 + 1))
