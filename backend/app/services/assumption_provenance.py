from datetime import date
from typing import Dict, Any, Optional


INPUT_CONTRACT = {
    "story_text": ("narrative", False, "all"),
    "growth_story": ("narrative", False, "all"),
    "margin_story": ("narrative", False, "all"),
    "reinvestment_story": ("narrative", False, "all"),
    "risk_story": ("narrative", False, "all"),
    "projection_years_count": ("operating", True, "all"),
    "starting_revenue": ("operating", True, "all"),
    "revenue_growth_years_json": ("operating", True, "all"),
    "target_operating_margin": ("operating", True, "all"),
    "current_operating_margin": ("operating", True, "all"),
    "tax_rate": ("operating", True, "all"),
    "sales_to_capital_ratio": ("operating", True, "fcff_dcf"),
    "reinvestment_method": ("operating", True, "fcff_dcf"),
    "starting_invested_capital": ("operating", True, "fcff_dcf"),
    "risk_free_rate": ("discount_rate", True, "all"),
    "equity_risk_premium": ("discount_rate", True, "all"),
    "beta": ("discount_rate", True, "all"),
    "cost_of_equity": ("discount_rate", True, "all"),
    "pre_tax_cost_of_debt": ("discount_rate", True, "fcff_dcf"),
    "debt_to_capital": ("discount_rate", True, "fcff_dcf"),
    "equity_to_capital": ("discount_rate", True, "fcff_dcf"),
    "wacc_start": ("discount_rate", True, "fcff_dcf"),
    "wacc_terminal": ("discount_rate", True, "fcff_dcf"),
    "terminal_growth_rate": ("terminal_value", True, "all"),
    "terminal_roic": ("terminal_value", True, "fcff_dcf"),
    "cash": ("equity_bridge", True, "all"),
    "cross_holdings": ("equity_bridge", False, "all"),
    "minority_interests": ("equity_bridge", True, "all"),
    "preferred_stock": ("equity_bridge", True, "all"),
    "debt": ("equity_bridge", True, "all"),
    "operating_leases": ("equity_bridge", False, "all"),
    "employee_options_value": ("equity_bridge", True, "all"),
    "diluted_shares": ("equity_bridge", True, "all"),
    "basic_shares": ("equity_bridge", False, "all"),
    "current_market_price": ("market_context", True, "all"),
    "cash_flow_currency": ("currency", True, "all"),
    "discount_rate_currency": ("currency", True, "all"),
    "currency_override_note": ("currency", False, "all"),
    "net_income": ("equity_cash_flow", False, "fcfe_ddm"),
    "capex": ("equity_cash_flow", False, "fcfe_ddm"),
    "depreciation": ("equity_cash_flow", False, "fcfe_ddm"),
    "change_in_nwc": ("equity_cash_flow", False, "fcfe_ddm"),
    "new_debt_issued": ("equity_cash_flow", False, "fcfe_ddm"),
    "debt_repaid": ("equity_cash_flow", False, "fcfe_ddm"),
    "dividends": ("equity_cash_flow", False, "fcfe_ddm"),
    "buybacks": ("equity_cash_flow", False, "fcfe_ddm"),
    "stock_issuances": ("equity_cash_flow", False, "fcfe_ddm"),
    "company_age": ("lifecycle", False, "special_case"),
    "probability_of_failure": ("distress", False, "distressed"),
    "distress_sale_proceeds": ("distress", False, "distressed"),
    "book_value_of_equity": ("financial_services", False, "financial_services"),
    "target_roe": ("financial_services", False, "financial_services"),
}


PLACEHOLDER_SOURCE_TYPES = {
    "missing_actual_default",
    "generic_market_default",
    "country_default",
}


DERIVED_NORMALIZED_METRICS = {
    "ebitda",
    "effective_tax_rate",
    "nopat",
    "net_debt",
    "working_capital",
    "reinvestment",
    "fcff",
    "fcfe",
    "invested_capital",
    "roic",
    "roe",
}


def _freshness_metadata(source_as_of: str | None, max_age_days: int) -> Dict[str, Any]:
    if not source_as_of:
        return {
            "source_as_of": None,
            "max_age_days": max_age_days,
            "age_days": None,
            "is_stale": False,
            "freshness_unknown": True,
            "requires_review": True,
        }
    try:
        parsed = date.fromisoformat(source_as_of[:10])
    except ValueError:
        return {
            "source_as_of": source_as_of,
            "max_age_days": max_age_days,
            "age_days": None,
            "is_stale": False,
            "freshness_unknown": True,
            "requires_review": True,
        }
    age_days = max((date.today() - parsed).days, 0)
    is_stale = age_days > max_age_days
    return {
        "source_as_of": parsed.isoformat(),
        "max_age_days": max_age_days,
        "age_days": age_days,
        "is_stale": is_stale,
        "freshness_unknown": False,
        "requires_review": is_stale,
    }


