import logging
import math
import re
from datetime import date
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

    def fetch_vintage_observations(
        self, series_id: str, *, as_of: date, observation_start: date,
        observation_end: date, mode: str = "as_of", max_pages: int = 5,
    ) -> dict[str, Any]:
        """Retrieve ALFRED revisions, retaining intervals and an explicit cutoff.

        This does not mutate the application's current-value macro table. A
        bounded request may be partial; callers must preserve that status.
        """
        if not self.api_key:
            raise ValueError("FRED API key is required to fetch observations.")
        series_id = series_id.strip().upper()
        if (not re.fullmatch(r"[A-Z0-9_.-]{1,80}", series_id)
                or observation_start > observation_end or as_of > date.today()
                or mode not in {"as_of", "initial_release"} or not 1 <= max_pages <= 10):
            raise ValueError("Invalid FRED vintage request.")
        raw_pages, revisions = [], []
        count = None
        offset = 0
        for _ in range(max_pages):
            params = {
                "series_id": series_id, "api_key": self.api_key, "file_type": "json",
                "realtime_start": "1776-07-04", "realtime_end": as_of.isoformat(),
                "observation_start": observation_start.isoformat(),
                "observation_end": observation_end.isoformat(), "output_type": 1,
                "order_by": "observation_date", "sort_order": "asc", "limit": 1000,
                "offset": offset,
            }
            data = self._request("series/observations", params)
            rows, reported_count = data.get("observations"), data.get("count")
            if (not isinstance(rows, list) or len(rows) > 1000
                    or isinstance(reported_count, bool) or not isinstance(reported_count, int)
                    or reported_count < 0 or len(rows) > max(0, reported_count - offset)
                    or data.get("offset", offset) != offset or (count is not None and count != reported_count)):
                raise RuntimeError("FRED returned inconsistent vintage pagination.")
            count = reported_count
            if not rows and offset < count:
                raise RuntimeError("FRED returned an incomplete vintage page.")
            raw_pages.append(data)
            for row in rows:
                try:
                    observed = date.fromisoformat(row["date"])
                    start = date.fromisoformat(row["realtime_start"])
                    end = date.fromisoformat(row["realtime_end"])
                    raw_value = row["value"]
                    value = None if raw_value == "." else float(raw_value)
                    if (isinstance(raw_value, bool) or (value is not None and not math.isfinite(value))
                            or start > end or not observation_start <= observed <= observation_end
                            or start > as_of):
                        raise ValueError
                except (KeyError, ValueError, TypeError, OverflowError):
                    raise RuntimeError("FRED returned invalid vintage observations.") from None
                revisions.append({"date": observed.isoformat(), "value": value,
                    "raw_value": raw_value, "realtime_start": start.isoformat(),
                    "realtime_end": end.isoformat()})
            offset += len(rows)
            if offset >= count:
                break
        selected: dict[str, dict] = {}
        for row in revisions:
            if mode == "as_of" and row["realtime_end"] < as_of.isoformat():
                continue
            previous = selected.get(row["date"])
            if previous and row["realtime_start"] == previous["realtime_start"]:
                if row["value"] != previous["value"]:
                    raise RuntimeError("FRED returned conflicting vintage observations.")
                continue
            if previous is None or ((row["realtime_start"] > previous["realtime_start"])
                                    if mode == "as_of" else (row["realtime_start"] < previous["realtime_start"])):
                selected[row["date"]] = row
        complete = offset >= (count or 0)
        return {"series_id": series_id, "as_of": as_of.isoformat(), "mode": mode,
            "observations": [selected[key] for key in sorted(selected)], "revisions": revisions,
            "raw_pages": raw_pages, "complete": complete, "fetched_count": offset,
            "expected_count": count, "warnings": [] if complete else ["VINTAGE_PAGE_BUDGET_EXHAUSTED"]}
