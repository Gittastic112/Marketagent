from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class MacroPeriodInput(BaseModel):
    period_label: str
    period_end_date: Optional[date] = None
    operating_income: Optional[float] = None
    market_cap: Optional[float] = None
    total_debt: Optional[float] = None
    cash: Optional[float] = None
    enterprise_value: Optional[float] = None


class MacroTopDownRequest(BaseModel):
    company_id: int
    valuation_id: Optional[int] = None
    frequency: str = "annual"
    periods: List[MacroPeriodInput]


class MacroSegmentInput(BaseModel):
    segment_name: str
    sic_code: Optional[str] = None
    benchmark_industry_name: Optional[str] = None
    segment_value: Optional[float] = None
    segment_revenue: Optional[float] = None
    segment_weight: Optional[float] = None


class MacroBottomUpRequest(BaseModel):
    company_id: int
    valuation_id: Optional[int] = None
    segments: List[MacroSegmentInput]


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

    model_config = ConfigDict(from_attributes=True)
