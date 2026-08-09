import json
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.dcf import DcfAssumptionSet, ValuationAssumptionChangeLog, ValuationModel
from app.models.event import Event
from app.services.ai_contract import AIProvenance, persist_ai_output

def evaluate_event_impact_on_valuation(
    db: Session,
    event_id: int,
    assumption_set_id: int,
    model_name: str = "deterministic-impact-v1",
) -> dict[str, Any]:
    """
    Evaluates how a market event impacts the current DCF assumptions.
    Returns a dict with 'is_stale', 'stale_reason', and 'proposed_changes'.
    """
    event = db.scalar(select(Event).where(Event.id == event_id))
    if not event:
        raise ValueError(f"Event {event_id} not found")

    assumption_set = db.scalar(select(DcfAssumptionSet).where(DcfAssumptionSet.id == assumption_set_id))
    if not assumption_set:
        raise ValueError(f"Assumption Set {assumption_set_id} not found")

    company = db.scalar(select(Company).where(Company.id == event.company_id))
    valuation = db.get(ValuationModel, assumption_set.valuation_model_id)
    if valuation is None:
        raise ValueError(f"Valuation Model {assumption_set.valuation_model_id} not found")

    # Construct Prompt Context
    prompt_context = f"""
    You are an expert equity analyst. A new market event has occurred for {company.name if company else 'the company'}.

    Event: {event.title}
    Type: {event.event_type}
    Description: {event.description}

    Current Valuation Assumptions:
    - Revenue Growth Years 1-5: (Check JSON)
    - Target Operating Margin: {assumption_set.target_operating_margin}
    - Sales to Capital Ratio: {assumption_set.sales_to_capital_ratio}
    - Risk Free Rate: {assumption_set.risk_free_rate}
    - Equity Risk Premium: {assumption_set.equity_risk_premium}

    Does this event materially alter the fundamental economics, growth prospects, or risk profile of the company?
    If so, the valuation is 'stale'.

    Respond STRICTLY in the following JSON format:
    {{
        "is_stale": true/false,
        "stale_reason": "Explanation of why the valuation is now stale (or why it isn't).",
        "proposed_changes": [
            {{
                "parameter_name": "e.g. target_operating_margin",
                "old_value": "e.g. 0.15",
                "new_value": "e.g. 0.12",
                "rationale": "Why this parameter needs to change."
            }}
        ]
    }}
    """

    # Deterministic triage only. This is persisted as mock output, not as an LLM claim.
    is_impactful = (event.priority_score and event.priority_score > 5) or "earnings" in event.title.lower() or "guidance" in event.title.lower()

    if is_impactful:
        llm_response = {
            "is_stale": True,
            "stale_reason": f"Event '{event.title}' likely impacts future margins or growth assumptions.",
            "proposed_changes": [
                {
                    "parameter_name": "target_operating_margin",
                    "old_value": str(assumption_set.target_operating_margin) if assumption_set.target_operating_margin else "None",
                    "new_value": "Requires review",
                    "rationale": "Material event requires reassessing margin trajectory."
                }
            ]
        }
    else:
        llm_response = {
            "is_stale": False,
            "stale_reason": "Event does not appear to materially alter long-term economic assumptions.",
            "proposed_changes": []
        }
    persist_ai_output(
        db,
        provenance=AIProvenance(
            user_id=valuation.user_id,
            prompt_version="v1.1.0-deterministic-impact",
            input_text=prompt_context,
            reference_type="dcf_assumption_set",
            reference_id=assumption_set.id,
            source_ids=(
                f"event:{event.id}",
                f"valuation:{valuation.id}",
                f"dcf_assumption_set:{assumption_set.id}",
            ),
            source_scope="event_and_valuation_assumptions",
            external_data_classes=(),
        ),
        provider_name="internal_rule_engine",
        model_name=model_name,
        is_mock=True,
        output_text=json.dumps(llm_response),
        limitations=(
            "Mock Data: deterministic priority and keyword triage only. "
            "No language model evaluated the event."
        ),
        confidence_label="low",
        transmission_scope="none",
    )

    # Process Impacts
    if llm_response.get("is_stale"):
        assumption_set.is_stale = True
        assumption_set.stale_reason = llm_response.get("stale_reason")
        assumption_set.stale_event_id = event.id

        for change in llm_response.get("proposed_changes", []):
            change_log = ValuationAssumptionChangeLog(
                valuation_model_id=assumption_set.valuation_model_id,
                assumption_set_id=assumption_set.id,
                event_id=event.id,
                parameter_name=change.get("parameter_name"),
                old_value=change.get("old_value"),
                new_value=change.get("new_value"),
                rationale=change.get("rationale")
            )
            db.add(change_log)

    db.commit()

    return llm_response
