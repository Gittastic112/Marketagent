from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import ApiResponse
from app.api.errors import PublicApiError
from app.db.session import get_db
from app.models.macro import MacroObservation, MacroSeries
from app.models.macro_sensitivity import SectorMacroSensitivityBenchmark
from app.services.bottom_up_macro_sensitivity import BottomUpMacroSensitivityService
from app.services.macro_context import (
    DEFAULT_MACRO_COUNTRY,
    DEFAULT_MACRO_MARKET,
    benchmark_context,
)
from app.services.macro_scenario_translation import MacroScenarioTranslationService
from app.services.top_down_macro_sensitivity import TopDownMacroSensitivityService

router = APIRouter(prefix="/api/valuation/macro", tags=["valuation-macro"])


class MacroScenarioRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    market: str = DEFAULT_MACRO_MARKET
    country: str = DEFAULT_MACRO_COUNTRY
    sic_code: str = Field(..., min_length=1)
    rate_shock: float = 0.0
    gdp_shock: float = 0.0
    inflation_shock: float = 0.0
    currency_shock: float = 0.0
    currency_variable_direction: str | None = Field(default=None, alias="currencyVariableDirection")


class TopDownMacroPeriod(BaseModel):
    period: str
    operating_income: float
    market_cap: float
    total_debt: float
    enterprise_value: float | None = None
    change_in_long_term_bond_rate: float
    gdp_growth: float
    inflation_change: float
    currency_change: float


class TopDownMacroRequest(BaseModel):
    frequency: str = "annual"
    periods: list[TopDownMacroPeriod]


class BottomUpMacroSegment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    sic_code: str = Field(..., alias="sicCode")
    value: float


class BottomUpMacroRequest(BaseModel):
    market: str = DEFAULT_MACRO_MARKET
    country: str = DEFAULT_MACRO_COUNTRY
    segments: list[BottomUpMacroSegment]


@router.get("/sector", response_model=ApiResponse[dict[str, Any]])
def get_sector_macro_sensitivity(
    sic: str = Query(..., min_length=1),
    market: str = DEFAULT_MACRO_MARKET,
    country: str = DEFAULT_MACRO_COUNTRY,
    db: Session = Depends(get_db),
):
    benchmark = db.scalar(
        select(SectorMacroSensitivityBenchmark).where(
            SectorMacroSensitivityBenchmark.market == market,
            SectorMacroSensitivityBenchmark.country == country,
            SectorMacroSensitivityBenchmark.sic_code == sic
        )
    )
    if not benchmark:
        raise HTTPException(
            status_code=404,
            detail="Sector macro sensitivity benchmark not found",
        )

    return ApiResponse(
        data={
            **benchmark_context(benchmark),
            "sic_code": benchmark.sic_code,
            "industry_name": benchmark.industry_name,
            "source_file": benchmark.source_file,
            "firm_value_duration": benchmark.firm_value_duration,
            "firm_value_cyclicality": benchmark.firm_value_cyclicality,
            "firm_value_inflation": benchmark.firm_value_inflation,
            "firm_value_currency": benchmark.firm_value_currency,
            "operating_income_duration": benchmark.operating_income_duration,
            "operating_income_cyclicality": benchmark.operating_income_cyclicality,
            "operating_income_inflation": benchmark.operating_income_inflation,
            "operating_income_currency": benchmark.operating_income_currency,
        }
    )


@router.get("/data", response_model=ApiResponse[list[dict[str, Any]]])
def list_macro_data(
    frequency: str | None = None,
    series_name: str | None = None,
    start: date | None = None,
    end: date | None = None,
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    statement = (
        select(MacroSeries, MacroObservation)
        .join(MacroObservation, MacroObservation.series_id == MacroSeries.id)
        .order_by(MacroSeries.name, MacroObservation.date_recorded)
        .limit(limit)
    )
    if frequency:
        statement = statement.where(MacroSeries.frequency == frequency)
    if series_name:
        statement = statement.where(MacroSeries.name == series_name)
    if start:
        statement = statement.where(MacroObservation.date_recorded >= start)
    if end:
        statement = statement.where(MacroObservation.date_recorded <= end)

    observations = []
    for series, observation in db.execute(statement):
        observations.append(
            {
                "series_name": series.name,
                "description": series.description,
                "frequency": series.frequency,
                "date_recorded": observation.date_recorded,
                "value": observation.value,
            }
        )

    return ApiResponse(data=observations)


@router.post("/scenario", response_model=ApiResponse[dict[str, Any]])
def run_macro_scenario(
    payload: MacroScenarioRequest,
    db: Session = Depends(get_db),
):
    try:
        result = MacroScenarioTranslationService.translate(
            db,
            sic_code=payload.sic_code,
            market=payload.market,
            country=payload.country,
            rate_shock=payload.rate_shock,
            gdp_shock=payload.gdp_shock,
            inflation_shock=payload.inflation_shock,
            currency_shock=payload.currency_shock,
            currency_variable_direction=payload.currency_variable_direction,
        )
    except LookupError as exc:
        raise PublicApiError(
            status_code=404,
            code="MACRO_BENCHMARK_NOT_FOUND",
            message="Sector macro sensitivity benchmark not found",
        ) from exc

    return ApiResponse(data=result)


@router.post("/top-down", response_model=ApiResponse[dict[str, Any]])
def run_top_down_macro_sensitivity(payload: TopDownMacroRequest):
    try:
        result = TopDownMacroSensitivityService.calculate(
            [period.model_dump() for period in payload.periods],
            frequency=payload.frequency,
        )
    except ValueError as exc:
        raise PublicApiError(
            status_code=400,
            code="MACRO_PERIODS_INVALID",
            message="At least 3 periods with valid macro inputs are required.",
            field="periods",
        ) from exc

    return ApiResponse(data=result)


@router.post("/bottom-up", response_model=ApiResponse[dict[str, Any]])
def run_bottom_up_macro_sensitivity(
    payload: BottomUpMacroRequest,
    db: Session = Depends(get_db),
):
    try:
        result = BottomUpMacroSensitivityService.calculate(
            db,
            market=payload.market,
            country=payload.country,
            segments=[segment.model_dump() for segment in payload.segments],
        )
    except LookupError as exc:
        raise PublicApiError(
            status_code=404,
            code="MACRO_BENCHMARK_NOT_FOUND",
            message="Sector macro sensitivity benchmark not found",
        ) from exc
    except ValueError as exc:
        raise PublicApiError(
            status_code=400,
            code="MACRO_SEGMENTS_INVALID",
            message="Total segment value must be greater than zero.",
            field="segments",
        ) from exc

    return ApiResponse(data=result)
