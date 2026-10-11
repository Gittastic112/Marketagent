"""Valuation input contracts and validation. No HTTP, ORM, or service dependencies."""
from datetime import datetime
from math import isfinite
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator


class ValuationModelCreate(BaseModel):
    company_id: int | None = None
    name: str
    description: str | None = None
    model_type: Literal["fcff_dcf", "distressed", "financial_services"] = "fcff_dcf"


class ValuationModelUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ValuationCompanyContextRead(BaseModel):
    company_id: int
    market: str
    country: str
    default_currency: str
    cash_flow_currency: str
    discount_rate_currency: str
    available_benchmark_countries: list[str]
    recommended_benchmark_country: str
    benchmark_source: str
    warnings: list[str] = Field(default_factory=list)


class DcfAssumptionSetCreate(BaseModel):
    valuation_model_id: int | None = None
    scenario: str = "Base"

    # Story-based Valuation
    story_text: str | None = None
    growth_story: str | None = None
    margin_story: str | None = None
    reinvestment_story: str | None = None
    risk_story: str | None = None

    # Core Assumptions
    projection_years_count: int = 10
    starting_revenue: float | None = None
    revenue_growth_years_json: dict[str, Any] | None = None
    target_operating_margin: float | None = None
    current_operating_margin: float | None = None
    tax_rate: float | None = None
    sales_to_capital_ratio: float | None = None
    reinvestment_method: str = "sales_to_capital"
    starting_invested_capital: float | None = None

    # Cost of Capital
    risk_free_rate: float | None = None
    equity_risk_premium: float | None = None
    beta: float | None = None
    cost_of_equity: float | None = None
    pre_tax_cost_of_debt: float | None = None
    debt_to_capital: float | None = None
    equity_to_capital: float | None = None
    wacc_start: float | None = None
    wacc_terminal: float | None = None

    # Terminal Value
    terminal_growth_rate: float | None = None
    terminal_roic: float | None = None

    # Bridge to Equity
    cash: float | None = None
    cross_holdings: float | None = None
    minority_interests: float | None = None
    preferred_stock: float | None = None
    debt: float | None = None
    operating_leases: float | None = None
    employee_options_value: float | None = None
    diluted_shares: float | None = None
    basic_shares: float | None = None
    current_market_price: float | None = None
    cash_flow_currency: str | None = None
    discount_rate_currency: str | None = None
    currency_override_note: str | None = None

    # Phase 11 additions: FCFE, Dividends, Buybacks
    net_income: float | None = None
    capex: float | None = None
    depreciation: float | None = None
    change_in_nwc: float | None = None
    new_debt_issued: float | None = None
    debt_repaid: float | None = None
    dividends: float | None = None
    buybacks: float | None = None
    stock_issuances: float | None = None
    company_age: float | None = None

    # Phase 18: Market Intelligence Integration
    is_stale: bool = False
    stale_reason: str | None = None
    stale_event_id: int | None = None

    # Phase 16: Lifecycle and Special Cases
    probability_of_failure: float | None = None
    distress_sale_proceeds: float | None = None
    book_value_of_equity: float | None = None
    target_roe: float | None = None


class DcfAssumptionSetWrite(DcfAssumptionSetCreate):
    @model_validator(mode="after")
    def validate_dcf_input_units(self):
        bounded = {
            "current_operating_margin": (-1.0, 1.0),
            "target_operating_margin": (-1.0, 1.0),
            "tax_rate": (0.0, 1.0),
            "risk_free_rate": (0.0, 1.0),
            "equity_risk_premium": (0.0, 1.0),
            "cost_of_equity": (0.0, 1.0),
            "pre_tax_cost_of_debt": (0.0, 1.0),
            "debt_to_capital": (0.0, 1.0),
            "equity_to_capital": (0.0, 1.0),
            "wacc_start": (0.0, 1.0),
            "wacc_terminal": (0.0, 1.0),
            "terminal_growth_rate": (-0.2, 0.2),
            "terminal_roic": (0.0, 1.0),
            "beta": (0.0, 5.0),
            "probability_of_failure": (0.0, 1.0),
            "target_roe": (-1.0, 1.0),
        }
        for field, (lower, upper) in bounded.items():
            value = getattr(self, field)
            if value is not None and not lower <= value <= upper:
                raise ValueError(f"{field} must be between {lower} and {upper} using decimal units")
        for field in ("book_value_of_equity", "net_income", "distress_sale_proceeds", "diluted_shares"):
            value = getattr(self, field)
            if value is not None and not isfinite(value):
                raise ValueError(f"{field} must be finite")
        if self.distress_sale_proceeds is not None and self.distress_sale_proceeds < 0:
            raise ValueError("distress_sale_proceeds must be nonnegative common-equity recovery")
        for field in ("starting_revenue", "sales_to_capital_ratio", "starting_invested_capital", "diluted_shares"):
            value = getattr(self, field)
            if value is not None and value <= 0:
                raise ValueError(f"{field} must be greater than zero")
        if self.projection_years_count < 1 or self.projection_years_count > 30:
            raise ValueError("projection_years_count must be between 1 and 30")
        for field in ("cash_flow_currency", "discount_rate_currency"):
            value = getattr(self, field)
            if value is not None:
                normalized = value.strip().upper()
                if len(normalized) != 3 or not normalized.isalpha():
                    raise ValueError(f"{field} must be a three-letter currency code")
                setattr(self, field, normalized)
        if (
            self.cash_flow_currency
            and self.discount_rate_currency
            and self.cash_flow_currency != self.discount_rate_currency
            and not (self.currency_override_note or "").strip()
        ):
            raise ValueError("currency_override_note is required when cash-flow and discount-rate currencies differ")
        if self.debt_to_capital is not None and self.equity_to_capital is not None:
            if abs((self.debt_to_capital + self.equity_to_capital) - 1.0) > 0.001:
                raise ValueError("Debt-to-capital and equity-to-capital must sum to 1.0")
        return self


