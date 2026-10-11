import json
import logging
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

from app.providers.base import BaseMacroProvider

logger = logging.getLogger(__name__)
MAX_RESPONSE_BYTES = 5_000_000


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _read_json_response(response) -> dict[str, Any]:
    headers = response.headers
    declared = headers.get("content-length")
    if headers.get("content-encoding", "identity").lower() not in {"", "identity"}:
        raise RuntimeError("FRED returned an unsupported compressed response.")
    if declared is not None and (not declared.isdecimal() or int(declared) > MAX_RESPONSE_BYTES):
        raise RuntimeError("FRED response exceeded the configured size limit.")
    started, raw = time.monotonic(), bytearray()
    while chunk := response.read(min(64 * 1024, MAX_RESPONSE_BYTES + 1 - len(raw))):
        if time.monotonic() - started > 30 or len(raw) + len(chunk) > MAX_RESPONSE_BYTES:
            raise RuntimeError("FRED response exceeded the configured time or size limit.")
        raw.extend(chunk)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("FRED returned an invalid JSON response.") from None
    if not isinstance(payload, dict):
        raise RuntimeError("FRED returned an unexpected response shape.")
    return payload


class FredProvider(BaseMacroProvider):
    """
    Provider for Federal Reserve Economic Data (FRED).
    Requires a FRED API key.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred"

    @property
    def provider_name(self) -> str:
        return "FRED"

    def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        # FRED requires a query key. urllib avoids httpx's full-URL INFO logs;
        # a fixed TLS endpoint, no proxy and no redirect keep it at that endpoint.
        if self.base_url != "https://api.stlouisfed.org/fred":
            raise ValueError("Unsupported FRED endpoint.")
        request = urllib.request.Request(f"{self.base_url}/{endpoint}?{urllib.parse.urlencode(params)}",
            headers={"User-Agent": "Market Intelligence Engine", "Accept-Encoding": "identity"})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
        try:
            with opener.open(request, timeout=20) as response:
                return _read_json_response(response)
        except Exception:
            raise RuntimeError("FRED request failed or exceeded processing limits.") from None

    def fetch_series_info(self, series_id: str) -> dict[str, Any]:
        """Fetch metadata about a specific FRED series."""
        if not self.api_key:
            raise ValueError("FRED API key is required to fetch series data.")

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
        }
        data = self._request("series", params)
        series = data.get("seriess")
        if not isinstance(series, list) or not series or not isinstance(series[0], dict):
            raise RuntimeError("FRED returned invalid or missing series metadata.")
        return series[0]

    def fetch_observations(
        self,
        series_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch the latest observations for a given FRED series."""
        if not self.api_key:
            raise ValueError("FRED API key is required to fetch observations.")

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit,
        }
        data = self._request("series/observations", params)
        observations = data.get("observations", [])
        if not isinstance(observations, list):
            raise RuntimeError("FRED returned invalid observation data.")
        return observations
