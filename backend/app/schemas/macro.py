from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MacroScenarioRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, allow_inf_nan=False)
    market: str = Field(default="IN", min_length=1, max_length=10)
    country: str = Field(default="India", min_length=1, max_length=120)
    sic_code: str = Field(min_length=1, max_length=20)
    rate_shock: float = 0.0
    gdp_shock: float = 0.0
    inflation_shock: float = 0.0
    currency_shock: float = 0.0
    currency_variable_direction: str | None = Field(default=None, alias="currencyVariableDirection", max_length=240)


class TopDownMacroPeriod(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    period: str = Field(min_length=1, max_length=40)
    operating_income: float
    market_cap: float | None = None
    total_debt: float | None = None
    enterprise_value: float | None = None
    change_in_long_term_bond_rate: float
    gdp_growth: float
    inflation_change: float
    currency_change: float


class TopDownMacroRequest(BaseModel):
    frequency: str = Field(default="annual", max_length=20)
    periods: list[TopDownMacroPeriod] = Field(min_length=1, max_length=120)


class BottomUpMacroSegment(BaseModel):
    model_config = ConfigDict(populate_by_name=True, allow_inf_nan=False)
    name: str = Field(min_length=1, max_length=255)
    sic_code: str = Field(alias="sicCode", min_length=1, max_length=20)
    value: float = Field(ge=0)


class BottomUpMacroRequest(BaseModel):
    market: str = Field(default="IN", min_length=1, max_length=10)
    country: str = Field(default="India", min_length=1, max_length=120)
    segments: list[BottomUpMacroSegment] = Field(min_length=1, max_length=100)


class MacroPeriodInput(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    period_label: str
    period_end_date: Optional[date] = None
    operating_income: Optional[float] = None
    market_cap: Optional[float] = None
    total_debt: Optional[float] = None
    cash: Optional[float] = None
    enterprise_value: Optional[float] = None
    change_in_long_term_bond_rate: float | None = None
    gdp_growth: float | None = None
    inflation_change: float | None = None
    currency_change: float | None = None


class MacroTopDownRequest(BaseModel):
    company_id: int = Field(gt=0)
    valuation_id: Optional[int] = Field(default=None, gt=0)
    frequency: str = "annual"
    periods: List[MacroPeriodInput] = Field(min_length=1, max_length=120)


class MacroSegmentInput(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    segment_name: str
    sic_code: Optional[str] = None
    benchmark_industry_name: Optional[str] = None
    segment_value: Optional[float] = None
    segment_revenue: Optional[float] = None
    segment_weight: Optional[float] = None


class MacroBottomUpRequest(BaseModel):
    company_id: int = Field(gt=0)
    valuation_id: Optional[int] = Field(default=None, gt=0)
    market: str = Field(default="IN", min_length=1, max_length=10)
    country: str = Field(default="India", min_length=1, max_length=120)
    segments: List[MacroSegmentInput] = Field(min_length=1, max_length=100)


class MacroSensitivityMetrics(BaseModel):
    duration: Optional[float] = None
    cyclicality: Optional[float] = None
    inflation_sensitivity: Optional[float] = None
    currency_sensitivity: Optional[float] = None


class MacroSensitivityResult(BaseModel):
    method: str
    observation_count: Optional[int] = None
    firm_value: MacroSensitivityMetrics
    operating_income: MacroSensitivityMetrics
    confidence_label: Optional[str] = None
    warnings: Optional[List[str]] = None
    claim_type: str = "Calculation"
    basis: str | None = None
    formula: str | None = None
    factor_diagnostics: dict[str, Any] = Field(default_factory=dict)
    covered_weight: float | None = None
    metric_coverage: dict[str, float] = Field(default_factory=dict)
    covered_contributions: dict[str, float] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)
