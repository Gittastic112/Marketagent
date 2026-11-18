from app.core.config import get_settings
from app.services.market_data.base import MarketDataProvider, MarketDataProviderError
from app.services.market_data.alpha_vantage import AlphaVantageProvider
from app.services.market_data.fmp import FMPProvider
from app.providers.market_data.yfinance_provider import YFinanceMarketProvider
from app.providers.market_data.massive import MassiveProvider
from app.providers.market_data.nse_mcp import NSEMarketProvider


def get_market_data_provider(provider_name: str | None = None) -> MarketDataProvider:
    """One authoritative factory. Explicit request selection never implies fallback."""
    settings = get_settings()
    provider_name = (provider_name if provider_name is not None else settings.market_data_provider).strip().lower()
    if provider_name in {"alphavantage", "alpha_vantage"}:
        if settings.alpha_vantage_api_key:
            return AlphaVantageProvider(api_key=settings.alpha_vantage_api_key)
    elif provider_name == "fmp":
        if settings.fmp_api_key:
            return FMPProvider(api_key=settings.fmp_api_key)
    elif provider_name == "massive":
        if getattr(settings, "massive_api_key", None):
            return MassiveProvider(api_key=settings.massive_api_key)
    elif provider_name == "nse_mcp":
        return NSEMarketProvider()
    elif provider_name == "yfinance_personal":
        return YFinanceMarketProvider()
    else:
        raise MarketDataProviderError(code="PROVIDER_NOT_SUPPORTED",
            message="The selected market data provider is not supported.", provider=provider_name,
            status_code=400, retryable=False)
    raise MarketDataProviderError(code="PROVIDER_NOT_CONFIGURED",
        message="The explicitly selected market data provider needs its configured API key.",
        provider=provider_name, status_code=503, retryable=False)
