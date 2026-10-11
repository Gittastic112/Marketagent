"""Personal-use provider contract tests. No external requests are made."""
from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd
import pytest

from app.providers.market_data import yfinance_provider as module
from app.services.market_data.base import MarketDataProviderError, MarketDataRequest


class FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        value = cls(2026, 9, 21, 15, tzinfo=timezone.utc)
        return value.astimezone(tz) if tz else value.replace(tzinfo=None)


def test_history_excludes_unfinished_and_future_daily_bars(monkeypatch):
    calls = []

    class Ticker:
        fast_info = {"currency": "INR"}

        def history(self, **kwargs):
            calls.append(kwargs)
            return pd.DataFrame(
                {"Close": [100, 0, float("nan"), 110, 120]},
                index=pd.to_datetime(["2026-09-16", "2026-09-17", "2026-09-18", "2026-09-21", "2026-09-22"]).tz_localize("Asia/Kolkata"),
            )

    monkeypatch.setattr(module, "datetime", FixedDatetime)
    monkeypatch.setattr(module.yf, "Ticker", lambda symbol: Ticker())
    result = module.YFinanceMarketProvider()._fetch_history(
        MarketDataRequest(ticker="RELIANCE", market="IN", exchange="NSE", currency="INR"), 7,
    )

    assert [row.date.isoformat() for row in result] == ["2026-09-16"]
    assert calls == [{"start": "2026-09-14", "end": "2026-09-21", "auto_adjust": False}]
    assert result[0].close_price == Decimal("100")
    assert result[0].currency == "INR"
    assert result[0].provider_symbol == "RELIANCE.NS"
    assert result[0].price_type == "end_of_day"
    assert result[0].adjustment_state == "unadjusted"
    assert any("current UTC date" in warning for warning in result[0].warnings)


def test_history_with_only_todays_bar_is_unavailable(monkeypatch):
    class Ticker:
        fast_info = {"currency": "USD"}

        def history(self, **kwargs):
            return pd.DataFrame({"Close": [100]}, index=pd.to_datetime(["2026-09-21"]))

    monkeypatch.setattr(module, "datetime", FixedDatetime)
    monkeypatch.setattr(module.yf, "Ticker", lambda symbol: Ticker())
    with pytest.raises(MarketDataProviderError) as error:
        module.YFinanceMarketProvider()._fetch_history(
            MarketDataRequest(ticker="NVDA", market="US", currency="USD"), 7,
        )
    assert error.value.code == "PROVIDER_UNAVAILABLE"


def test_latest_quote_does_not_claim_verified_real_time(monkeypatch):
    class Ticker:
        fast_info = {"currency": "USD", "lastPrice": 100}

    monkeypatch.setattr(module.yf, "Ticker", lambda symbol: Ticker())
    quote = module.YFinanceMarketProvider()._fetch_quote(
        MarketDataRequest(ticker="NVDA", market="US", currency="USD"),
    )
    assert quote.current_price == Decimal("100")
    assert quote.price_type == "unknown"
    assert quote.source_timestamp is None
    assert quote.delay_minutes is None
    assert any("unofficial personal-use" in warning for warning in quote.warnings)
    assert any("timestamp and delay" in warning for warning in quote.warnings)
