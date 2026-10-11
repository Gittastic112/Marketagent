from app.core.config import get_settings
from app.services.market_data.base import MarketDataProvider, MarketDataProviderError
from app.services.market_data.alpha_vantage import AlphaVantageProvider
from app.services.market_data.fmp import FMPProvider
from app.providers.market_data.yfinance_provider import YFinanceMarketProvider

def get_market_data_provider() -> MarketDataProvider:
    """
    Return the explicitly selected adapter. No implicit source fallback.
    """
    settings = get_settings()
    provider_name = settings.market_data_provider.strip().lower()
    supported_providers = {"alphavantage", "alpha_vantage", "fmp", "yfinance_personal"}

    if provider_name not in supported_providers:
        raise MarketDataProviderError(
            code="PROVIDER_NOT_SUPPORTED",
            message=f"Market data provider '{provider_name}' is not supported.",
            provider=provider_name,
            status_code=400,
            retryable=False,
        )

    providers = []

    # 1. Configured Free-Tier Provider
    if provider_name in ("alphavantage", "alpha_vantage") and settings.alpha_vantage_api_key:
        providers.append(AlphaVantageProvider(api_key=settings.alpha_vantage_api_key))
    elif provider_name == "fmp" and settings.fmp_api_key:
        providers.append(FMPProvider(api_key=settings.fmp_api_key))

    # 2. Personal-use / Unofficial Provider Fallback (only if allowed or strictly configured)
    if provider_name == "yfinance_personal":
        providers.append(YFinanceMarketProvider())

    if not providers:
        raise MarketDataProviderError(
            code="PROVIDER_NOT_CONFIGURED",
            message="Market data provider is not configured. Add its API key or explicitly select yfinance_personal.",
            provider=provider_name,
            status_code=503,
            retryable=False,
        )

    return providers[0]
