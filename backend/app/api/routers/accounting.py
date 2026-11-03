from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.services.accounting_normalization import AccountingNormalizationService, GoodwillDiagnosticsService

router = APIRouter(prefix="/api/valuation/accounting", tags=["accounting"])

class RDCapitalizationRequest(BaseModel):
    reported_ebit: float
    reported_invested_capital: float
    current_rd: float
    historical_rd: List[float] # Expected 5 elements, newest first (1y ago, 2y ago...)

class GoodwillDiagnosticsRequest(BaseModel):
    goodwill: float
    total_assets: float
    impairment_expense: Optional[float] = 0.0

@router.post("/rd-capitalization", response_model=ApiResponse[Dict[str, Any]])
def capitalize_rd(req: RDCapitalizationRequest):
    """
    Capitalizes R&D expense over 5 years. Returns the R&D asset, amortization,
    and the adjusted EBIT and Invested Capital.
    """
    result = AccountingNormalizationService.normalize_rd(
        reported_ebit=req.reported_ebit,
        reported_ic=req.reported_invested_capital,
        current_rd=req.current_rd,
        historical_rd=req.historical_rd
    )
    return ApiResponse(data=result)

@router.post("/goodwill-diagnostics", response_model=ApiResponse[Dict[str, Any]])
def diagnose_goodwill(req: GoodwillDiagnosticsRequest):
    """
    Analyzes goodwill as a percentage of total assets and flags potential
    overpayment or acquisition intensity.
    """
    result = GoodwillDiagnosticsService.diagnose(
        goodwill=req.goodwill,
        total_assets=req.total_assets,
        impairment_expense=req.impairment_expense
    )
    return ApiResponse(data=result)
