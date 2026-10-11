"""Saved-basis option contracts. No HTTP or persistence dependencies."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool


class RealOptionEligibilityInputs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    has_underlying_asset: StrictBool = False
    has_finite_life: StrictBool = False
    has_clear_exercise_price: StrictBool = False
    has_asymmetric_payoff: StrictBool = False
    has_exclusivity: StrictBool = False
    can_estimate_volatility: StrictBool = False
    can_estimate_underlying_value: StrictBool = False


class SavedRealOptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assumptions_updated_at: datetime
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    option_type: Literal["call", "put"]
    underlying_asset_value: float = Field(gt=0, le=1e18, allow_inf_nan=False, strict=True)
    exercise_price: float = Field(gt=0, le=1e18, allow_inf_nan=False, strict=True)
    option_life_years: float = Field(gt=0, le=100, allow_inf_nan=False, strict=True)
    risk_free_rate: float = Field(ge=-.5, le=1, allow_inf_nan=False, strict=True)
    volatility: float = Field(gt=0, le=5, allow_inf_nan=False, strict=True)
    dividend_yield_or_cost_of_delay: float = Field(ge=0, le=1, allow_inf_nan=False, strict=True)
    exclusivity_score: float = Field(ge=0, le=1, allow_inf_nan=False, strict=True)
    is_already_counted: StrictBool
    confirm_incremental_equity_basis: StrictBool
    eligibility: RealOptionEligibilityInputs


class SavedRealOptionResponse(BaseModel):
    assumption_set_id: int
    assumptions_updated_at: datetime
    output_created_at: datetime
    calculated_at: datetime
    currency: str
    model_type: str
    input_sha256: str
    diluted_shares: float
    base_equity_value: float
    base_value_per_share: float
    raw_option_value: float
    adjusted_option_value: float
    option_value_per_share: float
    option_adjusted_equity_value: float
    option_adjusted_intrinsic_value: float
    warnings: list[str]
