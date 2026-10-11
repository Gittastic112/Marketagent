"""Bounded public-source GETs: pinned DNS, verified TLS, no redirects or proxies."""
import time

import httpx

from app.core.security import public_url_addresses


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
            response.raise_for_status()  # Includes redirects: do not forward to a new destination.
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
            return bytes(body).decode(response.encoding or "utf-8", errors="replace")
