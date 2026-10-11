from abc import ABC, abstractmethod
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


PriceType = Literal["real_time", "delayed", "end_of_day", "unknown", "manual"]
AdjustmentState = Literal["adjusted", "unadjusted", "not_applicable", "unknown"]


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


class MarketDataRequest(BaseModel):
    market: str
    exchange: str | None = None
    ticker: str
    currency: str | None = None

    @field_validator("market", "ticker")
    @classmethod
    def normalize_required_identity(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("market and ticker are required")
        return normalized

    @field_validator("exchange", "currency")
    @classmethod
    def normalize_optional_identity(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip().upper() or None


class MarketQuoteResult(BaseModel):
    provider_name: str
    provider_symbol: str
    market: str
    exchange: str | None = None
    ticker: str
    currency: str
    current_price: Decimal = Field(gt=0)
    change_percent: Decimal | None = None
    volume: int | None = Field(default=None, ge=0)
    market_cap: Decimal | None = Field(default=None, ge=0)
    pe_ratio: Decimal | None = None
    fifty_two_week_high: Decimal | None = Field(default=None, gt=0)
    fifty_two_week_low: Decimal | None = Field(default=None, gt=0)
    source_timestamp: datetime | None = None
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    price_type: PriceType = "unknown"
    delay_minutes: int | None = Field(default=None, ge=0)
    adjustment_state: AdjustmentState = "not_applicable"
    warnings: list[str] = Field(default_factory=list)


class MarketHistoryResult(BaseModel):
    provider_name: str
    provider_symbol: str
    market: str
    exchange: str | None = None
    ticker: str
    currency: str
    date: date
    close_price: Decimal = Field(gt=0)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    price_type: PriceType = "end_of_day"
    adjustment_state: AdjustmentState = "unknown"
    warnings: list[str] = Field(default_factory=list)


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
