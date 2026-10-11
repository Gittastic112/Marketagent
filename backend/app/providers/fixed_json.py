"""Bounded fixed-provider JSON requests whose keys must be in query strings.

urllib has no default full-URL INFO log. Keys never appear in errors, redirects
are rejected, and environment proxies are disabled. Normal TLS/DNS applies;
this is not the pinned-DNS transport for arbitrary public document URLs.
"""
import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request


class FixedJsonError(RuntimeError):
    def __init__(self, kind: str, status_code: int | None = None):
        super().__init__("Provider request failed or exceeded processing limits.")
        self.kind = kind
        self.status_code = status_code


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_json(response, *, max_bytes: int, started: float | None = None) -> dict:
    headers = response.headers
    declared = headers.get("content-length")
    if headers.get("content-encoding", "identity").lower() not in {"", "identity"}:
        raise FixedJsonError("invalid")
    if declared is not None and (not declared.isdecimal() or int(declared) > max_bytes):
        raise FixedJsonError("invalid")
    started = time.monotonic() if started is None else started
    body = bytearray()
    # HTTPResponse.read(n) can wait for many packets. read1 returns after one
    # buffered read so an endless trickle still meets the elapsed-time checks.
    while chunk := response.read1(min(64 * 1024, max_bytes + 1 - len(body))):
        if time.monotonic() - started > 30:
            raise FixedJsonError("timeout")
        if len(body) + len(chunk) > max_bytes:
            raise FixedJsonError("invalid")
        body.extend(chunk)
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeError, ValueError):
        raise FixedJsonError("invalid") from None
    if not isinstance(payload, dict):
        raise FixedJsonError("invalid")
    return payload


def fetch_json(url: str, params: dict, *, max_bytes: int, timeout: int = 20) -> dict:
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in {"api.stlouisfed.org", "www.alphavantage.co"}
            or parsed.port not in {None, 443} or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise FixedJsonError("invalid_endpoint")
    request = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}",
        headers={"User-Agent": "Market Intelligence Engine", "Accept-Encoding": "identity"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    started = time.monotonic()
    try:
        with opener.open(request, timeout=timeout) as response:
            return read_json(response, max_bytes=max_bytes, started=started)
    except FixedJsonError:
        raise
    except urllib.error.HTTPError as error:
        raise FixedJsonError("http", error.code) from None
    except (TimeoutError, socket.timeout):
        raise FixedJsonError("timeout") from None
    except Exception:
        raise FixedJsonError("unavailable") from None
