"""Market API contracts, independent of HTTP and persistence."""

from datetime import (
    date,
    datetime,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

from typing import (
    Any,
    Literal,
)


class ScoringConfigUpdate(BaseModel):
    weight_credibility: float | None = None
    weight_novelty: float | None = None
    weight_impact: float | None = None
    weight_speed: float | None = None


class FredIngestionCreate(BaseModel):
    series_id: str = Field(min_length=1, max_length=50)


class FredIngestionRead(BaseModel):
    series_id: str
    macro_series_id: int
    processing_run_id: int
    source_url: str
    observations_fetched: int
    observations_created: int
    observations_skipped_duplicate: int
    observations_skipped_missing: int
    observations_rejected: int


class ScoringConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    weight_credibility: float
    weight_novelty: float
    weight_impact: float
    weight_speed: float


class MacroObservationCreate(BaseModel):
    date_recorded: date
    value: float


class MacroObservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    series_id: int
    date_recorded: date
    value: float


class MacroSeriesCreate(BaseModel):
    name: str
    description: str | None = None
    units: str | None = None
    frequency: str | None = None


class MacroSeriesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None
    units: str | None
    frequency: str | None
    provider_name: str | None = None
    source_url: str | None = None
    observations: list[MacroObservationRead] = []


class CountryMarketContextManualCreate(BaseModel):
    market: str
    country: str
    currency: str
    risk_free_rate: float | None = None
    risk_free_rate_source: str | None = None
    equity_risk_premium: float | None = None
    country_risk_premium: float | None = None
    inflation_rate: float | None = None
    fx_rate_to_usd: float | None = None
    as_of_date: date | None = None
    notes: str | None = None


class CountryMarketContextRead(CountryMarketContextManualCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_manual: bool
    created_at: datetime
    updated_at: datetime


class RiskFreeRateRead(BaseModel):
    market: str
    country: str
    currency: str
    risk_free_rate: float
    risk_free_rate_source: str
    as_of_date: date | None = None
    is_manual: bool
    warnings: list[str] = Field(default_factory=list)


class FxRateObservationCreate(BaseModel):
    base_currency: str = Field(min_length=3, max_length=10)
    quote_currency: str = Field(min_length=3, max_length=10)
    rate: float = Field(gt=0)
    as_of_date: date
    provider_name: str = Field(default="manual", min_length=1, max_length=80)
    provider_symbol: str | None = Field(default=None, max_length=80)
    source_url: str | None = Field(default=None, max_length=1000)
    source_timestamp: datetime | None = None

    @field_validator("base_currency", "quote_currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("provider_name")
    @classmethod
    def normalize_fx_provider(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_pair(self):
        if self.base_currency == self.quote_currency:
            raise ValueError("FX base and quote currencies must differ")
        return self


class FxRateObservationRead(FxRateObservationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    claim_type: str
    import_run_id: int | None = None
    observed_at: datetime
    created_at: datetime


class MarketPriceCreate(BaseModel):
    company_id: int | None = None
    ticker: str
    price: float = Field(ge=0)
    currency: str = "USD"
    as_of_date: date


class MarketPriceUpdate(BaseModel):
    company_id: int | None = None
    ticker: str | None = None
    price: float | None = Field(default=None, ge=0)
    currency: str | None = None
    as_of_date: date | None = None


class MarketPriceRead(MarketPriceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_name: str
    provider_symbol: str | None = None
    source_url: str | None = None
    market: str | None = None
    exchange: str | None = None
    source_timestamp: datetime | None = None
    observed_at: datetime
    price_type: str
    claim_type: str
    import_run_id: int | None = None
    delay_minutes: int | None = None
    adjustment_state: str
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CompanyMarketDataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    market: str | None = None
    exchange: str | None = None
    ticker: str | None = None
    currency: str | None = None
    provider_name: str | None = None
    provider_symbol: str | None = None
    current_price: float | None = None
    change_percent: float | None = None
    volume: int | None = None
    market_cap: float | None = None
    pe_ratio: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None
    source_timestamp: datetime | None = None
    observed_at: datetime | None = None
    price_type: str | None = None
    delay_minutes: int | None = None
    adjustment_state: str | None = None
    warnings: list[str] = Field(default_factory=list)
    last_updated: datetime


class MarketDataIngestionRequest(BaseModel):
    market: str
    exchange: str | None = None
    ticker: str
    days: int = Field(default=365, ge=1, le=3650)


class MarketHistoryPriceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    as_of_date: date = Field(serialization_alias="date")
    price: float
    currency: str
    provider_name: str
    provider_symbol: str | None = None
    market: str | None = None
    exchange: str | None = None
    observed_at: datetime
    price_type: str
    adjustment_state: str
    warnings: list[str] = Field(default_factory=list)


class FinancialMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    metric_name: str
    value: float
    unit: str | None = None


class FinancialPeriodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period_type: str
    year: int
    quarter: int | None = None
    report_date: date
    metrics: list[FinancialMetricRead] = Field(default_factory=list)


class MarketRegimeInputCreate(BaseModel):
    metric_name: Literal["options", "liquidity", "volume", "breadth", "macro"]
    value: float = Field(ge=-100, le=100)
    as_of_date: date
    source_url: HttpUrl | None = None
    source_name: str = Field(min_length=2, max_length=200)
    input_type: Literal["manual", "provider"] = "manual"
    methodology: str = Field(min_length=10, max_length=1000)

    @field_validator("as_of_date")
    @classmethod
    def reject_future_observations(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("as_of_date cannot be in the future")
        return value

    @model_validator(mode="after")
    def require_provider_source_url(self):
        if self.input_type == "provider" and self.source_url is None:
            raise ValueError("provider inputs require source_url")
        return self


class MarketRegimeInputRead(MarketRegimeInputCreate):
    id: int
    source_record_type: str | None = None
    source_record_id: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarketRegimeScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    score_date: date
    overall_score: float
    options_score: float | None = None
    liquidity_score: float | None = None
    volume_score: float | None = None
    breadth_score: float | None = None
    macro_score: float | None = None
    confidence: str
    calculation_status: Literal["complete", "stale", "blocked"]
    formula: str
    blockers: list[str] = Field(default_factory=list)
    input_sources: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    mode: str
    live_modules: list[str] = Field(default_factory=list)
    manual_modules: list[str] = Field(default_factory=list)
    simulated_modules: list[str] = Field(default_factory=list)
    created_at: datetime


class MarketRegimeMacroProviderRead(BaseModel):
    metric_name: Literal["macro"] = "macro"
    series_id: Literal["NFCI"] = "NFCI"
    macro_series_id: int | None = None
    observation_id: int | None = None
    observed_value: float | None = None
    normalized_value: float | None = None
    as_of_date: date | None = None
    source_name: str
    source_url: str
    methodology: str
    claim_type: Literal["Calculation"] = "Calculation"
    freshness_threshold_days: int
    age_days: int | None = None
    is_stale: bool = False
    can_apply: bool = False
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    applied_input_id: int | None = None
    created: bool = False
