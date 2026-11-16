from typing import Any

from fastapi import APIRouter
from app.schemas.wacc import WaccCalculationRequest

from app.schemas.common import ApiMeta, ApiResponse
from app.services.synthetic_rating_catalog import (
    SYNTHETIC_RATING_SOURCE,
)
from app.services.wacc_engine import (
    CostOfEquityService,
    SyntheticRatingService,
    CostOfDebtService,
    CapitalStructureService,
    WaccService,
)

router = APIRouter(prefix="/api/valuation/wacc", tags=["wacc"])


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
