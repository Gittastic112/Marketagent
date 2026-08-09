import json
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.models.ai import AiOutput
from app.services.ai_contract import AIProvenance, execute_ai_generation

PROMPT_VERSION = "v1.0.0-dcf-mapper"

class DcfVariableImpact(BaseModel):
    variable_name: str = Field(..., description="The standard DCF variable impacted, e.g., 'Revenue Growth Rate', 'Operating Margin', 'Cost of Capital', 'Tax Rate', 'Sales to Capital Ratio'.")
    impact_direction: str = Field(..., description="Must be one of 'increase', 'decrease', or 'unknown'.")
    confidence: str = Field(..., description="Must be one of 'high', 'medium', or 'low'.")
    reasoning: str = Field(..., description="A short explanation of why this variable is impacted.")

class DcfMappingResult(BaseModel):
    impacted_variables: list[DcfVariableImpact]

def map_event_to_dcf_variables(
    db: Session,
    event_text: str,
    event_id: int | None,
    user_id: str,
) -> AiOutput:
    prompt = f"""
    Analyze the following market event or news snippet and determine which standard Discounted Cash Flow (DCF) valuation variables are likely to be impacted.

    Standard variables include:
    - Revenue Growth Rate
    - Operating Margin
    - Tax Rate
    - Cost of Capital (WACC)
    - Sales to Capital Ratio (Reinvestment)
    - Terminal Growth Rate

    Event text:
    {event_text}
    """

    schema = DcfMappingResult.model_json_schema()

    return execute_ai_generation(
        db,
        provenance=AIProvenance(
            user_id=user_id,
            reference_type="event",
            reference_id=event_id,
            prompt_version=PROMPT_VERSION,
            input_text=prompt,
        ),
        generate=lambda provider: provider.generate_structured_response(prompt, schema),
    )