class DcfAssumptionVersionWrite(DcfAssumptionSetWrite):
    # Version commands are not persisted financial inputs or draft-promotion data.
    base_assumption_set_id: int | None = Field(default=None, gt=0)
    base_assumption_set_updated_at: datetime | None = None

    @model_validator(mode="after")
    def validate_version_basis(self):
        if (self.base_assumption_set_id is None) != (self.base_assumption_set_updated_at is None):
            raise ValueError("A versioned save requires both the base assumption ID and timestamp")
        return self


class DcfAssumptionSetUpdate(DcfAssumptionSetCreate):
    pass


class ReverseDcfRequest(BaseModel):
    assumption_set_id: int = Field(gt=0)
    target_parameter: Literal["target_operating_margin", "revenue_growth", "wacc_start", "terminal_growth_rate"]
    current_market_price: float = Field(gt=0, allow_inf_nan=False)
    diluted_shares: float | None = Field(default=None, gt=0, allow_inf_nan=False)


class QuickValuationAssumptionsRequest(BaseModel):
    company_id: int = Field(gt=0)


class QuickValuationCalculateRequest(BaseModel):
    company_id: int = Field(gt=0)
    projection_years_count: int = Field(default=10, ge=1, le=20)
    starting_revenue: float = Field(gt=0, allow_inf_nan=False)
    revenue_growth_years_json: dict[str, float] = Field(min_length=1, max_length=20)
    current_operating_margin: float = Field(ge=-1, le=1, allow_inf_nan=False)
    target_operating_margin: float = Field(ge=-1, le=1, allow_inf_nan=False)
    tax_rate: float = Field(ge=0, le=1, allow_inf_nan=False)
    sales_to_capital_ratio: float = Field(gt=0, allow_inf_nan=False)
    starting_invested_capital: float = Field(ge=0, allow_inf_nan=False)
    wacc_start: float = Field(gt=0, le=1, allow_inf_nan=False)
    wacc_terminal: float = Field(gt=0, le=1, allow_inf_nan=False)
    terminal_growth_rate: float = Field(ge=-0.2, le=0.2, allow_inf_nan=False)
    terminal_roic: float = Field(gt=0, le=1, allow_inf_nan=False)
    cash: float = Field(default=0, ge=0, allow_inf_nan=False)
    cross_holdings: float = Field(default=0, ge=0, allow_inf_nan=False)
    debt: float = Field(default=0, ge=0, allow_inf_nan=False)
    operating_leases: float = Field(default=0, ge=0, allow_inf_nan=False)
    minority_interests: float = Field(default=0, ge=0, allow_inf_nan=False)
    preferred_stock: float = Field(default=0, ge=0, allow_inf_nan=False)
    employee_options_value: float = Field(default=0, ge=0, allow_inf_nan=False)
    diluted_shares: float = Field(default=0, gt=0, allow_inf_nan=False)
    current_market_price: float = Field(gt=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_quick_dcf(self):
        normalized_years: dict[str, float] = {}
        for key, value in self.revenue_growth_years_json.items():
            try:
                year = int(key)
            except (TypeError, ValueError) as exc:
                raise ValueError("Revenue growth keys must be projection year numbers") from exc
            if str(year) != key or year < 1 or year > self.projection_years_count:
                raise ValueError("Revenue growth years must be within the projection horizon")
            if value <= -1 or value > 5:
                raise ValueError("Revenue growth rates must be greater than -100% and no more than 500%")
            normalized_years[str(year)] = value
        if self.terminal_growth_rate >= self.wacc_terminal:
            raise ValueError("terminal_growth_rate must be below wacc_terminal")
        self.revenue_growth_years_json = normalized_years
        return self


class ValuationSetupDraftUpdate(BaseModel):
    assumptions_patch: dict[str, Any] = Field(default_factory=dict)
    reviewed_fields: list[str] = Field(default_factory=list)
    expected_updated_at: datetime | None = None


class ValuationSetupDraftCommand(BaseModel):
    expected_updated_at: datetime | None = None


class ValuationSetupDraftReset(ValuationSetupDraftCommand):
    fields: list[str]


class ValuationSetupDraftPromote(BaseModel):
    name: str
    description: str | None = None
    model_type: str = "fcff_dcf"
    expected_updated_at: datetime | None = None
