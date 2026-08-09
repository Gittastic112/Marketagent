from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.errors import PublicApiError

from app.api.schemas import (
    ApiResponse,
    OptionEligibilityTestRequest,
    OptionEligibilityTestResponse,
    RealOptionCalculateRequest,
    RealOptionCalculateResponse,
    VolatilityBenchmarkRead
)
from app.services.real_options_service import (
    RealOptionEligibilityService,
    BlackScholesRealOptionService,
    RealOptionIntegrationService
)
from app.models.real_options import IndustryVolatilityBenchmark
from app.models.damodaran import DamodaranDatasetFile

router = APIRouter()

@router.get(
    "/volatility",
    response_model=ApiResponse[VolatilityBenchmarkRead],
    include_in_schema=False,
)
@router.get(
    "/api/valuation/options/volatility",
    response_model=ApiResponse[VolatilityBenchmarkRead],
)
def get_volatility_benchmark(
    country: str,
    industry: str,
    db: Session = Depends(get_db)
):
    result = (
        db.query(IndustryVolatilityBenchmark, DamodaranDatasetFile)
        .join(
            DamodaranDatasetFile,
            DamodaranDatasetFile.id == IndustryVolatilityBenchmark.dataset_file_id,
        )
        .filter(
            IndustryVolatilityBenchmark.country == country,
            IndustryVolatilityBenchmark.industry_name == industry,
            DamodaranDatasetFile.dataset_code == "volatility",
            DamodaranDatasetFile.is_active.is_(True),
        )
        .first()
    )
    if result is None:
        raise PublicApiError(
            status_code=404,
            code="VOLATILITY_BENCHMARK_NOT_FOUND",
            message="No active volatility benchmark was found for the requested country and industry.",
        )
    benchmark, dataset = result

    data = VolatilityBenchmarkRead(
        country=benchmark.country,
        industry=benchmark.industry_name,
        numberOfFirms=benchmark.number_of_firms,
        equityStandardDeviation=benchmark.equity_standard_deviation,
        firmValueStandardDeviation=benchmark.firm_value_standard_deviation,
        equityValueWeight=benchmark.equity_value_weight,
        debtValueWeight=benchmark.debt_value_weight,
        assumptions={
            "debtToEquityVolatilityRatio": benchmark.assumed_debt_to_equity_vol_ratio,
            "debtEquityCorrelation": benchmark.assumed_debt_equity_correlation,
        },
        datasetVersionId=dataset.id,
        sourceFile=benchmark.source_file,
        sourceSha256=dataset.source_sha256,
        sourceAsOf=dataset.source_as_of,
        dateConfidence=dataset.date_confidence,
        canonicalSourcePath=dataset.canonical_source_path,
    )
    return ApiResponse(
        data=data,
        meta={
            "source": "damodaran.optvarIndia.xls",
            "is_mock": False,
            "confidence": dataset.date_confidence,
            "warnings": [
                "Industry volatility is a prior; company or project volatility still requires review."
            ],
        },
    )

@router.post(
    "/api/valuation/options/eligibility",
    response_model=ApiResponse[OptionEligibilityTestResponse],
)
@router.post(
    "/eligibility",
    response_model=ApiResponse[OptionEligibilityTestResponse],
    include_in_schema=False,
)
def run_eligibility_test(request: OptionEligibilityTestRequest):
    inputs = {
        "has_underlying_asset": request.has_underlying_asset,
        "has_finite_life": request.has_finite_life,
        "has_clear_exercise_price": request.has_clear_exercise_price,
        "has_asymmetric_payoff": request.has_asymmetric_payoff,
        "has_exclusivity": request.has_exclusivity,
        "can_estimate_volatility": request.can_estimate_volatility,
        "can_estimate_underlying_value": request.can_estimate_underlying_value,
    }

    result = RealOptionEligibilityService.evaluate(inputs)

    data = OptionEligibilityTestResponse(
        eligibilityPassed=result["eligibilityPassed"],
        eligibilityScore=result["eligibilityScore"],
        recommendation=result["recommendation"],
        warnings=result["warnings"]
    )

    return ApiResponse(data=data)

@router.post(
    "/api/valuation/options/calculate",
    response_model=ApiResponse[RealOptionCalculateResponse],
)
@router.post(
    "/calculate",
    response_model=ApiResponse[RealOptionCalculateResponse],
    include_in_schema=False,
)
def calculate_real_option(request: RealOptionCalculateRequest):
    try:
        calc_result = BlackScholesRealOptionService.calculate(
            S=request.underlying_asset_value,
            K=request.exercise_price,
            t=request.option_life_years,
            r=request.risk_free_rate,
            sigma=request.volatility,
            y=request.dividend_yield_or_cost_of_delay,
            option_type=request.option_type,
            exclusivity_score=request.exclusivity_score
        )
    except Exception as exc:
        raise PublicApiError(
            status_code=422,
            code="INVALID_REAL_OPTION_INPUT",
            message="The real option inputs do not produce a valid calculation.",
        ) from exc

    integration_result = RealOptionIntegrationService.generate_adjusted_output(
        base_dcf_value=request.base_dcf_value,
        adjusted_option_value=calc_result["adjusted_option_value"],
        is_already_counted=request.is_already_counted
    )

    data = RealOptionCalculateResponse(
        d1=calc_result["d1"],
        d2=calc_result["d2"],
        nd1=calc_result["nd1"],
        nd2=calc_result["nd2"],
        raw_option_value=calc_result["raw_option_value"],
        adjusted_option_value=calc_result["adjusted_option_value"],
        option_delta=calc_result["option_delta"],
        option_adjusted_intrinsic_value=integration_result["option_adjusted_intrinsic_value"],
        warnings=integration_result["warnings"]
    )

    return ApiResponse(data=data)
