"""Read-only mapping from one owned saved assumption set, never industry priors."""

import hashlib
import json
from math import isfinite
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dcf import DcfAssumptionSet, ValuationModel


DIRECT_FIELDS = {
    "revenue": "starting_revenue", "netIncome": "net_income",
    "bookEquity": "book_value_of_equity", "investedCapital": "starting_invested_capital",
    "cash": "cash", "debt": "debt", "dilutedShares": "diluted_shares",
}


def build_saved_relative_inputs(row: DcfAssumptionSet, *, company_id: int) -> dict[str, Any]:
    financials: dict[str, float | None] = {}
    fields: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []
    warnings = [
        "Saved model values are User Assumptions, not independently verified company actuals.",
        "Confirm all monetary inputs use one currency and scale, and diluted shares use the matching scale. No unit conversion is performed.",
        "Enterprise-to-equity methods use the simplified bridge: enterprise value minus debt plus cash.",
    ]

    def read(field: str) -> float | None:
        value = getattr(row, field, None)
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            blockers.append(f"{field} must be a finite number.")
            return None
        if field in {"cash", "debt"} and value < 0:
            blockers.append(f"{field} must be nonnegative.")
            return None
        if field == "diluted_shares" and value <= 0:
            blockers.append("diluted_shares must be positive.")
            return None
        if field == "current_operating_margin" and not -1 <= value <= 1:
            blockers.append("current_operating_margin must be a decimal rate between -1 and 1.")
            return None
        return value

    for target, source in DIRECT_FIELDS.items():
        value = read(source)
        financials[target] = value
        fields[target] = {
            "value": value, "claimType": "User Assumption", "sourceFields": [source],
            "reason": "Copied from saved assumptions." if value is not None else "Missing or invalid saved input; no fallback applied.",
        }
    margin = read("current_operating_margin")
    revenue = financials["revenue"]
    ebit = revenue * margin if revenue is not None and margin is not None else None
    if ebit is not None and not isfinite(ebit):
        blockers.append("Derived EBIT exceeds the supported numeric range.")
        ebit = None
    financials["ebit"] = ebit
    fields["ebit"] = {"value": ebit, "claimType": "Calculation",
        "sourceFields": ["starting_revenue", "current_operating_margin"],
        "reason": "Starting revenue × current operating margin; unavailable if either operand is missing or invalid."}
    financials["ebitda"] = None
    fields["ebitda"] = {"value": None, "claimType": "Calculation", "sourceFields": [],
        "reason": "Unavailable: saved depreciation does not establish complete depreciation and amortization for EBITDA. EBIT is not substituted."}
    for field in ("cross_holdings", "minority_interests", "preferred_stock", "operating_leases", "employee_options_value"):
        if getattr(row, field, None) not in (None, 0):
            warnings.append(f"Saved {field} is not included in the simplified relative-valuation bridge.")
    currency = (row.cash_flow_currency or "").strip().upper()
    if len(currency) != 3 or not currency.isascii() or not currency.isalpha():
        currency = None
        blockers.append("Save an explicit three-letter cash-flow currency before calculating.")
    if row.is_stale:
        blockers.append("Saved assumptions are marked stale; review and save current inputs.")
    method_inputs = []
    for method, field in (("pe", "netIncome"), ("pbv", "bookEquity"), ("ps", "revenue"),
            ("ev_sales", "revenue"), ("ev_ebitda", "ebitda"), ("ev_ebit", "ebit")):
        value = financials[field]
        available = value is not None and value > 0
        bridge_available = not method.startswith("ev_") or all(financials[key] is not None for key in ("cash", "debt"))
        method_inputs.append({"method": method, "requiredField": field,
            "hasPositiveBase": available,
            "hasPerShareInputs": available and bridge_available and financials["dilutedShares"] is not None,
            "reason": "Positive company base is available; benchmark coverage still needs checking."
                if available else f"A positive {field} is unavailable; this method cannot calculate."})
    if not any(method["hasPositiveBase"] for method in method_inputs):
        blockers.append("No method has a positive company financial base. Supply current saved inputs before calculating.")
    result = {
        "assumptionSetId": row.id, "modelId": row.valuation_model_id, "companyId": company_id,
        "savedAt": row.created_at.isoformat() if row.created_at else None,
        "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        "currency": currency, "isStale": bool(row.is_stale),
        "financials": financials, "fields": fields, "methodInputs": method_inputs,
        "canCalculate": not blockers, "blockers": blockers, "warnings": warnings,
    }
    result["inputBasisSha256"] = hashlib.sha256(json.dumps(result, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return result


def load_saved_relative_inputs(db: Session, *, assumption_id: int, user_id: str) -> dict[str, Any]:
    owned = db.execute(select(DcfAssumptionSet, ValuationModel)
        .join(ValuationModel, DcfAssumptionSet.valuation_model_id == ValuationModel.id)
        .where(DcfAssumptionSet.id == assumption_id, ValuationModel.user_id == user_id)).first()
    if owned is None:
        raise HTTPException(status_code=404, detail="Assumption set not found")
    row, model = owned
    result = build_saved_relative_inputs(row, company_id=model.company_id)
    result["isMock"] = "mock" in model.name.lower()
    return result


def saved_input_meta(basis: dict[str, Any]) -> dict[str, Any]:
    return {"source": "saved_dcf_user_assumptions", "confidence": "medium",
        "last_updated": basis["updatedAt"], "is_stale": basis["isStale"],
        "is_mock": basis["isMock"], "warnings": basis["warnings"] + basis["blockers"]}
