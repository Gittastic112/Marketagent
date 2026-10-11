from contextlib import contextmanager
import json

import pytest

from app.services import sec_xbrl_extractor as extractor


def install_stream(monkeypatch, chunks, headers=None):
    calls = []
    state = {"closed": False, "read": 0}

    class Response:
        def raise_for_status(self):
            pass

        def iter_bytes(self):
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

    monkeypatch.setattr(extractor.httpx, "stream", stream)
    monkeypatch.setattr(extractor, "validate_safe_url", lambda url: url)
    return calls, state


def test_companyfacts_stream_uses_fixed_host_timeout_and_no_redirects(monkeypatch):
    raw = json.dumps({"cik": 320193, "facts": {}}).encode()
    calls, state = install_stream(monkeypatch, [raw[:10], raw[10:]])
    assert extractor.fetch_company_facts("320193", user_agent="Test test@example.com")["cik"] == 320193
    args, options = calls[0]
    assert args == ("GET", "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json")
    assert options["timeout"] == 20
    assert options["follow_redirects"] is False
    assert state["closed"] is True


@pytest.mark.parametrize("declared_length", [None, "1000", "not-a-number"])
def test_companyfacts_size_limit_checks_headers_and_decoded_chunks(monkeypatch, declared_length):
    monkeypatch.setattr(extractor, "MAX_COMPANY_FACTS_BYTES", 8)
    headers = {} if declared_length is None else {"content-length": declared_length}
    _, state = install_stream(monkeypatch, [b"12345678", b"9", b"must not read"], headers)
    with pytest.raises(ValueError, match="size limit"):
        extractor.fetch_company_facts("320193", user_agent="Test test@example.com")
    assert state["closed"] is True
    assert state["read"] == (0 if declared_length == "1000" else 2)


def test_companyfacts_stream_enforces_elapsed_deadline(monkeypatch):
    _, state = install_stream(monkeypatch, [b"{}"])
    clock = iter([0, 61])
    monkeypatch.setattr(extractor.time, "monotonic", lambda: next(clock))
    with pytest.raises(ValueError, match="time limit"):
        extractor.fetch_company_facts("320193", user_agent="Test test@example.com")
    assert state["closed"] is True


@pytest.mark.parametrize("payload", [b"not json", b"[]", b'{"cik": 1}'])
def test_companyfacts_rejects_invalid_payloads(monkeypatch, payload):
    _, state = install_stream(monkeypatch, [payload])
    with pytest.raises(ValueError):
        extractor.fetch_company_facts("320193", user_agent="Test test@example.com")
    assert state["closed"] is True
