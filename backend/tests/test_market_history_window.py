"""Mock Data clocks. No exchange calendar or real-time completion is inferred."""
from datetime import datetime, timezone

import pytest

from app.services.market_data.base import MarketDataProviderError, MarketDataRequest
from app.services.market_data.sessions import history_window


@pytest.mark.parametrize("market,instant,start,end,zone", [
    ("US", "2026-07-01T02:00:00+00:00", "2026-06-23", "2026-06-30", "America/New_York"),
    ("IN", "2026-07-01T02:00:00+00:00", "2026-06-24", "2026-07-01", "Asia/Kolkata"),
    ("US", "2026-03-09T04:30:00+00:00", "2026-03-02", "2026-03-09", "America/New_York"),
    ("US", "2026-11-02T04:30:00+00:00", "2026-10-25", "2026-11-01", "America/New_York"),
    ("IN", "2026-09-19T00:00:00+00:00", "2026-09-12", "2026-09-19", "Asia/Kolkata"),
])
def test_market_local_exclusive_cutoff_across_utc_midnight_dst_and_weekends(market, instant, start, end, zone):
    window = history_window(MarketDataRequest(market=market, ticker="MOCK"), 7,
                            now=datetime.fromisoformat(instant))
    assert (window.start.isoformat(), window.end.isoformat(), window.zone.key) == (start, end, zone)
    assert zone in window.warning
    assert "current market-local date" in window.warning


@pytest.mark.parametrize("days", [0, 3651, -1])
def test_history_window_is_bounded(days):
    with pytest.raises(MarketDataProviderError) as error:
        history_window(MarketDataRequest(market="US", ticker="MOCK"), days)
    assert error.value.code == "PROVIDER_INVALID_REQUEST"


def test_unknown_market_does_not_silently_use_utc_or_naive_clock():
    with pytest.raises(MarketDataProviderError):
        history_window(MarketDataRequest(market="OTHER", ticker="MOCK"), 7)
    with pytest.raises(ValueError, match="timezone"):
        history_window(MarketDataRequest(market="US", ticker="MOCK"), 7, now=datetime(2026, 1, 1))
