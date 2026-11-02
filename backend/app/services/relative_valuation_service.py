"""DCF-implied ratios use explicit saved inputs, never earnings or EBITDA proxies."""
from math import isfinite
from typing import Any

from app.schemas.valuation_outputs import DcfOutputCreate, DiagnosticWarning


RATIO_FIELDS = ("implied_pe", "implied_ev_ebitda", "implied_ev_sales", "implied_ev_ebit", "implied_pbv")


def field(value: Any, name: str) -> Any:
    return value.get(name) if isinstance(value, dict) else getattr(value, name, None)


def finite(value: Any) -> bool:
    return isinstance(value, (float, int)) and not isinstance(value, bool) and isfinite(value)


def implied_pricing(output: Any, assumptions: Any) -> dict[str, Any]:
    revenue = field(assumptions, "starting_revenue")
    margin = field(assumptions, "current_operating_margin")
    ebit = revenue * margin if finite(revenue) and revenue >= 0 and finite(margin) and -1 <= margin <= 1 else None
    warnings = field(output, "warnings_json") or []
    blocked = bool(field(assumptions, "is_stale")) or any(
        isinstance(warning, dict) and warning.get("module") != "relative_pricing"
        and warning.get("severity") in {"critical", "blocking"} for warning in warnings)
    methods = []
    for key, label, numerator_field, denominator, sources, formula in (
        ("implied_pe", "Implied P/E", "equity_value", field(assumptions, "net_income"), ["net_income"], "DCF equity value / saved net income"),
        ("implied_ev_ebitda", "Implied EV/EBITDA", "enterprise_value", None, [], "Unavailable without complete depreciation and amortization evidence"),
        ("implied_ev_sales", "Implied EV/Sales", "enterprise_value", revenue, ["starting_revenue"], "DCF enterprise value / saved starting revenue"),
        ("implied_ev_ebit", "Implied EV/EBIT", "enterprise_value", ebit, ["starting_revenue", "current_operating_margin"], "DCF enterprise value / (saved starting revenue × current operating margin)"),
        ("implied_pbv", "Implied P/B", "equity_value", field(assumptions, "book_value_of_equity"), ["book_value_of_equity"], "DCF equity value / saved book equity"),
    ):
        numerator = field(output, numerator_field)
        value = None
        reason = None
        if assumptions is None:
            reason = "Saved input context is unavailable; stored legacy ratios are not displayed."
        elif blocked:
            reason = "Saved inputs are stale or the DCF has critical/blocking diagnostics."
        elif key == "implied_ev_ebitda":
            reason = "Complete D&A evidence is unavailable; EBIT is not EBITDA."
        elif not finite(numerator):
            reason = "DCF value is missing or non-finite."
        elif not finite(denominator) or denominator <= 0:
            reason = "A positive finite saved denominator is unavailable."
        else:
            ratio = numerator / denominator
            if finite(ratio):
                value = ratio
            else:
                reason = "Ratio exceeds the supported numeric range."
        methods.append({"field": key, "label": label, "value": value,
            "numerator": numerator if finite(numerator) else None,
            "denominator": denominator if finite(denominator) else None,
            "sourceFields": [numerator_field, *sources], "formula": formula, "reason": reason})
    return {"version": 1, "claimType": "Calculation", "assumptionSetId": field(assumptions, "id"),
        "outputCreatedAt": field(output, "created_at"),
        "assumptionsUpdatedAt": field(assumptions, "updated_at"),
        "isStale": bool(field(assumptions, "is_stale")), "methods": methods,
        "note": "Ratios use stored DCF values and saved User Assumptions, not verified earnings or market multiples. Monetary inputs must share currency and scale. Reading does not rerun the DCF, recalculate its stored quality score, or rewrite historical records."}


class RelativeValuationService:
    @classmethod
    def calculate_implied_multiples(cls, output: DcfOutputCreate, assumption_set: Any) -> None:
        for method in implied_pricing(output, assumption_set)["methods"]:
            setattr(output, method["field"], method["value"])

    @classmethod
    def generate_relative_pricing_diagnostics(cls, output: DcfOutputCreate) -> list[DiagnosticWarning]:
        warnings = []
        for value, threshold, label, source, formula in (
            (output.implied_pe, 50, "P/E", "net_income", "DCF equity value / saved net income"),
            (output.implied_ev_sales, 15, "EV/Sales", "starting_revenue", "DCF enterprise value / saved starting revenue"),
        ):
            if finite(value) and value > threshold:
                warnings.append(DiagnosticWarning(severity="warning", module="relative_pricing",
                    message=f"DCF-implied {label} exceeds the configured {threshold}x review threshold ({value:.1f}x). This is a heuristic, not an empirical industry benchmark.",
                    affectedAssumptions=[source], suggestedFix="Review the saved denominator and DCF assumptions; this threshold does not determine fair value.", formula=formula))
        return warnings


def reconcile_output_read(data: dict[str, Any], assumptions: Any) -> dict[str, Any]:
    """Return a detached response copy. Never mutate persisted ratios or warnings."""
    result = dict(data)
    price = field(assumptions, "current_market_price") if assumptions is not None else result.get("current_market_price")
    stored_price = result.get("current_market_price")
    if not finite(price) or price <= 0 or not finite(stored_price) or stored_price <= 0:
        # Historical calculations stored 0/0 for absent comparison data. Withhold
        # those values in the response without rewriting the saved calculation.
        result["current_market_price"] = None
        result["upside_downside_pct"] = None
    elif not finite(result.get("upside_downside_pct")):
        result["upside_downside_pct"] = None
    basis = implied_pricing(result, assumptions)
    for method in basis["methods"]:
        result[method["field"]] = method["value"]
    retained = [warning for warning in (result.get("warnings_json") or [])
        if not isinstance(warning, dict) or warning.get("module") != "relative_pricing"]
    pricing_output = DcfOutputCreate(**{key: result.get(key) for key in ("assumption_set_id", *RATIO_FIELDS)})
    result["warnings_json"] = retained + [warning.model_dump() for warning in RelativeValuationService.generate_relative_pricing_diagnostics(pricing_output)]
    result["implied_pricing_basis"] = basis
    return result