def _provenance(
    source_type: str,
    label: str,
    confidence: str,
    claim_type: Optional[str] = None,
    **metadata: Any,
) -> Dict[str, Any]:
    is_placeholder = source_type in PLACEHOLDER_SOURCE_TYPES
    if is_placeholder and not label.startswith("[PLACEHOLDER]"):
        label = f"[PLACEHOLDER] {label}"

    if claim_type is None:
        claim_type = {
            "company_actual": "Fact",
            "calculation": "Calculation",
            "formula": "Calculation",
            "industry_benchmark": "Estimate",
            "industry_benchmark_blend": "Estimate",
            "methodology_engine": "Estimate",
            "user_input": "User Assumption",
        }.get(source_type, "Estimate")

    return {
        "source_type": source_type,
        "label": label,
        "confidence": confidence,
        "claim_type": claim_type,
        "is_placeholder": is_placeholder,
        "requires_review": is_placeholder,
        **metadata,
    }


def _source_metadata(provenance: Dict[str, Any]) -> Dict[str, Any]:
    placeholder_fields = [
        key for key, value in provenance.items()
        if isinstance(value, dict) and value.get("is_placeholder")
    ]
    review_fields = [
        key for key, value in provenance.items()
        if isinstance(value, dict) and value.get("requires_review")
    ]
    legacy_fallback_fields = [
        key for key, value in provenance.items()
        if isinstance(value, dict) and value.get("fallback_policy")
    ]
    stale_source_fields = [
        key for key, value in provenance.items()
        if isinstance(value, dict) and value.get("is_stale")
    ]
    freshness_unknown_fields = [
        key for key, value in provenance.items()
        if isinstance(value, dict) and value.get("freshness_unknown")
    ]
    source_dates = sorted(
        value["source_as_of"]
        for value in provenance.values()
        if isinstance(value, dict) and value.get("source_as_of")
    )
    source_counts_by_type: Dict[str, int] = {}
    for value in provenance.values():
        if not isinstance(value, dict):
            continue
        source_type = value.get("source_type", "unknown")
        source_counts_by_type[source_type] = source_counts_by_type.get(source_type, 0) + 1

    currency_entries = [
        value
        for value in provenance.values()
        if isinstance(value, dict) and value.get("reporting_currency")
    ]
    source_rank = {
        "reviewed_metric_unit": 5,
        "reviewed_candidate_unit": 4,
        "filing_metadata": 3,
        "manual_entry": 2,
        "company_fallback": 1,
        "system_default": 0,
        "legacy_unknown": 0,
    }
    preferred_currency_entry = max(
        currency_entries,
        key=lambda value: source_rank.get(value.get("reporting_currency_source"), 0),
        default=None,
    )
    reporting_currency = (
        preferred_currency_entry.get("reporting_currency") if preferred_currency_entry else None
    )
    reporting_currency_source = (
        preferred_currency_entry.get("reporting_currency_source")
        if preferred_currency_entry
        else None
    )
    reporting_currency_confidence = (
        preferred_currency_entry.get("reporting_currency_confidence")
        if preferred_currency_entry
        else None
    )

    return {
        "promotion_ready": len(review_fields) == 0,
        "requires_review": len(review_fields) > 0,
        "placeholder_fields": placeholder_fields,
        "review_fields": review_fields,
        "source_counts_by_type": source_counts_by_type,
        "legacy_fallback_fields": legacy_fallback_fields,
        "stale_source_fields": stale_source_fields,
        "freshness_unknown_fields": freshness_unknown_fields,
        "oldest_source_as_of": source_dates[0] if source_dates else None,
        "latest_source_as_of": source_dates[-1] if source_dates else None,
        "reporting_currency": reporting_currency,
        "reporting_currency_source": reporting_currency_source,
        "reporting_currency_confidence": reporting_currency_confidence,
    }


def _input_readiness(
    assumptions: Dict[str, Any],
    provenance: Dict[str, Any],
) -> tuple[list[Dict[str, Any]], Dict[str, Any]]:
    rows: list[Dict[str, Any]] = []
    for field, (category, required, model_scope) in INPUT_CONTRACT.items():
        value = assumptions.get(field)
        entry = provenance.get(field, {})
        if not isinstance(entry, dict):
            entry = {}
        present = value is not None and value != ""
        source_type = entry.get("source_type")
        if not present:
            status = "missing" if required else "optional_unavailable"
        elif entry.get("is_placeholder") or entry.get("requires_review"):
            status = "review_required"
        elif source_type == "user_input":
            status = "user_input"
        elif source_type in {"formula", "calculation"}:
            status = "calculated"
        else:
            status = "source_backed"
        rows.append({
            "field": field,
            "category": category,
            "required": required,
            "model_scope": model_scope,
            "status": status,
            "source_type": source_type,
            "source_file": entry.get("source_file"),
            "source_as_of": entry.get("source_as_of"),
            "claim_type": entry.get("claim_type"),
        })

    counts: Dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    required_missing = [
        row["field"] for row in rows
        if row["required"] and row["status"] == "missing"
    ]
    required_review = [
        row["field"] for row in rows
        if row["required"] and row["status"] == "review_required"
    ]
    return rows, {
        "field_count": len(rows),
        "counts_by_status": counts,
        "required_missing_fields": required_missing,
        "required_review_fields": required_review,
        "ready_for_review": not required_missing,
        "ready_for_promotion": not required_missing and not required_review,
    }
