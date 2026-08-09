from app.services.market_data.base import (
    MarketDataProvider,
    MarketDataProviderError,
    MarketDataRequest,
    MarketHistoryResult,
    MarketQuoteResult,
)

class FMPProvider(MarketDataProvider):
    """
    Placeholder for Financial Modeling Prep (FMP) integration.
    """
    provider_name = "fmp"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_quote(self, request: MarketDataRequest) -> MarketQuoteResult:
        raise MarketDataProviderError(
            code="PROVIDER_NOT_IMPLEMENTED",
            message="The FMP market data adapter is not implemented.",
            provider=self.provider_name,
            status_code=501,
            retryable=False,
        )

    async def get_historical_prices(
        self,
        request: MarketDataRequest,
        days: int = 365,
    ) -> list[MarketHistoryResult]:
        raise MarketDataProviderError(
            code="PROVIDER_NOT_IMPLEMENTED",
            message="The FMP market data adapter is not implemented.",
            provider=self.provider_name,
            status_code=501,
            retryable=False,
        )
