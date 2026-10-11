from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.ai_errors import ai_output_meta, public_ai_error
from app.api.dependencies import get_current_user
from app.schemas.common import ApiResponse
from app.db.session import get_db
from app.models.ai import AiOutput
from app.models.company import Company
from app.models.dcf import DcfAssumptionSet, DcfOutput, ValuationModel
from app.services.ai_contract import AIExecutionError, require_privacy_disclosure
from app.services.memo_writer import ValuationMemoAgent
from app.services.narrative_to_numbers import NarrativeToNumbersAgent


router = APIRouter()


class NarrativeRequest(BaseModel):
    narrative_text: str
    privacy_disclosure_version: str


class MemoRequest(BaseModel):
    privacy_disclosure_version: str


def get_owned_valuation(db: Session, valuation_id: int, user_id: str) -> ValuationModel:
    valuation = db.scalar(
        select(ValuationModel).where(
            ValuationModel.id == valuation_id,
            ValuationModel.user_id == user_id,
        )
    )
    if valuation is None:
        raise HTTPException(status_code=404, detail="Valuation not found")
    return valuation


def get_scenario(
    db: Session,
    *,
    valuation_id: int,
    scenario: str,
) -> DcfAssumptionSet:
    assumption_set = db.scalar(
        select(DcfAssumptionSet).where(
            DcfAssumptionSet.valuation_model_id == valuation_id,
            DcfAssumptionSet.scenario == scenario,
        )
    )
    if assumption_set is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return assumption_set


@router.post("/valuation/{valuation_id}/scenarios/{scenario}/ai/narrative-to-numbers")
def narrative_to_numbers(
    valuation_id: int,
    scenario: str,
    request: NarrativeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict[str, Any]]:
    valuation = get_owned_valuation(db, valuation_id, current_user["id"])
    assumption_set = get_scenario(db, valuation_id=valuation.id, scenario=scenario)
    current_assumptions = {
        "revenue_growth": assumption_set.revenue_growth_years_json,
        "target_margin": assumption_set.target_operating_margin,
        "sales_to_capital": assumption_set.sales_to_capital_ratio,
        "terminal_growth": assumption_set.terminal_growth_rate,
    }
    agent = NarrativeToNumbersAgent(db, user_id=current_user["id"])
    try:
        require_privacy_disclosure(request.privacy_disclosure_version)
        suggestions = agent.map_narrative(
            company_id=valuation.company_id,
            valuation_id=valuation.id,
            assumption_set_id=assumption_set.id,
            narrative_text=request.narrative_text,
            current_assumptions=current_assumptions,
        )
    except AIExecutionError as exc:
        raise public_ai_error(exc) from exc
    assert agent.last_ai_output is not None
    return ApiResponse(data=suggestions, meta=ai_output_meta(agent.last_ai_output))


@router.post("/valuation/{valuation_id}/scenarios/{scenario}/ai/memo")
def generate_valuation_memo(
    valuation_id: int,
    scenario: str,
    request: MemoRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict[str, Any]]:
    valuation = get_owned_valuation(db, valuation_id, current_user["id"])
    company = db.get(Company, valuation.company_id)
    assumption_set = get_scenario(db, valuation_id=valuation.id, scenario=scenario)
    output = db.scalar(select(DcfOutput).where(DcfOutput.assumption_set_id == assumption_set.id))
    if output is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot generate memo without DCF output. Run calculation first.",
        )
    agent = ValuationMemoAgent(db)
    try:
        require_privacy_disclosure(request.privacy_disclosure_version)
        memo_text = agent.generate_memo(
            company=company,
            valuation=valuation,
            assumption_set=assumption_set,
            output=output,
        )
    except AIExecutionError as exc:
        raise public_ai_error(exc) from exc
    assert agent.last_ai_output is not None
    return ApiResponse(
        data={
            "memo_markdown": memo_text,
            "ai_output_id": agent.last_ai_output.id,
            "provider_name": agent.last_ai_output.provider_name,
            "is_mock": agent.last_ai_output.is_mock,
            "confidence_label": agent.last_ai_output.confidence_label,
        },
        meta=ai_output_meta(agent.last_ai_output),
    )


@router.get("/valuation/{valuation_id}/scenarios/{scenario}/ai/memo")
def get_valuation_memo(
    valuation_id: int,
    scenario: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict[str, Any]]:
    valuation = get_owned_valuation(db, valuation_id, current_user["id"])
    assumption_set = get_scenario(db, valuation_id=valuation.id, scenario=scenario)
    ai_output = db.scalar(
        select(AiOutput)
        .where(
            AiOutput.user_id == current_user["id"],
            AiOutput.reference_type == "dcf_assumption_set",
            AiOutput.reference_id == assumption_set.id,
            AiOutput.prompt_version.like("%memo-writer%"),
            AiOutput.execution_status == "success",
        )
        .order_by(AiOutput.created_at.desc(), AiOutput.id.desc())
    )
    if ai_output is None:
        return ApiResponse(data={"memo_markdown": None})
    return ApiResponse(
        data={
            "memo_markdown": ai_output.output_text,
            "ai_output_id": ai_output.id,
            "created_at": ai_output.created_at,
            "provider_name": ai_output.provider_name,
            "is_mock": ai_output.is_mock,
            "confidence_label": ai_output.confidence_label,
        },
        meta=ai_output_meta(ai_output),
    )
