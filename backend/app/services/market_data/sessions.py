"""Conservative daily history boundaries for the supported research markets."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.services.market_data.base import MarketDataProviderError, MarketDataRequest


@dataclass(frozen=True)
class HistoryWindow:
    start: date
    end: date
    zone: ZoneInfo

    @property
    def warning(self) -> str:
        return (f"Daily history excludes the current market-local date ({self.zone.key}). "
                "Prior-date provider bars are not independently certified exchange closes; "
                "no exchange holiday calendar is applied.")


def history_window(request: MarketDataRequest, days: int, *, now: datetime | None = None) -> HistoryWindow:
    zone_name = {"US": "America/New_York", "IN": "Asia/Kolkata"}.get(request.market)
    if not zone_name or not 1 <= days <= 3650:
        raise MarketDataProviderError(code="PROVIDER_INVALID_REQUEST",
            message="Daily history requires a supported US/India market and 1-3650 calendar days.",
            provider="internal", status_code=422, retryable=False)
    clock = now or datetime.now(timezone.utc)
    if clock.tzinfo is None or clock.utcoffset() is None:
        raise ValueError("A timezone-aware clock is required")
    zone = ZoneInfo(zone_name)
    end = clock.astimezone(zone).date()
    return HistoryWindow(start=end - timedelta(days=days), end=end, zone=zone)
