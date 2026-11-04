import json
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.models.ai import AiOutput
from app.services.ai_contract import AIProvenance, execute_ai_generation

PROMPT_VERSION = "v1.0.0-contradiction-detector"

class ContradictionAlertModel(BaseModel):
    is_contradiction: bool = Field(..., description="True if the evidence directly contradicts the assumption, False otherwise.")
    confidence: str = Field(..., description="Must be one of 'high', 'medium', or 'low'.")
    reasoning: str = Field(..., description="A short explanation of why the evidence contradicts the assumption.")

def detect_thesis_contradiction(
    db: Session,
    evidence_text: str,
    assumption_text: str,
    event_id: int | None,
    user_id: str,
    privacy_disclosure_version: str | None = None,
) -> AiOutput:
    prompt = f"""
    Analyze the following market event evidence and determine if it directly contradicts the stated thesis assumption.

    Thesis Assumption:
    {assumption_text}

    Event Evidence:
    {evidence_text}
    """

    schema = ContradictionAlertModel.model_json_schema()

    return execute_ai_generation(
        db,
        provenance=AIProvenance(
            user_id=user_id,
            reference_type="event",
            reference_id=event_id,
            prompt_version=PROMPT_VERSION,
            input_text=prompt,
            external_data_classes=("event_text", "private_thesis_assumptions"),
            action_key="thesis_contradiction", privacy_disclosure_version=privacy_disclosure_version,
        ),
        generate=lambda provider: provider.generate_structured_response(prompt, schema),
    )
