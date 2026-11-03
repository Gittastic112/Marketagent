"""Non-writing option analysis with explicit common-equity units and saved basis."""
from datetime import UTC, datetime
import hashlib
import json
import math

from pydantic import ValidationError

from app.models.dcf import DcfAssumptionSet
from app.schemas.real_options import SavedRealOptionRequest, SavedRealOptionResponse
from app.schemas.valuation_inputs import DcfAssumptionSetWrite
from app.services.real_options_service import BlackScholesRealOptionService


def calculate_saved_real_option(row: DcfAssumptionSet, request: SavedRealOptionRequest) -> SavedRealOptionResponse:
    expected = request.assumptions_updated_at.replace(tzinfo=None)
    if request.assumptions_updated_at.tzinfo is not None:
        expected = request.assumptions_updated_at.astimezone(UTC).replace(tzinfo=None)
    actual = row.updated_at.astimezone(UTC).replace(tzinfo=None) if row.updated_at.tzinfo else row.updated_at
    if row.is_stale or expected != actual:
        raise ValueError("Saved assumptions changed or are stale. Reload and review a current calculation.")
    if row.valuation_model.model_type != "fcff_dcf":
        raise ValueError("Saved real-option integration currently supports FCFF models only.")
    try:
        saved = DcfAssumptionSetWrite.model_validate(row, from_attributes=True)
    except ValidationError:
        raise ValueError("Saved input units or currencies are invalid. Correct and save them first.") from None
    if any(isinstance(v, float) and not math.isfinite(v) for v in saved.model_dump().values()):
        raise ValueError("Saved inputs contain nonfinite values.")
    if not saved.cash_flow_currency or not saved.discount_rate_currency or request.currency != saved.cash_flow_currency:
        raise ValueError("Option amounts must use the explicit saved cash-flow currency; no FX conversion is performed.")
    if not request.confirm_incremental_equity_basis or not all(request.eligibility.model_dump().values()):
        raise ValueError("Confirm every eligibility criterion and the incremental common-equity currency/scale basis before calculating.")
    output = row.outputs
    warnings = output.warnings_json if output else None
    shares = row.diluted_shares
    if (output is None or output.assumption_set_id != row.id
            or shares is None or not math.isfinite(shares) or shares <= 0
            or output.diluted_shares != shares
            or any(v is None or not math.isfinite(v) for v in (output.equity_value, output.intrinsic_value_per_share))
            or not math.isclose(output.equity_value / shares, output.intrinsic_value_per_share, rel_tol=1e-9, abs_tol=1e-9)
            or not isinstance(warnings, list)
            or any(not isinstance(w, dict) or w.get("severity") not in {"info", "watch", "warning"}
                   or not isinstance(w.get("module"), str) or not isinstance(w.get("message"), str) for w in warnings)):
        raise ValueError("Saved output, shares or diagnostics are missing, inconsistent or blocked. Save a valid calculation first.")
    option = BlackScholesRealOptionService.calculate(
        S=request.underlying_asset_value, K=request.exercise_price, t=request.option_life_years,
        r=request.risk_free_rate, sigma=request.volatility, y=request.dividend_yield_or_cost_of_delay,
        option_type=request.option_type, exclusivity_score=request.exclusivity_score)
    addition = 0 if request.is_already_counted else option["adjusted_option_value"]
    combined = output.equity_value + addition
    per_share = combined / shares
    option_per_share = option["adjusted_option_value"] / shares
    if not all(math.isfinite(v) for v in (combined, per_share, option_per_share)):
        raise ValueError("The supplied scale does not produce finite option values.")
    notes = [
        "Experimental supplemental analysis. A passing calculation does not certify company or project option value.",
        "Calculation from User Assumptions, not verified company facts or a live market quote.",
        "Eligibility and incremental common-equity scope are user confirmations, not independent verification.",
        "Black-Scholes and the exclusivity multiplier are simplified assumptions; results are not saved.",
    ]
    notes.extend(w["message"] for w in warnings)
    if request.is_already_counted:
        notes.append("Option value is already counted in the base DCF; no separate value was added.")
    fingerprint = json.dumps({
        "request": request.model_dump(mode="json"), "assumption_set_id": row.id,
        "output_created_at": output.created_at.isoformat(), "diluted_shares": shares,
        "base_equity_value": output.equity_value, "base_value_per_share": output.intrinsic_value_per_share,
    }, sort_keys=True, separators=(",", ":"))
    return SavedRealOptionResponse(
        assumption_set_id=row.id, assumptions_updated_at=row.updated_at, output_created_at=output.created_at,
        calculated_at=datetime.now(UTC), currency=saved.cash_flow_currency, model_type=row.valuation_model.model_type,
        input_sha256=hashlib.sha256(fingerprint.encode()).hexdigest(), diluted_shares=shares,
        base_equity_value=output.equity_value, base_value_per_share=output.intrinsic_value_per_share,
        raw_option_value=option["raw_option_value"], adjusted_option_value=option["adjusted_option_value"],
        option_value_per_share=option_per_share, option_adjusted_equity_value=combined,
        option_adjusted_intrinsic_value=per_share, warnings=notes)
