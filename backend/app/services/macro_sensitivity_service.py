"""Compatibility entry points delegated to explicit-input, non-writing engines."""
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.dcf import ValuationModel
from app.schemas.macro import MacroTopDownRequest, MacroBottomUpRequest, MacroSensitivityResult
from app.services.top_down_macro_sensitivity import TopDownMacroSensitivityService
from app.services.bottom_up_macro_sensitivity import BottomUpMacroSensitivityService


def _context(db: Session, company_id: int, valuation_id: int | None, user_id: str | None) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise LookupError("Company not found")
    if valuation_id is not None:
        model = db.scalar(select(ValuationModel).where(ValuationModel.id == valuation_id,
            ValuationModel.company_id == company_id, ValuationModel.user_id == user_id))
        if user_id is None or model is None:
            raise LookupError("Valuation not found")
    return company


def run_top_down_macro_sensitivity(db: Session, request: MacroTopDownRequest, *, user_id: str | None = None) -> MacroSensitivityResult:
    _context(db, request.company_id, request.valuation_id, user_id)
    periods = []
    for item in request.periods:
        row = item.model_dump()
        row["period"] = item.period_end_date.isoformat() if item.period_end_date else item.period_label
        if item.cash is not None and item.enterprise_value is None:
            raise ValueError("Provide explicit enterprise value when cash adjustments are intended.")
        periods.append(row)
    result = TopDownMacroSensitivityService.calculate(periods, request.frequency)
    result["warnings"].append("Compatibility calculation is read-only; inputs and historical results are not saved or rewritten.")
    return MacroSensitivityResult(**result)


def run_bottom_up_macro_sensitivity(db: Session, request: MacroBottomUpRequest, *, user_id: str | None = None) -> MacroSensitivityResult:
    company = _context(db, request.company_id, request.valuation_id, user_id)
    if company.market and company.market != request.market:
        raise ValueError("Company and benchmark markets must match.")
    # A single common basis must cover every segment. Never mix values, revenues
    # and weights or fill a missing segment with a guessed neutral coefficient.
    basis = next((field for field in ("segment_value", "segment_revenue", "segment_weight")
                  if all(getattr(segment, field) is not None for segment in request.segments)), None)
    if basis is None:
        raise ValueError("Every segment requires an explicit value, revenue or weight on one shared basis.")
    if basis == "segment_weight" and not math.isclose(sum(s.segment_weight for s in request.segments), 1, abs_tol=1e-6):
        raise ValueError("Explicit segment weights must sum to one.")
    if any(not segment.sic_code for segment in request.segments):
        raise ValueError("Every segment requires an explicit SIC code.")
    result = BottomUpMacroSensitivityService.calculate(db, market=request.market, country=request.country,
        segments=[{"name": segment.segment_name, "sic_code": segment.sic_code, "value": getattr(segment, basis)}
                  for segment in request.segments])
    result["warnings"].append(f"Compatibility calculation uses the explicit {basis} basis and does not save or rewrite records.")
    result["basis"] = f"User Assumption: all submitted segments use {basis}; no claim of independently verified segment valuation."
    return MacroSensitivityResult(**result)
