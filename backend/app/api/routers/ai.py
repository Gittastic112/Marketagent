from typing import Any

from fastapi import APIRouter, Depends, HTTPException
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
from app.schemas.valuation_ai import NarrativeRequest, ValuationAIRequest as MemoRequest
from app.services.valuation_ai_basis import explanation_evidence, latest_scenario, require_memo_basis, utc, valuation_basis


router = APIRouter()


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
    request: MemoRequest | None = None,
    assumption_set_id: int | None = None,
) -> DcfAssumptionSet:
    latest = latest_scenario(db, valuation_id, scenario)
    assumption_set = latest if assumption_set_id is None else db.scalar(
        select(DcfAssumptionSet).where(
            DcfAssumptionSet.valuation_model_id == valuation_id,
            DcfAssumptionSet.scenario == scenario,
            DcfAssumptionSet.id == assumption_set_id,
        )
    )
    if assumption_set is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if request and request.assumption_set_id is not None and (
        request.assumption_set_id != assumption_set.id
        or utc(request.assumptions_updated_at) != utc(assumption_set.updated_at)
    ):
        raise HTTPException(status_code=409, detail="Saved assumptions changed. Reload the latest version before requesting AI. No provider request was sent.")
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
    assumption_set = get_scenario(db, valuation_id=valuation.id, scenario=scenario, request=request)
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
            saved_basis=valuation_basis(assumption_set),
            privacy_disclosure_version=request.privacy_disclosure_version,
        )
    except AIExecutionError as exc:
        raise public_ai_error(exc) from exc
    assert agent.last_ai_output is not None
    return ApiResponse(data={**suggestions, "evidence": explanation_evidence(db, agent.last_ai_output, assumption_set)},
                       meta=ai_output_meta(agent.last_ai_output))


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
    assumption_set = get_scenario(db, valuation_id=valuation.id, scenario=scenario, request=request)
    try:
        require_memo_basis(assumption_set)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
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
            privacy_disclosure_version=request.privacy_disclosure_version,
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
            "created_at": agent.last_ai_output.created_at,
            "evidence": explanation_evidence(db, agent.last_ai_output, assumption_set),
        },
        meta=ai_output_meta(agent.last_ai_output),
    )


@router.get("/valuation/{valuation_id}/scenarios/{scenario}/ai/memo")
def get_valuation_memo(
    valuation_id: int,
    scenario: str,
    assumption_set_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict[str, Any]]:
    valuation = get_owned_valuation(db, valuation_id, current_user["id"])
    assumption_set = get_scenario(db, valuation_id=valuation.id, scenario=scenario, assumption_set_id=assumption_set_id)
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
            "evidence": explanation_evidence(db, ai_output, assumption_set),
        },
        meta=ai_output_meta(ai_output),
    )
