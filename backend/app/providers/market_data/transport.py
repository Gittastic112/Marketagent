"""Fixed-host, bounded JSON/SSE transport; no redirects, proxies or URL logs.

Query-key APIs use urllib because HTTPX's normal INFO logging includes the URL.
No arbitrary user URL or server-provided pagination URL is fetched here.
"""
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import socket
import time
from typing import Any
from urllib import error, parse, request

from app.services.market_data.base import MarketDataProviderError

HOSTS = {
    "fmp": "financialmodelingprep.com",
    "massive": "api.massive.com",
    "openfigi": "api.openfigi.com",
    "nse_mcp": "mcp.nseindia.in",
}
MAX_RESPONSE_BYTES = 5_000_000
MAX_REQUESTS = 32


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def response_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


@dataclass(frozen=True)
class CapturedResponse:
    endpoint: str
    request: dict
    payload: Any
    raw_text: str
    observed_at: datetime

    @property
    def sha256(self) -> str:
        return response_hash(self.payload)


@dataclass(frozen=True)
class WireResponse:
    payload: Any
    raw_text: str
    headers: dict[str, str]
    observed_at: datetime


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def provider_error(provider: str, code: str, message: str, *, status: int = 502, retryable: bool = False):
    return MarketDataProviderError(code=code, message=message, provider=provider,
                                   status_code=status, retryable=retryable)


def _decode_json(text: str, provider: str):
    def bad_constant(value):
        raise ValueError("Non-finite JSON")
    try:
        return json.loads(text, parse_constant=bad_constant)
    except (ValueError, TypeError):
        raise provider_error(provider, "PROVIDER_INVALID_RESPONSE", "Provider returned invalid JSON.") from None


def _read(response, *, provider: str, rpc_id: int | None, notification: bool, started: float) -> WireResponse:
    headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
    if headers.get("content-encoding", "identity").lower() not in {"", "identity"}:
        raise provider_error(provider, "PROVIDER_RESPONSE_LIMIT", "Compressed provider responses are not accepted.")
    declared = headers.get("content-length")
    if declared and (not declared.isdecimal() or int(declared) > MAX_RESPONSE_BYTES):
        raise provider_error(provider, "PROVIDER_RESPONSE_LIMIT", "Provider response exceeds its size limit.")
    observed = datetime.now(timezone.utc)
    if notification and response.status in {200, 202, 204}:
        return WireResponse(None, "", headers, observed)
    sse = headers.get("content-type", "").lower().startswith("text/event-stream")
    body = bytearray()
    pending = b""
    event_data: list[bytes] = []
    while True:
        chunk = response.read1(min(65536, MAX_RESPONSE_BYTES + 1 - len(body)))
        if time.monotonic() - started > 25:
            raise provider_error(provider, "PROVIDER_TIMEOUT", "Provider exceeded the response deadline.", status=504, retryable=True)
        if not chunk:
            break
        body.extend(chunk)
        if len(body) > MAX_RESPONSE_BYTES:
            raise provider_error(provider, "PROVIDER_RESPONSE_LIMIT", "Provider response exceeds its size limit.")
        if sse:
            pending += chunk
            while b"\n" in pending:
                line, pending = pending.split(b"\n", 1)
                line = line.rstrip(b"\r")
                if line.startswith(b"data:"):
                    event_data.append(line[5:].lstrip(b" "))
                elif not line and event_data:
                    try:
                        text = b"\n".join(event_data).decode("utf-8")
                    except UnicodeError:
                        raise provider_error(provider, "PROVIDER_INVALID_RESPONSE", "Provider returned invalid text.") from None
                    event_data = []
                    value = _decode_json(text, provider)
                    if isinstance(value, dict) and value.get("id") == rpc_id:
                        return WireResponse(value, body.decode("utf-8"), headers, observed)
    if sse:
        raise provider_error(provider, "PROVIDER_INCOMPLETE_STREAM", "MCP stream ended before its matching result.", retryable=True)
    try:
        text = body.decode("utf-8")
    except UnicodeError:
        raise provider_error(provider, "PROVIDER_INVALID_RESPONSE", "Provider returned invalid text.") from None
    return WireResponse(_decode_json(text, provider), text, headers, observed)


