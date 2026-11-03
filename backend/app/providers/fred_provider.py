import logging
from typing import Any

from app.providers.base import BaseMacroProvider
from app.providers.fixed_json import NoRedirect as _NoRedirect, fetch_json, read_json

logger = logging.getLogger(__name__)
MAX_RESPONSE_BYTES = 5_000_000


def _read_json_response(response) -> dict[str, Any]:
    return read_json(response, max_bytes=MAX_RESPONSE_BYTES)


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
        try:
            return fetch_json(f"{self.base_url}/{endpoint}", params, max_bytes=MAX_RESPONSE_BYTES)
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
