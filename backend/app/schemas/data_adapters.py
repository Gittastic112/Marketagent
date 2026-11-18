"""Pure market adapter contracts; provider/service imports remain compatible."""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


PriceType = Literal["real_time", "delayed", "end_of_day", "unknown", "manual"]
AdjustmentState = Literal["adjusted", "unadjusted", "not_applicable", "unknown"]


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


class AdapterHistoryRequest(MarketDataRequest):
    """Inclusive dates; distinct from the legacy trailing-days request."""
    model_config = ConfigDict(extra="forbid")
    start_date: date
    end_date: date
    adjustment: Literal["provider", "unadjusted", "split_adjusted"] = "provider"

    @model_validator(mode="after")
    def bounded_window(self):
        if self.end_date < self.start_date or (self.end_date - self.start_date).days > 3650:
            raise ValueError("An ordered window of at most 3650 days is required")
        return self


class AdapterDatedQuoteRequest(MarketDataRequest):
    model_config = ConfigDict(extra="forbid")
    requested_date: date


class AdapterActionRequest(MarketDataRequest):
    model_config = ConfigDict(extra="forbid")
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def bounded_window(self):
        if self.end_date < self.start_date or (self.end_date - self.start_date).days > 3650:
            raise ValueError("An ordered window of at most 3650 days is required")
        return self


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


class AdapterCoverageGap(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    code: str
    retryable: bool = False


class AdapterHistoryResult(BaseModel):
    requested_start: date
    requested_end: date
    points: list[MarketHistoryResult] = Field(default_factory=list)
    coverage: Literal["complete", "partial", "empty"]
    # Complete means all requested API windows were read, not certified coverage
    # of every expected session or availability to investors in the past.
    gaps: list[AdapterCoverageGap] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AdapterDatedQuoteResult(BaseModel):
    requested_date: date
    actual_date: date
    point: MarketHistoryResult
    previous_session_substitution: bool = False


class CorporateActionEvidence(BaseModel):
    provider: str
    provider_record_id: str | None = None
    ticker: str
    market: str
    exchange: str | None = None
    action_type: Literal["split", "bonus", "dividend", "other"]
    description: str
    ex_date: date | None = None
    execution_date: date | None = None
    announcement_date: date | None = None
    record_date: date | None = None
    payment_date: date | None = None
    cash_amount: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    currency: str | None = None
    old_shares: Decimal | None = Field(default=None, gt=0, allow_inf_nan=False)
    new_shares: Decimal | None = Field(default=None, gt=0, allow_inf_nan=False)
    observed_at: datetime
    publication_time: datetime | None = None
    source_response_hash: str
    source_locator: str
    warnings: list[str] = Field(default_factory=list)


class AdapterActionsResult(BaseModel):
    actions: list[CorporateActionEvidence] = Field(default_factory=list)
    coverage: Literal["complete", "partial", "empty"]
    gaps: list[AdapterCoverageGap] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class IdentityMappingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id_type: Literal["TICKER", "ID_ISIN", "ID_CUSIP", "ID_SEDOL", "ID_BB_GLOBAL"]
    id_value: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9 .&/_-]+$")
    exchange_code: str | None = Field(default=None, max_length=12, pattern=r"^[A-Za-z0-9]+$")
    mic_code: str | None = Field(default=None, max_length=4, pattern=r"^[A-Za-z0-9]+$")
    include_unlisted_equities: bool = False

    @model_validator(mode="after")
    def one_exchange_filter(self):
        if self.exchange_code and self.mic_code:
            raise ValueError("Use exchange_code or mic_code, not both")
        return self


class IdentityCandidate(BaseModel):
    figi: str
    ticker: str | None = None
    name: str | None = None
    exchange_code: str | None = None
    composite_figi: str | None = None
    share_class_figi: str | None = None
    security_type: str | None = None
    market_sector: str | None = None


class IdentityMappingResult(BaseModel):
    candidates: list[IdentityCandidate]
    resolution: Literal["candidate", "ambiguous", "unresolved"]
    observed_at: datetime
    warnings: list[str] = Field(default_factory=list)


class SecurityReferenceResult(BaseModel):
    provider: str
    ticker: str
    name: str | None = None
    market: str
    exchange: str
    currency: str
    active: bool | None = None
    cik: str | None = None
    composite_figi: str | None = None
    share_class_figi: str | None = None
    observed_at: datetime
    requested_date: date | None = None
    warnings: list[str] = Field(default_factory=list)


class CalendarSessionOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: date
    closed: bool = False
    opens_at: datetime | None = None
    closes_at: datetime | None = None
    source_url: str = Field(max_length=1000, pattern=r"^https://")
    reason: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def valid_session(self):
        if self.closed:
            if self.opens_at or self.closes_at:
                raise ValueError("Closed override cannot contain session times")
        elif not self.opens_at or not self.closes_at:
            raise ValueError("Open override requires both session times")
        else:
            if any(v.tzinfo is None or v.utcoffset() is None for v in (self.opens_at, self.closes_at)):
                raise ValueError("Override times require UTC offsets")
            if self.closes_at <= self.opens_at:
                raise ValueError("Session close must follow open")
        return self


class CalendarScheduleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exchange: Literal["XNYS", "XNAS", "XNSE", "XBOM"]
    start_date: date
    end_date: date
    overrides: list[CalendarSessionOverride] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def valid_window(self):
        if self.end_date < self.start_date or (self.end_date - self.start_date).days > 366:
            raise ValueError("Calendar window must be ordered and at most 366 days")
        days = [o.date for o in self.overrides]
        if len(days) != len(set(days)) or any(not self.start_date <= d <= self.end_date for d in days):
            raise ValueError("Overrides must have unique dates inside the request window")
        return self


class CalendarSession(BaseModel):
    date: date
    opens_at: datetime
    closes_at: datetime
    interruptions: list[tuple[datetime, datetime]] = Field(default_factory=list)
    source: Literal["library", "user_source_override"] = "library"
    source_url: str | None = None


class CalendarScheduleResult(BaseModel):
    exchange: str
    timezone: str
    library_version: str
    coverage_start: date
    coverage_end: date
    override_hash: str
    sessions: list[CalendarSession]
    warnings: list[str]


AdapterData = TypeVar("AdapterData")


class DataAdapterReceipt(BaseModel, Generic[AdapterData]):
    provider: str
    observed_at: datetime
    processing_run_id: int
    source_document_ids: list[int] = Field(default_factory=list)
    result: AdapterData
    warnings: list[str] = Field(default_factory=list)
