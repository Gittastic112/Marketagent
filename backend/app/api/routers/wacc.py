from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field, model_validator

from app.api.schemas import ApiMeta, ApiResponse
from app.services.synthetic_rating_catalog import (
    SYNTHETIC_RATING_SOURCE,
    SyntheticRatingFirmType,
)
from app.services.wacc_engine import (
    CostOfEquityService,
    SyntheticRatingService,
    CostOfDebtService,
    CapitalStructureService,
    WaccService,
)

router = APIRouter(prefix="/api/valuation/wacc", tags=["wacc"])


class WaccCalculationRequest(BaseModel):
    risk_free_rate: float
    beta: float
    mature_erp: float
    country_risk_premium: float = 0.0
    lambda_crp: float = 1.0

    interest_coverage_ratio: float
    firm_type: SyntheticRatingFirmType | None = None
    is_large_mfg: bool | None = Field(
        default=None,
        description="Legacy large/small selector; prefer firm_type.",
        json_schema_extra={"deprecated": True},
    )
    marginal_tax_rate: float

    market_equity: float
    total_debt: float

    terminal_wacc: float
    years_to_fade: int = 5
    total_years: int = 10

    @model_validator(mode="after")
    def validate_firm_type_inputs(self):
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


@router.post("/calculate", response_model=ApiResponse[dict[str, Any]])
def calculate_wacc_components(req: WaccCalculationRequest):
    """
    Calculates the full WACC build-up from component parts dynamically.
    """
    cost_of_equity = CostOfEquityService.calculate(
        req.risk_free_rate,
        req.beta,
        req.mature_erp,
        req.country_risk_premium,
        req.lambda_crp,
    )

    rating_estimate = SyntheticRatingService.estimate(
        req.interest_coverage_ratio,
        firm_type=req.resolved_firm_type,
    )
    rating = rating_estimate.rating
    default_spread = rating_estimate.default_spread

    pre_tax_cost_of_debt = CostOfDebtService.calculate_pre_tax(
        req.risk_free_rate,
        default_spread,
    )
    after_tax_cost_of_debt = CostOfDebtService.calculate_after_tax(
        pre_tax_cost_of_debt,
        req.marginal_tax_rate,
    )

    equity_weight, debt_weight = CapitalStructureService.calculate_market_weights(
        req.market_equity,
        req.total_debt,
    )

    current_wacc = WaccService.calculate_wacc(
        cost_of_equity, after_tax_cost_of_debt, equity_weight, debt_weight
    )

    wacc_array = WaccService.calculate_wacc_fade(
        current_wacc, req.terminal_wacc, req.years_to_fade, req.total_years
    )

    source_warning = (
        "ratings.xls source date is unknown; current recency is a User "
        "Assumption approved for the local workflow on 2026-08-07."
    )
    return ApiResponse(
        data={
            "cost_of_equity": cost_of_equity,
            "synthetic_rating": rating,
            "default_spread": default_spread,
            "synthetic_rating_details": rating_estimate.to_dict(),
            "synthetic_rating_provenance": SYNTHETIC_RATING_SOURCE.to_dict(),
            "pre_tax_cost_of_debt": pre_tax_cost_of_debt,
            "after_tax_cost_of_debt": after_tax_cost_of_debt,
            "equity_weight": equity_weight,
            "debt_weight": debt_weight,
            "current_wacc": current_wacc,
            "wacc_array": wacc_array,
        },
        meta=ApiMeta(
            source="user_inputs+ratings.xls",
            confidence="low",
            warnings=[source_warning],
        ),
    )
