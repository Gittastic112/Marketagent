"""Option Calculations API contracts, independent of HTTP and persistence."""

from pydantic import (
    BaseModel,
)

from typing import (
    Literal,
)


class OptionEligibilityTestRequest(BaseModel):
    valuation_id: str | None = None
    option_type: str
    has_underlying_asset: bool = False
    has_finite_life: bool = False
    has_clear_exercise_price: bool = False
    has_asymmetric_payoff: bool = False
    has_exclusivity: bool = False
    can_estimate_volatility: bool = False
    can_estimate_underlying_value: bool = False


class OptionEligibilityTestResponse(BaseModel):
    eligibilityPassed: bool
    eligibilityScore: float
    recommendation: str
    warnings: list[str] = []


class RealOptionCalculateRequest(BaseModel):
    valuation_id: str | None = None
    option_type: str = "call"
    underlying_asset_value: float
    exercise_price: float
    option_life_years: float
    risk_free_rate: float
    volatility: float
    dividend_yield_or_cost_of_delay: float = 0.0
    exclusivity_score: float = 1.0
    is_already_counted: bool = False
    base_dcf_value: float = 0.0


class RealOptionCalculateResponse(BaseModel):
    d1: float
    d2: float
    nd1: float
    nd2: float
    raw_option_value: float
    adjusted_option_value: float
    option_delta: float
    option_adjusted_intrinsic_value: float | None = None
    warnings: list[str] = []


class VolatilityBenchmarkRead(BaseModel):
    country: str
    industry: str
    numberOfFirms: int | None
    equityStandardDeviation: float | None
    firmValueStandardDeviation: float | None
    equityValueWeight: float | None
    debtValueWeight: float | None
    assumptions: dict[str, float]
    claimType: Literal["Source Summary"] = "Source Summary"
    datasetVersionId: int
    sourceFile: str
    sourceSha256: str
    sourceAsOf: str
    dateConfidence: str
    canonicalSourcePath: str
