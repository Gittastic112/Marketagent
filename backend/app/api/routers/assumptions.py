from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.dependencies import get_current_user, get_db
from app.api.schemas import ApiResponse
from app.services.assumption_methodology import AssumptionMethodologyService
from app.models.assumption_methodology import ValuationAssumptionProvenance
from app.models.dcf import ValuationModel

router = APIRouter()

@router.get("/methods/{assumption_key}", response_model=ApiResponse[Dict[str, Any]])
def get_assumption_methods(
    assumption_key: str,
    country: str,
    industry: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Any:
    methods = AssumptionMethodologyService.get_available_methods(db, assumption_key, country, industry)
    default = AssumptionMethodologyService.get_default_method(db, assumption_key, country, industry)

    return ApiResponse(data={
        "assumption_key": assumption_key,
        "country": country,
        "industry": industry,
        "default_method": default["method_key"] if default else "user_custom",
        "selected_method": default["method_key"] if default else "user_custom",
        "methods": methods,
        "range": {
            "low": default.get("low_value"),
            "base": default.get("base_value", default.get("value")),
            "high": default.get("high_value")
        } if default and "low_value" in default else None,
        "requires_review": True
    })

@router.get("/country/{country}", response_model=ApiResponse[Dict[str, Any]])
def get_country_methods(
    country: str,
    industry: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Any:
    return ApiResponse(data=AssumptionMethodologyService.build_country_assumption_pack(db, country, industry))

class SelectMethodRequest(BaseModel):
    assumption_key: str
    method_key: str
    applied_value: float
    source_label: str
    confidence: str
    notes: Optional[str] = None

@router.post(
    "/valuations/{valuation_id}/select-method",
    response_model=ApiResponse[Dict[str, Any]],
)
def select_valuation_assumption_method(
    valuation_id: int,
    request: SelectMethodRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Any:
    valuation = db.query(ValuationModel).filter_by(
        id=valuation_id,
        user_id=current_user["id"],
    ).first()
    if not valuation:
        raise HTTPException(status_code=404, detail="Valuation not found")

    # Update or create the provenance log
    provenance = db.query(ValuationAssumptionProvenance).filter_by(
        valuation_id=valuation_id,
        assumption_key=request.assumption_key
    ).first()

    if not provenance:
        provenance = ValuationAssumptionProvenance(
            valuation_id=valuation_id,
            assumption_key=request.assumption_key,
        )
        db.add(provenance)

    provenance.selected_method_key = request.method_key
    provenance.applied_value = request.applied_value
    provenance.source_label = request.source_label
    provenance.confidence = request.confidence
    provenance.review_status = "overridden" if request.method_key == "user_custom" else "reviewed"
    if request.notes:
        provenance.notes = request.notes

    db.commit()
    db.refresh(provenance)

    return ApiResponse(data={"status": "success", "provenance_id": provenance.id})