def fetch_fixed(provider: str, endpoint: str, *, params=None, payload=None, headers=None,
                rpc_id: int | None = None, notification: bool = False) -> WireResponse:
    parsed = parse.urlsplit(endpoint)
    if (parsed.scheme != "https" or parsed.hostname != HOSTS.get(provider)
            or parsed.port not in {None, 443} or parsed.username or parsed.password
            or parsed.query or parsed.fragment):
        raise provider_error(provider, "PROVIDER_ENDPOINT_REJECTED", "Provider endpoint is not allowlisted.")
    url = endpoint + ("?" + parse.urlencode(params) if params else "")
    outgoing = request.Request(url, data=canonical_json(payload).encode() if payload is not None else None,
        headers={"Accept": "application/json", "Accept-Encoding": "identity",
                 "User-Agent": "Marketagent/1 personal-research", "Content-Type": "application/json", **(headers or {})})
    opener = request.build_opener(request.ProxyHandler({}), NoRedirect())
    started = time.monotonic()
    try:
        with opener.open(outgoing, timeout=15) as response:
            return _read(response, provider=provider, rpc_id=rpc_id, notification=notification, started=started)
    except MarketDataProviderError:
        raise
    except error.HTTPError as exc:
        code, status, retry = {
            401: ("PROVIDER_AUTHENTICATION_FAILED", 502, False),
            403: ("PROVIDER_ENTITLEMENT_REQUIRED", 403, False),
            404: ("PROVIDER_NOT_FOUND", 404, False),
            429: ("PROVIDER_RATE_LIMITED", 429, True),
        }.get(exc.code, ("PROVIDER_UNAVAILABLE", 502, exc.code >= 500))
        raise provider_error(provider, code, "Provider could not fulfill the request.", status=status, retryable=retry) from None
    except (TimeoutError, socket.timeout):
        raise provider_error(provider, "PROVIDER_TIMEOUT", "Provider request timed out.", status=504, retryable=True) from None
    except Exception:
        raise provider_error(provider, "PROVIDER_UNAVAILABLE", "Provider request could not be completed.", retryable=True) from None


class AdapterTransport:
    def __init__(self, provider: str):
        self.provider = provider
        self.captures: list[CapturedResponse] = []
        self.request_count = 0

    async def request(self, endpoint: str, *, params=None, payload=None, headers=None,
                      rpc_id=None, notification=False, capture=True) -> WireResponse:
        self.request_count += 1
        if self.request_count > MAX_REQUESTS:
            raise provider_error(self.provider, "PROVIDER_REQUEST_BUDGET", "Provider request budget was exhausted.")
        result = await asyncio.to_thread(fetch_fixed, self.provider, endpoint, params=params,
            payload=payload, headers=headers, rpc_id=rpc_id, notification=notification)
        # A provider that echoes authentication must not turn a successful
        # response into a stored, publicly browseable source document.
        secrets = [str(v) for k, v in (params or {}).items() if k.lower() in {"apikey", "api_key"}]
        for name, value in (headers or {}).items():
            if name.lower() in {"authorization", "x-openfigi-apikey"}:
                secrets.append(str(value).removeprefix("Bearer "))
        if any(len(secret) >= 4 and secret in result.raw_text for secret in secrets):
            raise provider_error(self.provider, "PROVIDER_CREDENTIAL_ECHO", "Provider response cannot be preserved safely.")
        if capture:
            safe_params = {k: v for k, v in (params or {}).items() if k.lower() not in {"apikey", "api_key", "cursor"}}
            self.captures.append(CapturedResponse(endpoint, {"params": safe_params, "body": payload},
                result.payload, result.raw_text, result.observed_at))
        return result
