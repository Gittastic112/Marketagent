import json
import logging
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

from app.providers.base import BaseMacroProvider

logger = logging.getLogger(__name__)
MAX_RESPONSE_BYTES = 5_000_000


def _read_json_response(response) -> dict[str, Any]:
    raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise RuntimeError("FRED response exceeded the configured size limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("FRED returned an invalid JSON response.") from exc
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

    def fetch_series_info(self, series_id: str) -> dict[str, Any]:
        """Fetch metadata about a specific FRED series."""
        if not self.api_key:
            raise ValueError("FRED API key is required to fetch series data.")

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
        }
        url = f"{self.base_url}/series?{urllib.parse.urlencode(params)}"

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Market Intelligence Engine"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = _read_json_response(response)
                if "seriess" not in data or len(data["seriess"]) == 0:
                    raise ValueError(f"Series {series_id} not found in FRED.")
                series = data["seriess"][0]
                if not isinstance(series, dict):
                    raise RuntimeError("FRED returned invalid series metadata.")
                return series
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"FRED API error fetching series info: {exc.status} {exc.reason}"
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError("FRED series metadata request failed.") from exc

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
        url = f"{self.base_url}/series/observations?{urllib.parse.urlencode(params)}"

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Market Intelligence Engine"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = _read_json_response(response)
                if "observations" not in data:
                    return []
                observations = data["observations"]
                if not isinstance(observations, list):
                    raise RuntimeError("FRED returned invalid observation data.")
                return observations
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"FRED API error fetching observations: {exc.status} {exc.reason}"
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError("FRED observation request failed.") from exc
