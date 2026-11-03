"""Calculation result contracts. No HTTP, ORM, or service dependencies."""
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DiagnosticWarning(BaseModel):
    severity: str
    module: str
    message: str
    affectedAssumptions: list[str] = []
    suggestedFix: str | None = None
    formula: str | None = None


class DcfOutputCreate(BaseModel):
    assumption_set_id: int
    sum_pv_fcff: float | None = None
    terminal_value: float | None = None
    pv_terminal_value: float | None = None
    enterprise_value: float | None = None
    cash: float | None = None
    cross_holdings: float | None = None
    non_operating_assets: float | None = None
    debt: float | None = None
    operating_leases: float | None = None
    minority_interests: float | None = None
    preferred_stock: float | None = None
    employee_options_value: float | None = None
    equity_value: float | None = None
    diluted_shares: float | None = None
    intrinsic_value_per_share: float | None = None
    current_market_price: float | None = None
    upside_downside_pct: float | None = None
    terminal_value_pct_of_ev: float | None = None
    implied_exit_multiple: float | None = None
    implied_terminal_roic: float | None = None
    implied_pe: float | None = None
    implied_ev_ebitda: float | None = None
    implied_ev_sales: float | None = None
    implied_ev_ebit: float | None = None
    implied_pbv: float | None = None

    # Phase 11
    fcfe_intrinsic_value_per_share: float | None = None
    ddm_intrinsic_value_per_share: float | None = None

    # Phase 16
    base_dcf_value: float | None = None
    pv_of_excess_returns: float | None = None

    model_quality_score: float | None = None
    warnings_json: list[dict[str, Any]] | list[str] | None = None


class ReverseDcfResponse(BaseModel):
    target_parameter: str
    implied_value: float | None
    original_value: float | None
    intrinsic_value_at_implied: float | None
    diagnostics: list[DiagnosticWarning] = Field(default_factory=list)
    error: str | None = None
    assumption_set_id: int | None = None
    assumptions_updated_at: datetime | None = None
    calculated_at: datetime | None = None
    currency: str | None = None
    model_type: str | None = None
    comparison_price: float | None = None
    diluted_shares: float | None = None
    price_residual: float | None = None
    converged: bool = False


class QuickValuationProjectionRead(BaseModel):
    year_index: int
    revenue: float
    revenue_growth: float
    ebit_margin: float
    nopat: float
    reinvestment: float
    fcff: float
    roic: float
    wacc: float
    pv_fcff: float


class QuickValuationOutputRead(BaseModel):
    company_id: int
    currency: str | None
    claim_type: Literal["Calculation"] = "Calculation"
    is_persisted: Literal[False] = False
    sum_pv_fcff: float
    terminal_value: float
    pv_terminal_value: float
    enterprise_value: float
    cash: float
    cross_holdings: float
    debt: float
    operating_leases: float
    minority_interests: float
    preferred_stock: float
    employee_options_value: float
    equity_value: float
    diluted_shares: float
    intrinsic_value_per_share: float
    current_market_price: float
    upside_downside_pct: float | None
    terminal_value_pct_of_ev: float
    model_quality_score: float | None = None
    warnings_json: list[dict[str, Any]]
    projection_years: list[QuickValuationProjectionRead]
    limitations: list[str]


class DcfProjectionYearRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    assumption_set_id: int
    year_index: int
    calendar_year: int | None = Field(default=None, description="Unavailable without a reviewed fiscal-year anchor; use year_index for relative periods.")
    revenue: float | None = None
    revenue_growth: float | None = None
    ebit_margin: float | None = None
    ebit: float | None = None
    tax_rate: float | None = None
    nopat: float | None = None
    reinvestment: float | None = None
    fcff: float | None = None
    invested_capital: float | None = None
    roic: float | None = None
    wacc: float | None = None
    discount_factor: float | None = None
    pv_fcff: float | None = None
    created_at: datetime


    @field_validator("calendar_year", mode="before")
    @classmethod
    def withhold_unanchored_calendar_year(cls, value: object) -> None:
        # Legacy stored years came from a fixed 2024 origin, not reviewed input.
        # Shape the detached read contract without rewriting historical rows.
        return None


class DcfSensitivityTableRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    assumption_set_id: int
    table_type: str
    x_axis_json: dict[str, Any] | None = None
    y_axis_json: dict[str, Any] | None = None
    values_json: dict[str, Any] | None = None
    created_at: datetime


class DcfDecisionLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    valuation_model_id: int
    assumption_set_id: int
    decision_type: str
    user_note: str | None = None
    price_at_decision: float | None = None
    intrinsic_value_at_decision: float | None = None
    upside_downside_at_decision: float | None = None
    confidence_label: str | None = None
    created_at: datetime


class ValuationAssumptionChangeLogCreate(BaseModel):
    valuation_model_id: int
    assumption_set_id: int
    event_id: int | None = None
    parameter_name: str
    old_value: str | None = None
    new_value: str | None = None
    rationale: str | None = None
    is_applied: bool = False


class ValuationAssumptionChangeLogRead(ValuationAssumptionChangeLogCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    valuation_model_id: int
    assumption_set_id: int
    event_id: int | None = None
    parameter_name: str
    old_value: str | None = None
    new_value: str | None = None
    rationale: str | None = None
    is_applied: bool
    created_at: datetime
