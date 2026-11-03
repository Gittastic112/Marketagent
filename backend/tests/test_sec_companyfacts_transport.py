from contextlib import contextmanager
import json

import pytest

from app.services import sec_xbrl_extractor as extractor
from app.providers import safe_http


def install_stream(monkeypatch, chunks, headers=None):
    calls = []
    state = {"closed": False, "read": 0}

    class Response:
        encoding = "utf-8"
        def raise_for_status(self):
            pass

        def iter_bytes(self, chunk_size):
            for chunk in chunks:
                state["read"] += 1
                yield chunk

    response = Response()
    response.headers = headers or {}

    @contextmanager
    def stream(*args, **kwargs):
        calls.append((args, kwargs))
        try:
            yield response
        finally:
            state["closed"] = True

    class Client:
        def __init__(self, **options): self.options = options
        def __enter__(self): return self
        def __exit__(self, *_args): pass
        def stream(self, *args, **kwargs): return stream(*args, **self.options, **kwargs)
    monkeypatch.setattr(safe_http.httpx, "Client", Client)
    monkeypatch.setattr(safe_http, "public_url_addresses", lambda url: ("93.184.216.34",))
    return calls, state


def test_companyfacts_stream_uses_fixed_host_timeout_and_no_redirects(monkeypatch):
    raw = json.dumps({"cik": 320193, "facts": {}}).encode()
    calls, state = install_stream(monkeypatch, [raw[:10], raw[10:]])
    assert extractor.fetch_company_facts("320193", user_agent="Test test@example.com")["cik"] == 320193
    args, options = calls[0]
    assert args[0] == "GET"
    assert str(args[1]) == "https://93.184.216.34/api/xbrl/companyfacts/CIK0000320193.json"
    assert options["headers"]["Host"] == "data.sec.gov"
    assert options["extensions"]["sni_hostname"] == "data.sec.gov"
    assert options["timeout"] == 20
    assert options["follow_redirects"] is False
    assert options["trust_env"] is False
    assert state["closed"] is True


@pytest.mark.parametrize("declared_length", [None, "1000", "not-a-number"])
def test_companyfacts_size_limit_checks_headers_and_decoded_chunks(monkeypatch, declared_length):
    monkeypatch.setattr(extractor, "MAX_COMPANY_FACTS_BYTES", 8)
    headers = {} if declared_length is None else {"content-length": declared_length}
    _, state = install_stream(monkeypatch, [b"12345678", b"9", b"must not read"], headers)
    with pytest.raises(ValueError, match="size limit"):
        extractor.fetch_company_facts("320193", user_agent="Test test@example.com")
    assert state["closed"] is True
    assert state["read"] == (2 if declared_length is None else 0)


def test_companyfacts_stream_enforces_elapsed_deadline(monkeypatch):
    _, state = install_stream(monkeypatch, [b"{}"])
    clock = iter([0, 61])
    monkeypatch.setattr(safe_http.time, "monotonic", lambda: next(clock))
    with pytest.raises(ValueError, match="time or size limit"):
        extractor.fetch_company_facts("320193", user_agent="Test test@example.com")
    assert state["closed"] is True


@pytest.mark.parametrize("payload", [b"not json", b"[]", b'{"cik": 1}'])
def test_companyfacts_rejects_invalid_payloads(monkeypatch, payload):
    _, state = install_stream(monkeypatch, [payload])
    with pytest.raises(ValueError):
        extractor.fetch_company_facts("320193", user_agent="Test test@example.com")
    assert state["closed"] is True
