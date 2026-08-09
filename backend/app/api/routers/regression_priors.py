from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.schemas import ApiResponse
from app.db.session import get_db
from app.services.regression_prior_service import RegressionPriorService


router = APIRouter(prefix="/api/priors", tags=["regression_priors"])
Region = Literal["Global", "US"]


class DebtRatioPriorRequest(BaseModel):
    effective_tax_rate: float = Field(ge=0.0, le=1.0)
    expected_eps_growth: float = Field(ge=-1.0, le=10.0)
    institutional_holdings: float = Field(ge=0.0, le=1.0)
    company_age_years: float = Field(ge=0.0, le=500.0)
    region: Region = "Global"


class DividendYieldPriorRequest(BaseModel):
    effective_tax_rate: float = Field(ge=0.0, le=1.0)
    expected_eps_growth: float = Field(ge=-1.0, le=10.0)
    company_age_years: float = Field(ge=0.0, le=500.0)
    beta: float = Field(ge=-5.0, le=10.0)
    region: Region = "Global"


class DividendPayoutPriorRequest(BaseModel):
    beta: float = Field(ge=-5.0, le=10.0)
    return_on_equity: float = Field(ge=-10.0, le=10.0)
    region: Region = "Global"


class RegressionPriorResponse(BaseModel):
    prior_value: float | None
    formula: str
    model: str
    claim_type: Literal["Estimate"]
    confidence: Literal["low", "not_usable"]
    source: str
    source_path: str
    source_as_of: str
    adjusted_r_squared: float
    input_units: dict[str, str]
    output_unit: str
    usable: bool
    warnings: list[str]


@router.post("/debt-ratio", response_model=ApiResponse[RegressionPriorResponse])
def get_debt_ratio_prior(
    request: DebtRatioPriorRequest,
    db: Session = Depends(get_db),
):
    result = RegressionPriorService.calculate_debt_ratio_prior(
        db=db,
        effective_tax_rate=request.effective_tax_rate,
        expected_eps_growth=request.expected_eps_growth,
        institutional_holdings=request.institutional_holdings,
        company_age_years=request.company_age_years,
        region=request.region,
    )
    return ApiResponse(data=RegressionPriorResponse(**result))


@router.post("/dividend-yield", response_model=ApiResponse[RegressionPriorResponse])
def get_dividend_yield_prior(
    request: DividendYieldPriorRequest,
    db: Session = Depends(get_db),
):
    result = RegressionPriorService.calculate_dividend_yield_prior(
        db=db,
        effective_tax_rate=request.effective_tax_rate,
        expected_eps_growth=request.expected_eps_growth,
        company_age_years=request.company_age_years,
        beta=request.beta,
        region=request.region,
    )
    return ApiResponse(data=RegressionPriorResponse(**result))


@router.post("/dividend-payout", response_model=ApiResponse[RegressionPriorResponse])
def get_dividend_payout_prior(
    request: DividendPayoutPriorRequest,
    db: Session = Depends(get_db),
):
    result = RegressionPriorService.calculate_dividend_payout_prior(
        db=db,
        beta=request.beta,
        return_on_equity=request.return_on_equity,
        region=request.region,
    )
    return ApiResponse(data=RegressionPriorResponse(**result))
