"""Portfolio input and output contracts, independent of HTTP and persistence."""
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PortfolioCreate(BaseModel):
    name: str
    base_currency: str = "USD"
    description: str | None = None


class PortfolioUpdate(BaseModel):
    name: str | None = None
    base_currency: str | None = None
    description: str | None = None


class PortfolioRead(PortfolioCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PortfolioBenchmarkConfigCreate(BaseModel):
    portfolio_id: int = Field(gt=0)
    benchmark_company_id: int | None = Field(default=None, gt=0)
    ticker: str = Field(min_length=1, max_length=40)
    currency: str = Field(min_length=3, max_length=10)
    provider_name: str = Field(default="manual", min_length=1, max_length=80)
    provider_symbol: str | None = Field(default=None, max_length=80)
    effective_from: date
    active: bool = True
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("ticker", "currency")
    @classmethod
    def normalize_symbols(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("provider_name")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        return value.strip()


class PortfolioBenchmarkConfigUpdate(BaseModel):
    benchmark_company_id: int | None = Field(default=None, gt=0)
    ticker: str | None = Field(default=None, min_length=1, max_length=40)
    currency: str | None = Field(default=None, min_length=3, max_length=10)
    provider_name: str | None = Field(default=None, min_length=1, max_length=80)
    provider_symbol: str | None = Field(default=None, max_length=80)
    effective_from: date | None = None
    active: bool | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("ticker", "currency")
    @classmethod
    def normalize_optional_symbols(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else None

    @field_validator("provider_name")
    @classmethod
    def normalize_optional_provider(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class PortfolioBenchmarkConfigRead(PortfolioBenchmarkConfigCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PortfolioHoldingCreate(BaseModel):
    portfolio_id: int
    company_id: int | None = None
    ticker: str
    quantity: float = Field(ge=0)
    average_cost: float = Field(default=0, ge=0)
    currency: str = "USD"
    as_of_date: date


class PortfolioHoldingUpdate(BaseModel):
    portfolio_id: int | None = None
    company_id: int | None = None
    ticker: str | None = None
    quantity: float | None = Field(default=None, ge=0)
    average_cost: float | None = Field(default=None, ge=0)
    currency: str | None = None
    as_of_date: date | None = None


class PortfolioHoldingRead(PortfolioHoldingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


PortfolioTransactionType = Literal[
    "buy",
    "sell",
    "dividend",
    "split",
    "bonus",
    "deposit",
    "withdrawal",
    "fee",
    "tax",
    "manual_adjustment",
]


class PortfolioTransactionCreate(BaseModel):
    portfolio_id: int
    company_id: int | None = None
    ticker: str
    transaction_type: PortfolioTransactionType
    quantity: float = Field(ge=0)
    price: float = Field(default=0, ge=0)
    fees: float = Field(default=0, ge=0)
    currency: str = "USD"
    transaction_date: date
    notes: str | None = None


class PortfolioTransactionUpdate(BaseModel):
    portfolio_id: int | None = None
    company_id: int | None = None
    ticker: str | None = None
    transaction_type: PortfolioTransactionType | None = None
    quantity: float | None = Field(default=None, ge=0)
    price: float | None = Field(default=None, ge=0)
    fees: float | None = Field(default=None, ge=0)
    currency: str | None = None
    transaction_date: date | None = None
    notes: str | None = None


class PortfolioTransactionRead(PortfolioTransactionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PortfolioCashBalanceCreate(BaseModel):
    portfolio_id: int
    currency: str = "USD"
    amount: float = Field(default=0)
    as_of_date: date


class PortfolioCashBalanceUpdate(BaseModel):
    portfolio_id: int | None = None
    currency: str | None = None
    amount: float | None = Field(default=None)
    as_of_date: date | None = None


class PortfolioCashBalanceRead(PortfolioCashBalanceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PortfolioSnapshotCreate(BaseModel):
    portfolio_id: int
    snapshot_date: date
    total_market_value: float | None = Field(default=None, ge=0)
    total_cost_basis: float | None = Field(default=None, ge=0)
    total_cash: float | None = Field(default=None)
    payload_json: dict[str, Any] | None = None


class PortfolioSnapshotUpdate(BaseModel):
    portfolio_id: int | None = None
    snapshot_date: date | None = None
    total_market_value: float | None = Field(default=None, ge=0)
    total_cost_basis: float | None = Field(default=None, ge=0)
    total_cash: float | None = Field(default=None, ge=0)
    payload_json: dict[str, Any] | None = None


class PortfolioSnapshotRead(PortfolioSnapshotCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    total_portfolio_value: float | None = None
    base_currency: str | None = None
    calculation_status: Literal["complete", "partial", "not_available"] = "not_available"
    holdings_count: int = 0
    priced_holdings_count: int = 0
    missing_price_tickers_json: list[str] = Field(default_factory=list)
    missing_fx_pairs_json: list[str] = Field(default_factory=list)
    created_at: datetime


class PortfolioValuationHoldingRead(BaseModel):
    holding_id: int | None
    ticker: str
    company_id: int | None
    quantity: float
    average_cost: float
    currency: str
    market_price: float | None
    market_price_id: int | None = None
    market_price_provider: str | None = None
    market_price_as_of: date | None
    market_value: float | None
    total_cost: float
    unrealized_pnl: float | None
    unrealized_pnl_percent: float | None
    market_value_base: float | None = None
    total_cost_base: float | None = None
    unrealized_pnl_base: float | None = None
    market_fx_rate_to_base: float | None = None
    market_fx_rate_as_of: date | None = None
    market_fx_observation_id: int | None = None
    market_fx_is_stale: bool = False
    cost_fx_rate_to_base: float | None = None
    cost_fx_rate_as_of: date | None = None
    cost_fx_observation_id: int | None = None
    cost_fx_is_stale: bool = False
    cost_fx_observation_ids: list[int] = Field(default_factory=list)
    source_transaction_ids: list[int] = Field(default_factory=list)
    weight_percent: float | None
    is_stale_price: bool
    is_valuation_stale: bool | None = None
    stale_valuation_reason: str | None = None
    valuation_status: Literal["trusted", "stale", "untrusted", "unavailable"] = "unavailable"
    valuation_status_reason: str | None = None
    fx_impact: float | None = None
    opportunity_cost: float | None = None
    opportunity_cost_percent: float | None = None
    intrinsic_value: float | None = None
    dcf_output_id: int | None = None
    expected_return: float | None = None
    thesis_status: str | None = None
    active_alerts_count: int | None = 0


class PortfolioCashValuationRead(BaseModel):
    cash_balance_id: int | None
    currency: str
    amount: float
    as_of_date: date
    value_base: float | None
    fx_rate_to_base: float | None
    fx_rate_as_of: date | None
    fx_observation_id: int | None
    fx_is_stale: bool = False


class PortfolioValuationRead(BaseModel):
    portfolio_id: int
    as_of_date: date
    base_currency: str
    total_market_value: float | None
    total_portfolio_value: float | None
    total_cash_value: float | None
    total_cost_basis: float | None
    total_unrealized_pnl: float | None
    total_unrealized_pnl_percent: float | None
    missing_fx_pairs: list[str] = Field(default_factory=list)
    cash_balances: list[PortfolioCashValuationRead] = Field(default_factory=list)
    holdings: list[PortfolioValuationHoldingRead]
    replay_basis: dict[str, Any] | None = None


class PortfolioAttributionComponent(BaseModel):
    price_movement: float | None
    fx_impact: float | None


class PortfolioTransactionActivityRead(BaseModel):
    purchases: float
    sales: float
    dividends: float
    deposits: float
    withdrawals: float
    fees: float
    taxes: float
    net_position_cash_flow: float
    net_external_cash_flow: float


class PortfolioAttributionRead(BaseModel):
    as_of_date: date
    base_currency: str
    calculation_status: Literal["partial", "not_available"]
    total_unrealized_pnl: float | None
    components: PortfolioAttributionComponent
    opportunity_cost: float | None
    activity_by_currency: dict[str, PortfolioTransactionActivityRead]
    attribution_by_sector: dict[str, float]
    attribution_by_geography: dict[str, float]
    attribution_by_asset_type: dict[str, float]
    warnings: list[str]


class PortfolioReturnMetricRead(BaseModel):
    calculation_status: Literal["complete", "partial", "not_available"]
    return_decimal: float | None
    start_date: date | None
    end_date: date
    warnings: list[str] = Field(default_factory=list)
    source_snapshot_ids: list[int] = Field(default_factory=list)
    source_transaction_ids: list[int] = Field(default_factory=list)


class PortfolioPerformanceRead(BaseModel):
    portfolio_id: int
    requested_start_date: date
    requested_end_date: date
    time_weighted_return: PortfolioReturnMetricRead
    money_weighted_return: PortfolioReturnMetricRead


class PortfolioPeriodHoldingAttributionRead(BaseModel):
    key: str
    company_id: int | None = None
    ticker: str | None = None
    price_movement: float | None = None
    fx_impact: float | None = None
    position_change: float | None = None
    total_contribution: float | None = None
    calculation_status: Literal["complete", "partial", "not_available"]


class PortfolioPeriodAttributionRead(BaseModel):
    portfolio_id: int
    start_date: date
    end_date: date
    base_currency: str | None
    calculation_status: Literal["complete", "partial", "not_available"]
    confidence: Literal["high", "medium", "low", "invalid"]
    formula: str
    total_change: float | None
    price_movement: float | None
    fx_impact: float | None
    position_change: float | None
    cash_change: float | None
    external_cash_flow: float | None
    internal_cash_change: float | None
    unexplained_change: float | None
    holdings: list[PortfolioPeriodHoldingAttributionRead] = Field(default_factory=list)
    attribution_by_sector: dict[str, float] = Field(default_factory=dict)
    attribution_by_geography: dict[str, float] = Field(default_factory=dict)
    attribution_by_asset_type: dict[str, float] = Field(default_factory=dict)
    attribution_by_tag: dict[str, float] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    source_snapshot_ids: list[int] = Field(default_factory=list)
    source_transaction_ids: list[int] = Field(default_factory=list)


class PortfolioOpportunityCostRead(BaseModel):
    calculation_status: Literal["complete", "partial", "not_available", "not_configured"]
    portfolio_id: int
    start_date: date
    end_date: date
    benchmark_ticker: str | None
    benchmark_return: float | None
    portfolio_return: float | None
    return_spread: float | None
    benchmark_ending_value: float | None
    actual_ending_value: float | None
    opportunity_cost: float | None
    opportunity_cost_percent: float | None
    warnings: list[str] = Field(default_factory=list)
    source_snapshot_ids: list[int] = Field(default_factory=list)
    source_market_price_ids: list[int] = Field(default_factory=list)
    source_transaction_ids: list[int] = Field(default_factory=list)


class PortfolioRiskReturnHoldingRead(BaseModel):
    holding_id: int | None
    company_id: int | None
    ticker: str
    portfolio_weight_decimal: float | None
    risk_model_weight_decimal: float | None
    current_market_value_base: float | None
    latest_market_price_as_of: date | None = None
    price_age_days: int | None = None
    is_stale_price: bool = False
    observation_count: int
    aligned_observation_count: int
    return_start_date: date | None
    return_end_date: date | None
    historical_return_decimal: float | None
    annualized_volatility: float | None
    marginal_volatility: float | None
    marginal_volatility_for_one_percent: float | None
    component_risk: float | None
    component_risk_percent: float | None
    expected_return_decimal: float | None
    expected_return_kind: Literal["dcf_valuation_gap_not_annualized", "unavailable"]
    expected_return_claim_type: Literal["Estimate", "Unavailable"]
    expected_return_contribution: float | None
    source_dcf_output_id: int | None
    source_market_price_ids: list[int] = Field(default_factory=list)
    source_fx_observation_ids: list[int] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PortfolioRiskReturnRead(BaseModel):
    replay_basis: dict[str, Any] | None = None
    portfolio_id: int
    as_of_date: date
    lookback_start_date: date
    lookback_days: int
    min_observations: int
    base_currency: str
    calculation_status: Literal["complete", "partial", "not_available"]
    risk_calculation_status: Literal["complete", "partial", "not_available"]
    expected_return_calculation_status: Literal["complete", "partial", "not_available"]
    portfolio_volatility_annualized: float | None
    risk_covered_weight_percent: float
    risk_reconciliation_error: float | None
    portfolio_expected_return_decimal: float | None
    expected_return_coverage_percent: float
    risk_claim_type: Literal["Calculation", "Unavailable"]
    expected_return_claim_type: Literal["Estimate", "Unavailable"]
    contains_mock_data: bool = False
    risk_formula: str
    expected_return_formula: str
    holdings: list[PortfolioRiskReturnHoldingRead] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    source_market_price_ids: list[int] = Field(default_factory=list)
    source_fx_observation_ids: list[int] = Field(default_factory=list)
    source_dcf_output_ids: list[int] = Field(default_factory=list)


class PortfolioRealInputReadinessCheck(BaseModel):
    code: str
    label: str
    status: Literal["passed", "blocked"]
    required: str
    observed: str
    message: str
    source_record_ids: list[int] = Field(default_factory=list)


class PortfolioRealInputReadinessRead(BaseModel):
    portfolio_id: int
    user_id: str
    certification_status: Literal["ready", "blocked"]
    claim_type: Literal["Calculation"]
    as_of_date: date
    start_date: date | None
    end_date: date | None
    lookback_days: int
    min_observations: int
    contains_mock_data: bool = False
    checks: list[PortfolioRealInputReadinessCheck] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source_snapshot_ids: list[int] = Field(default_factory=list)
    source_market_price_ids: list[int] = Field(default_factory=list)
    source_fx_observation_ids: list[int] = Field(default_factory=list)
    source_dcf_output_ids: list[int] = Field(default_factory=list)


class PortfolioAnalyticsRead(BaseModel):
    portfolio_id: int
    as_of_date: date
    base_currency: str
    total_portfolio_value: float | None
    total_cash_value: float | None
    total_invested_value: float | None
    total_unrealized_pnl: float | None
    total_unrealized_pnl_percent: float | None
    top_positions: list[PortfolioValuationHoldingRead]
    top_gainers: list[PortfolioValuationHoldingRead]
    top_losers: list[PortfolioValuationHoldingRead]
    sector_exposure: dict[str, float]
    industry_exposure: dict[str, float]
    country_exposure: dict[str, float]
    currency_exposure: dict[str, float]
    asset_type_exposure: dict[str, float]
    concentration_score: float | None
    diversification_warnings: list[str]
    fx_impact: float | None = None
    opportunity_cost: float | None = None
    opportunity_cost_percent: float | None = None
    missing_fx_pairs: list[str] = Field(default_factory=list)
