import json

from sqlalchemy.orm import Session

from app.models.ai import AiOutput
from app.models.company import Company
from app.models.dcf import DcfAssumptionSet, DcfOutput, ValuationModel
from app.services.ai_contract import AIProvenance, execute_ai_generation


PROMPT_VERSION = "v1.1.0-memo-writer-contract"


class ValuationMemoAgent:
    """Write a source-scoped valuation memo from an existing DCF run."""

    def __init__(self, db: Session):
        self.db = db
        self.last_ai_output: AiOutput | None = None

    def generate_memo(
        self,
        company: Company,
        valuation: ValuationModel,
        assumption_set: DcfAssumptionSet,
        output: DcfOutput,
    ) -> str:
        context = {
            "company": {
                "name": company.name,
                "ticker": company.ticker,
                "industry": company.industry,
                "sector": company.sector,
            },
            "valuation": {
                "name": valuation.name,
                "type": valuation.model_type,
                "scenario": assumption_set.scenario,
            },
            "assumptions": {
                "story": assumption_set.story_text,
                "starting_revenue": assumption_set.starting_revenue,
                "revenue_growth": assumption_set.revenue_growth_years_json,
                "target_margin": assumption_set.target_operating_margin,
                "sales_to_capital": assumption_set.sales_to_capital_ratio,
                "wacc": assumption_set.wacc_start,
                "terminal_wacc": assumption_set.wacc_terminal,
                "terminal_growth": assumption_set.terminal_growth_rate,
            },
            "outputs": {
                "intrinsic_value_per_share": output.intrinsic_value_per_share,
                "current_market_price": output.current_market_price,
                "upside_downside_pct": output.upside_downside_pct,
                "implied_terminal_roic": output.implied_terminal_roic,
                "terminal_value_pct_of_ev": output.terminal_value_pct_of_ev,
            },
        }

        prompt = f"""
You are a financial valuation analyst following Aswath Damodaran's methodology.
Write a structured valuation memo for {company.name} ({company.ticker}) using only
the supplied calculation context. Do not invent external data and do not make a
buy or sell recommendation.

Calculation context:
{json.dumps(context, indent=2)}

Use these Markdown sections:
# Valuation Summary
State value, current price, implied upside or downside, and evidence gaps that
limit decision readiness.

# The Story
Restate the story that drives this valuation.

# Key Valuation Drivers
Explain growth, margin, and reinvestment assumptions.

# Risk and Cost of Capital
Explain WACC and terminal assumptions.

# Diagnostics and Red Flags
Identify terminal-value dependence, ROIC/WACC inconsistencies, and other model
risks visible in the supplied context.
"""

        self.last_ai_output = execute_ai_generation(
            self.db,
            provenance=AIProvenance(
                user_id=valuation.user_id,
                prompt_version=PROMPT_VERSION,
                input_text=prompt,
                reference_type="dcf_assumption_set",
                reference_id=assumption_set.id,
                source_ids=(
                    f"company:{company.id}",
                    f"valuation:{valuation.id}",
                    f"dcf_assumption_set:{assumption_set.id}",
                ),
                source_scope="valuation_inputs_and_outputs",
                external_data_classes=(
                    "company_metadata",
                    "valuation_assumptions",
                    "valuation_outputs",
                ),
            ),
            generate=lambda provider: provider.generate_chat_response(
                [{"role": "user", "content": prompt}]
            ),
        )
        return self.last_ai_output.output_text
