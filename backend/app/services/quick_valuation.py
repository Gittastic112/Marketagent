from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.schemas.valuation_inputs import (
    DcfAssumptionSetCreate,
    QuickValuationCalculateRequest,
)
from app.models import Company
from app.models.dcf import DcfAssumptionSet
from app.services.assumption_autofill_engine import AssumptionAutofillEngine
from app.services.dcf import calculate_dcf


def generate_quick_valuation_assumptions(
    db: Session,
    company: Company,
) -> dict[str, Any]:
    generated = AssumptionAutofillEngine.draft_assumptions(db, company.id, {})
    assumptions = DcfAssumptionSetCreate.model_validate(generated["assumptions"])
    return {
        "company_id": company.id,
        "assumptions": assumptions,
        "provenance": generated["provenance"],
        "source_metadata": generated["source_metadata"],
        "warnings": generated["warnings"],
    }


def calculate_quick_valuation(
    company: Company,
    payload: QuickValuationCalculateRequest,
) -> dict[str, Any]:
    assumption_values = payload.model_dump(exclude={"company_id"})
    assumption_set = DcfAssumptionSet(
        scenario="Quick Run",
        reinvestment_method="sales_to_capital",
        **assumption_values,
    )
    output, projection_years, _ = calculate_dcf(assumption_set)
    supplied_growth_years = set(payload.revenue_growth_years_json)
    missing_growth_years = [
        year
        for year in range(1, payload.projection_years_count + 1)
        if str(year) not in supplied_growth_years
    ]
    warnings = list(output.warnings_json or [])
    if missing_growth_years:
        warnings.append({
            "severity": "warning",
            "module": "revenue_growth",
            "message": "Missing projection-year growth rates defaulted to 0%.",
            "affectedAssumptions": ["revenue_growth_years_json"],
            "suggestedFix": "Enter an explicit growth rate for every projection year.",
            "formula": None,
        })

    return {
        "company_id": company.id,
        "currency": company.currency,
        "sum_pv_fcff": output.sum_pv_fcff,
        "terminal_value": output.terminal_value,
        "pv_terminal_value": output.pv_terminal_value,
        "enterprise_value": output.enterprise_value,
        "cash": output.cash,
        "cross_holdings": output.cross_holdings,
        "debt": output.debt,
        "operating_leases": output.operating_leases,
        "minority_interests": output.minority_interests,
        "preferred_stock": output.preferred_stock,
        "employee_options_value": output.employee_options_value,
        "equity_value": output.equity_value,
        "diluted_shares": output.diluted_shares,
        "intrinsic_value_per_share": output.intrinsic_value_per_share,
        "current_market_price": output.current_market_price,
        "upside_downside_pct": output.upside_downside_pct,
        "terminal_value_pct_of_ev": output.terminal_value_pct_of_ev,
        "model_quality_score": output.model_quality_score,
        "warnings_json": warnings,
        "projection_years": [
            {
                "year_index": row.year_index,
                "revenue": row.revenue,
                "revenue_growth": row.revenue_growth,
                "ebit_margin": row.ebit_margin,
                "nopat": row.nopat,
                "reinvestment": row.reinvestment,
                "fcff": row.fcff,
                "roic": row.roic,
                "wacc": row.wacc,
                "pv_fcff": row.pv_fcff,
            }
            for row in projection_years
        ],
        "limitations": [
            "This quick calculation is not persisted as a valuation model.",
            "Generated assumptions remain draft inputs and require user review.",
            "Sensitivity and reverse-DCF outputs require the full valuation workflow.",
        ],
    }
