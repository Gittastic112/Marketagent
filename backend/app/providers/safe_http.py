"""Bounded public-source GETs: pinned DNS, verified TLS, no redirects or proxies."""
import time
import json

import httpx

from app.core.security import public_url_addresses


def read_bounded_response(response: httpx.Response, *, max_bytes: int, started: float) -> bytes:
    response.raise_for_status()
    if response.headers.get("content-encoding", "identity").lower() not in {"identity", ""}:
        raise ValueError("Compressed source responses are not supported")
    declared = response.headers.get("content-length")
    if declared is not None and (not declared.isdecimal() or int(declared) > max_bytes):
        raise ValueError("Source response exceeds the size limit")
    body = bytearray()
    for chunk in response.iter_bytes(chunk_size=64 * 1024):
        if time.monotonic() - started > 30 or len(body) + len(chunk) > max_bytes:
            raise ValueError("Source response exceeds the time or size limit")
        body.extend(chunk)
    return bytes(body)


def fetch_public_text(url: str, *, max_bytes: int, headers: dict[str, str] | None = None) -> str:
    addresses = public_url_addresses(url)
    original = httpx.URL(url)
    # Use the numeric destination for the socket, but the original authority for
    # HTTP virtual hosting and TLS certificate verification (httpcore extension).
    target = original.copy_with(host=addresses[0])
    safe_headers = {**(headers or {}), "Host": original.netloc.decode(), "Accept-Encoding": "identity"}
    started = time.monotonic()
    with httpx.Client(trust_env=False, follow_redirects=False, timeout=20) as client:
        with client.stream("GET", target, headers=safe_headers,
                           extensions={"sni_hostname": original.host}) as response:
            return read_bounded_response(response, max_bytes=max_bytes, started=started).decode(
                response.encoding or "utf-8", errors="replace")


def fetch_public_json(url: str, *, max_bytes: int, headers: dict[str, str] | None = None) -> dict:
    try:
        payload = json.loads(fetch_public_text(url, max_bytes=max_bytes, headers=headers))
    except json.JSONDecodeError:
        raise ValueError("Source returned invalid JSON") from None
    if not isinstance(payload, dict):
        raise ValueError("Source returned an unexpected JSON shape")
    return payload
