import asyncio
from decimal import Decimal

import pytest

from app.providers.market_data.yfinance_provider import YFinanceMarketProvider
from app.services.market_data.alpha_vantage import AlphaVantageProvider
from app.services.market_data.base import MarketDataProviderError, MarketDataRequest, MarketQuoteResult
from app.services.market_data.factory import get_market_data_provider


def test_yfinance_ticker_mapping() -> None:
    provider = YFinanceMarketProvider()

    assert provider.provider_symbol(MarketDataRequest(market="US", ticker="AAPL", currency="USD")) == "AAPL"
    assert (
        provider.provider_symbol(
            MarketDataRequest(market="IN", exchange="NSE", ticker="ADANIPORTS", currency="INR")
        )
        == "ADANIPORTS.NS"
    )
    assert (
        provider.provider_symbol(
            MarketDataRequest(market="IN", exchange="BSE", ticker="532921", currency="INR")
        )
        == "532921.BO"
    )


@pytest.mark.parametrize("field", ["market", "ticker"])
def test_market_data_request_rejects_blank_required_identity(field: str) -> None:
    values = {"market": "US", "ticker": "AAPL"}
    values[field] = "  "

    with pytest.raises(ValueError):
        MarketDataRequest(**values)


def test_yfinance_quote_returns_contract_without_database_write(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeTicker:
        fast_info = {"lastPrice": 123.45, "currency": "INR"}

        def history(self, **kwargs):
            raise AssertionError("history fallback should not be used")

    monkeypatch.setattr(
        "app.providers.market_data.yfinance_provider.yf.Ticker",
        lambda symbol: FakeTicker(),
    )

    result = asyncio.run(
        YFinanceMarketProvider().get_quote(
            MarketDataRequest(market="IN", exchange="NSE", ticker="ADANIPORTS", currency="INR")
        )
    )

    assert isinstance(result, MarketQuoteResult)
    assert result.provider_name == "yfinance_personal"
    assert result.provider_symbol == "ADANIPORTS.NS"
    assert result.current_price == Decimal("123.45")
    assert "unofficial" in " ".join(result.warnings).lower()


def test_alpha_vantage_missing_key_is_not_an_empty_success() -> None:
    with pytest.raises(MarketDataProviderError) as exc_info:
        asyncio.run(
            AlphaVantageProvider(api_key="").get_quote(
                MarketDataRequest(market="US", exchange="NASDAQ", ticker="AAPL", currency="USD")
            )
        )

    assert exc_info.value.code == "PROVIDER_NOT_CONFIGURED"
    assert exc_info.value.retryable is False


def test_factory_rejects_unknown_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    class Settings:
        market_data_provider = "mystery"
        alpha_vantage_api_key = None
        fmp_api_key = None

    monkeypatch.setattr("app.services.market_data.factory.get_settings", lambda: Settings())

    with pytest.raises(MarketDataProviderError) as exc_info:
        get_market_data_provider()

    assert exc_info.value.code == "PROVIDER_NOT_SUPPORTED"


def test_single_configured_provider_is_not_hidden_by_a_fallback_wrapper(monkeypatch):
    class Settings:
        market_data_provider = "yfinance_personal"
        alpha_vantage_api_key = None
        fmp_api_key = None
    monkeypatch.setattr("app.services.market_data.factory.get_settings", lambda: Settings())
    assert isinstance(get_market_data_provider(), YFinanceMarketProvider)
