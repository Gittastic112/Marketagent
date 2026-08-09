from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.relative_valuation import RelativeValuationBenchmarkService, RelativeValuationRunService, RelativeValuationRequest
from app.api.schemas import ApiResponse

router = APIRouter(prefix="/api/valuation/relative", tags=["relative-valuation"])
legacy_router = APIRouter(prefix="/relative-valuation", tags=["relative-valuation"])


def _meta() -> dict[str, Any]:
    return {
        "source": "Damodaran India pricing workbooks",
        "confidence": "high",
        "is_mock": False,
    }


def _country_stats_meta() -> dict[str, Any]:
    return {
        "source": "Damodaran country statistics",
        "confidence": "high",
        "is_mock": False,
        "warnings": [],
    }

@legacy_router.get("/countries", response_model=ApiResponse, include_in_schema=False)
@router.get("/countries", response_model=ApiResponse)
def get_countries(db: Session = Depends(get_db)):
    countries = RelativeValuationBenchmarkService.get_countries(db)
    return ApiResponse(data=countries, meta=_meta())

@legacy_router.get("/countries/{country}/stats", response_model=ApiResponse, include_in_schema=False)
@router.get("/countries/{country}/stats", response_model=ApiResponse)
def get_country_stats(country: str, db: Session = Depends(get_db)):
    stats = RelativeValuationBenchmarkService.get_country_stats(db, country)
    if not stats:
        return ApiResponse(
            data=None,
            meta={"status": "error"},
            errors=[{"code": "NOT_FOUND", "message": f"Stats not found for country {country}"}],
        )
    return ApiResponse(data=stats.as_dict(), meta=_country_stats_meta())

@legacy_router.get("/countries/{country}/industries", response_model=ApiResponse, include_in_schema=False)
@router.get("/countries/{country}/industries", response_model=ApiResponse)
def get_industries(country: str, db: Session = Depends(get_db)):
    industries = RelativeValuationBenchmarkService.get_industries(db, country)
    return ApiResponse(data=industries, meta=_meta())

@legacy_router.get("/countries/{country}/industries/{industry}", response_model=ApiResponse, include_in_schema=False)
@router.get("/countries/{country}/industries/{industry}", response_model=ApiResponse)
def get_industry_benchmark(country: str, industry: str, db: Session = Depends(get_db)):
    benchmark = RelativeValuationBenchmarkService.get_industry_benchmark(db, country, industry)
    if not benchmark:
        return ApiResponse(
            data=None,
            meta={"status": "error"},
            errors=[{"code": "NOT_FOUND", "message": f"Benchmark not found for {industry} in {country}"}],
        )
    return ApiResponse(data=benchmark.as_dict(), meta=_meta())

@legacy_router.post("/run", response_model=ApiResponse, include_in_schema=False)
@router.post("/run", response_model=ApiResponse)
def run_relative_valuation(request: RelativeValuationRequest, db: Session = Depends(get_db)):
    result = RelativeValuationRunService.run_valuation(db, request)
    if "error" in result:
        return ApiResponse(
            data=None,
            meta={"status": "error"},
            errors=[{"code": "VALUATION_ERROR", "message": result["error"]}],
        )
    return ApiResponse(data=result, meta=_meta())
