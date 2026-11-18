from abc import ABC, abstractmethod

# Compatibility exports: the public service imports remain supported.
from app.schemas.data_adapters import (
    AdjustmentState, MarketDataRequest, MarketHistoryResult, MarketQuoteResult, PriceType,
)


class MarketDataProviderError(RuntimeError):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        provider: str,
        status_code: int = 502,
        retryable: bool = True,
        processing_run_id: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.provider = provider
        self.status_code = status_code
        self.retryable = retryable
        self.processing_run_id = processing_run_id


class MarketDataProvider(ABC):
    """
    Abstract base class for market data providers.
    """
    provider_name: str

    @abstractmethod
    async def get_quote(self, request: MarketDataRequest) -> MarketQuoteResult:
        """
        Fetch one validated, source-labeled quote result.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_historical_prices(
        self,
        request: MarketDataRequest,
        days: int = 365,
    ) -> list[MarketHistoryResult]:
        """
        Fetch validated, source-labeled daily history.
        """
        raise NotImplementedError
