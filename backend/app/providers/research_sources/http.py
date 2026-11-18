"""Bounded requests to fixed transcript endpoints; query keys are never logged."""
import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

from app.providers.fixed_json import NoRedirect
from app.providers.research_sources.errors import SourceAdapterError

ENDPOINTS = {
    "earningscall": "https://api.earningscall.dev/v4/transcript",
    "fmp": "https://financialmodelingprep.com/stable/earning-call-transcript",
}
MAX_BYTES = 8 * 1024 * 1024


def fetch_transcript_json(provider: str, params: dict) -> dict | list:
    if provider not in ENDPOINTS:
        raise SourceAdapterError("UNSUPPORTED_PROVIDER", "Unsupported transcript provider.")
    request = urllib.request.Request(ENDPOINTS[provider] + "?" + urllib.parse.urlencode(params),
        headers={"User-Agent": "Marketagent research", "Accept": "application/json", "Accept-Encoding": "identity"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    started = time.monotonic()
    try:
        with opener.open(request, timeout=15) as response:
            length = response.headers.get("Content-Length")
            if (response.headers.get("Content-Encoding", "identity").lower() not in {"", "identity"}
                    or (length is not None and (not length.isdecimal() or int(length) > MAX_BYTES))):
                raise SourceAdapterError("RESPONSE_LIMIT", "Transcript exceeds the supported response limit.", 502)
            body = bytearray()
            while chunk := response.read1(min(65536, MAX_BYTES + 1 - len(body))):
                body.extend(chunk)
                if len(body) > MAX_BYTES or time.monotonic() - started > 25:
                    raise SourceAdapterError("RESPONSE_LIMIT", "Transcript request exceeded processing limits.", 502)
            payload = json.loads(body.decode("utf-8"))
            if not isinstance(payload, (dict, list)):
                raise ValueError
            return payload
    except SourceAdapterError:
        raise
    except urllib.error.HTTPError as exc:
        catalog = {401: ("PROVIDER_AUTH_FAILED", "Provider credentials were rejected.", 503),
            403: ("PROVIDER_ENTITLEMENT", "This transcript is not available under the configured provider access.", 503),
            404: ("TRANSCRIPT_UNAVAILABLE", "No transcript is available for the requested call.", 404),
            429: ("PROVIDER_RATE_LIMIT", "The transcript provider rate limit was reached.", 429)}
        code, message, status = catalog.get(exc.code, ("PROVIDER_UNAVAILABLE", "Transcript provider request failed.", 502))
        raise SourceAdapterError(code, message, status, retryable=exc.code == 429 or exc.code >= 500) from None
    except (TimeoutError, socket.timeout):
        raise SourceAdapterError("PROVIDER_TIMEOUT", "Transcript provider request timed out.", 504, retryable=True) from None
    except Exception:
        raise SourceAdapterError("PROVIDER_RESPONSE_INVALID", "Transcript provider returned an unusable response.", 502) from None
