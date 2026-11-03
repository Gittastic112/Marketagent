"""Non-writing reverse calculations with explicit saved-input and result evidence."""
from datetime import UTC, datetime
import math

from pydantic import ValidationError

from app.models.dcf import DcfAssumptionSet
from app.schemas.valuation_inputs import DcfAssumptionSetWrite, ReverseDcfRequest
from app.schemas.valuation_outputs import DiagnosticWarning, ReverseDcfResponse
from app.services.reverse_dcf_engine import MarketImpliedAssumptionSolver


def solve_saved_reverse_dcf(row: DcfAssumptionSet, request: ReverseDcfRequest) -> ReverseDcfResponse:
    if row.is_stale:
        raise ValueError("Saved assumptions are stale. Review and save a current calculation first.")
    model_type = row.valuation_model.model_type or "fcff_dcf"
    if model_type not in {"fcff_dcf", "distressed"}:
        raise ValueError("Reverse DCF currently supports FCFF and distressed models, not financial-services excess-return models.")
    try:
        saved = DcfAssumptionSetWrite.model_validate(row, from_attributes=True)
    except ValidationError:
        raise ValueError("Saved assumption units or currencies are invalid. Correct and save them first.") from None
    values = saved.model_dump()
    if any(isinstance(value, float) and not math.isfinite(value) for value in values.values()):
        raise ValueError("Saved inputs contain nonfinite numbers. Correct and save them first.")
    required = ("starting_revenue", "current_operating_margin", "target_operating_margin", "tax_rate",
        "sales_to_capital_ratio", "starting_invested_capital", "wacc_start", "wacc_terminal",
        "terminal_growth_rate", "terminal_roic")
    if any(values[field] is None for field in required):
        raise ValueError("Reverse DCF requires explicit saved revenue, margins, tax, reinvestment, WACC and terminal inputs; missing inputs are not guessed.")
    if row.wacc_terminal <= row.terminal_growth_rate or row.wacc_terminal <= 0 or row.terminal_roic <= 0:
        raise ValueError("Saved terminal assumptions require positive WACC/ROIC and growth below WACC.")
    growth = row.revenue_growth_years_json or {}
    for key, value in growth.items():
        if (key not in {str(i) for i in range(1, row.projection_years_count + 1)}
                or isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or not -1 < value <= 5):
            raise ValueError("Saved projection growth rates are invalid. Review the year-by-year decimal inputs.")
    if not saved.cash_flow_currency or not saved.discount_rate_currency:
        raise ValueError("Save explicit cash-flow and discount-rate currencies before reverse DCF.")
    output = row.outputs
    warnings = output.warnings_json if output else None
    if (output is None or output.assumption_set_id != row.id
            or output.intrinsic_value_per_share is None or not math.isfinite(output.intrinsic_value_per_share)
            or not isinstance(warnings, list)
            or any(not isinstance(w, dict) or w.get("severity") not in {"info", "watch", "warning"}
                   or not isinstance(w.get("message"), str) or not isinstance(w.get("module"), str) for w in warnings)):
        raise ValueError("Saved output is missing, invalid, critical or unrecognized. Review diagnostics and save a new calculation first.")
    shares = request.diluted_shares if request.diluted_shares is not None else row.diluted_shares
    if shares is None or not math.isfinite(shares) or shares <= 0:
        raise ValueError("Supply positive diluted shares or save them in the model. No one-share fallback is used.")
    try:
        implied, original, diagnostics = MarketImpliedAssumptionSolver.solve(row,
            request.target_parameter, request.current_market_price, shares, model_type=model_type)
        calculated = (MarketImpliedAssumptionSolver.evaluate(row, request.target_parameter,
            implied, request.current_market_price, shares, model_type) if implied is not None else None)
    except (ValueError, ArithmeticError):
        raise ValueError("Reverse DCF could not calculate finite values within its search bounds. Review the saved inputs.") from None
    if calculated is not None:
        try:
            diagnostics.extend(DiagnosticWarning.model_validate(w) for w in (calculated.warnings_json or []))
        except ValidationError:
            diagnostics.append(DiagnosticWarning(severity="blocking", module="reverse_dcf", message="Calculated diagnostics require review."))
    actual = calculated.intrinsic_value_per_share if calculated is not None else None
    residual = actual - request.current_market_price if actual is not None else None
    converged = (residual is not None and math.isfinite(residual) and abs(residual) <= 0.01
        and not any(w.severity in {"critical", "blocking"} for w in diagnostics))
    return ReverseDcfResponse(target_parameter=request.target_parameter,
        implied_value=implied if converged else None, original_value=original,
        intrinsic_value_at_implied=actual if converged else None,
        diagnostics=diagnostics, assumption_set_id=row.id, assumptions_updated_at=row.updated_at,
        calculated_at=datetime.now(UTC), currency=saved.cash_flow_currency, model_type=model_type,
        comparison_price=request.current_market_price, diluted_shares=shares,
        price_residual=residual if converged else None, converged=converged)
