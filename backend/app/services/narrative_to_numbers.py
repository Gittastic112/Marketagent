import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.ai import AiOutput
from app.services.ai_contract import AIProvenance, execute_ai_generation


PROMPT_VERSION = "v1.1.0-narrative-to-numbers-contract"

NARRATIVE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "target_operating_margin": {"type": "NUMBER"},
        "target_operating_margin_reason": {"type": "STRING"},
        "revenue_growth_years": {
            "type": "OBJECT",
            "additionalProperties": {"type": "NUMBER"},
        },
        "revenue_growth_reason": {"type": "STRING"},
        "sales_to_capital_ratio": {"type": "NUMBER"},
        "sales_to_capital_reason": {"type": "STRING"},
        "terminal_growth_rate": {"type": "NUMBER"},
        "terminal_growth_reason": {"type": "STRING"},
    },
    "required": [
        "target_operating_margin",
        "target_operating_margin_reason",
        "revenue_growth_years",
        "revenue_growth_reason",
        "sales_to_capital_ratio",
        "sales_to_capital_reason",
        "terminal_growth_rate",
        "terminal_growth_reason",
    ],
}


class NarrativeToNumbersAgent:
    """Map a user narrative to reviewable DCF assumption estimates."""

    def __init__(self, db: Session, *, user_id: str):
        self.db = db
        self.user_id = user_id
        self.last_ai_output: AiOutput | None = None

    def map_narrative(
        self,
        *,
        company_id: int,
        valuation_id: int,
        assumption_set_id: int,
        narrative_text: str,
        current_assumptions: dict[str, Any],
    ) -> dict[str, Any]:
        prompt = f"""
Translate the user's qualitative company narrative into reviewable DCF estimates.
Use only the narrative and current assumptions below. Label the numerical outputs
as estimates, do not invent external evidence, and do not make a buy or sell
recommendation.

User narrative:
{narrative_text}

Current assumptions:
{json.dumps(current_assumptions, indent=2)}
"""

        def generate(provider):
            result = provider.generate_structured_response(prompt, NARRATIVE_SCHEMA)
            json.loads(result.output_text)
            return result

        self.last_ai_output = execute_ai_generation(
            self.db,
            provenance=AIProvenance(
                user_id=self.user_id,
                prompt_version=PROMPT_VERSION,
                input_text=prompt,
                reference_type="dcf_assumption_set",
                reference_id=assumption_set_id,
                source_ids=(
                    f"company:{company_id}",
                    f"valuation:{valuation_id}",
                    f"dcf_assumption_set:{assumption_set_id}",
                ),
                source_scope="user_narrative_and_current_assumptions",
                external_data_classes=("user_narrative", "valuation_assumptions"),
            ),
            generate=generate,
        )
        return json.loads(self.last_ai_output.output_text)
