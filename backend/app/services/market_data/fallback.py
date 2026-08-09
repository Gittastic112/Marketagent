from datetime import datetime, timezone
import logging

from app.services.market_data.base import (
    MarketDataProvider,
    MarketDataProviderError,
    MarketDataRequest,
    MarketQuoteResult,
    MarketHistoryResult
)

logger = logging.getLogger(__name__)

class FallbackMarketDataProvider(MarketDataProvider):
    """
    A market data provider that tries a list of providers in order, falling back to the next one
    if a provider fails with a retryable error (like rate limit / quota exceeded) or is unconfigured.
    """
    provider_name = "Fallback Provider"

    def __init__(self, providers: list[MarketDataProvider]):
        self.providers = providers

    async def get_quote(self, request: MarketDataRequest) -> MarketQuoteResult:
        errors = []
        for provider in self.providers:
            try:
                return await provider.get_quote(request)
            except MarketDataProviderError as e:
                logger.warning(f"Provider {provider.provider_name} failed get_quote for {request.ticker}: {e.message}")
                errors.append(e)
                if not e.retryable:
                    raise e
            except Exception as e:
                logger.error(f"Provider {provider.provider_name} failed unexpectedly: {e}")
                errors.append(e)

        raise MarketDataProviderError(
            code="ALL_PROVIDERS_FAILED",
            message="All fallback providers failed to get quote.",
            provider="Fallback",
            status_code=503,
            retryable=True
        )

    async def get_historical_prices(self, request: MarketDataRequest, days: int = 365) -> list[MarketHistoryResult]:
        errors = []
        for provider in self.providers:
            try:
                return await provider.get_historical_prices(request, days=days)
            except MarketDataProviderError as e:
                logger.warning(f"Provider {provider.provider_name} failed get_historical_prices for {request.ticker}: {e.message}")
                errors.append(e)
                if not e.retryable:
                    raise e
            except Exception as e:
                logger.error(f"Provider {provider.provider_name} failed unexpectedly: {e}")
                errors.append(e)

        raise MarketDataProviderError(
            code="ALL_PROVIDERS_FAILED",
            message="All fallback providers failed to get historical prices.",
            provider="Fallback",
            status_code=503,
            retryable=True
        )
