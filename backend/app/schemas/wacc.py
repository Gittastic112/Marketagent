"""Pure WACC request units, capital and horizon contracts."""
from enum import Enum
from math import isfinite
from pydantic import BaseModel, ConfigDict, Field, model_validator


class SyntheticRatingFirmType(str, Enum):
    LARGE_NON_FINANCIAL = "large_non_financial"
    SMALL_OR_RISKY = "small_or_risky"
    FINANCIAL_SERVICE = "financial_service"


class WaccCalculationRequest(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    risk_free_rate: float = Field(ge=0, le=1)
    beta: float = Field(ge=0, le=5)
    mature_erp: float = Field(ge=0, le=1)
    country_risk_premium: float = Field(default=0, ge=0, le=1)
    lambda_crp: float = Field(default=1, ge=0)

    interest_coverage_ratio: float
    firm_type: SyntheticRatingFirmType | None = None
    is_large_mfg: bool | None = Field(
        default=None,
        description="Legacy large/small selector; prefer firm_type.",
        json_schema_extra={"deprecated": True},
    )
    marginal_tax_rate: float = Field(ge=0, le=1)

    market_equity: float = Field(ge=0)
    total_debt: float = Field(ge=0)

    terminal_wacc: float = Field(ge=0, le=1)
    years_to_fade: int = Field(default=5, ge=0, le=30)
    total_years: int = Field(default=10, ge=1, le=30)

    @model_validator(mode="after")
    def validate_firm_type_inputs(self):
        capital = self.market_equity + self.total_debt
        if not isfinite(capital) or capital <= 0:
            raise ValueError("Total capital must be positive and finite")
        if self.years_to_fade > self.total_years:
            raise ValueError("years_to_fade cannot exceed total_years")
        if self.firm_type is None or self.is_large_mfg is None:
            return self
        legacy_type = (
            SyntheticRatingFirmType.LARGE_NON_FINANCIAL
            if self.is_large_mfg
            else SyntheticRatingFirmType.SMALL_OR_RISKY
        )
        if self.firm_type != legacy_type:
            raise ValueError("firm_type and legacy is_large_mfg inputs conflict")
        return self

    @property
    def resolved_firm_type(self) -> SyntheticRatingFirmType:
        if self.firm_type is not None:
            return self.firm_type
        if self.is_large_mfg is False:
            return SyntheticRatingFirmType.SMALL_OR_RISKY
        return SyntheticRatingFirmType.LARGE_NON_FINANCIAL
