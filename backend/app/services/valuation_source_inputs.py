"""Read-only source adapters for reviewable drafts, never canonical financial facts.

SEC candidates remain unapproved. Derivations retain exact candidate IDs and a
single annual basis. FRED is USD-only; quotes retain their original as-of date.
"""
from datetime import date
import hashlib
import json
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.financial import FinancialExtractionCandidate
from app.models.macro import MacroObservation, MacroSeries
from app.models.market_price import MarketPrice
from app.services.sec_xbrl_extractor import EXTRACTION_METHOD


DRAFT_REVIEW_POLICY_VERSION = "2026-10-30-growth-lease-unit-and-model-review"


def freshness(as_of: date, max_age: int) -> dict:
    age = (date.today() - as_of).days
    return dict(source_as_of=as_of.isoformat(), age_days=age, max_age_days=max_age,
        is_stale=age > max_age, freshness_unknown=False, requires_review=True)


def stored_usd_risk_free_rate(db: Session, currency: str | None):
    if (currency or "").upper() != "USD":
        return None
    row = db.execute(select(MacroObservation, MacroSeries).join(MacroSeries).where(
        MacroSeries.name == "DGS10", MacroSeries.provider_name == "FRED",
        MacroSeries.source_url == "https://fred.stlouisfed.org/series/DGS10",
        MacroObservation.date_recorded <= date.today(),
    ).order_by(MacroObservation.date_recorded.desc(), MacroObservation.id.desc()).limit(1)).first()
    if not row:
        return None
    observation, series = row
    if series.units not in {"%", "Percent"} or series.frequency not in {"D", "Daily"}:
        return None
    if not math.isfinite(observation.value):
        return None
    return observation.value / 100, {
        "source_type": "market_reference", "claim_type": "Estimate", "confidence": "high",
        "label": "FRED DGS10: US 10-year Treasury yield (USD risk-free proxy)",
        "is_placeholder": False, "source_table": "macro_observations",
        "source_record_id": observation.id, "series_id": series.id, "source_url": series.source_url,
        "unit": "decimal", "original_unit": series.units, "original_value": observation.value,
        "currency": "USD", "formula": "DGS10 percent / 100",
        "warnings": "Published yield is a Fact; using it as the valuation risk-free rate is a reviewed methodology choice. This Treasury proxy is not reduced by a sovereign default spread; reconcile that convention with the selected equity premium.",
        **freshness(observation.date_recorded, 7),
    }


def stored_market_price(db: Session, company: Company):
    row = db.scalar(select(MarketPrice).where(
        MarketPrice.company_id == company.id, MarketPrice.as_of_date <= date.today(),
        MarketPrice.currency == company.currency,
        MarketPrice.claim_type.not_ilike("%mock%"), MarketPrice.price_type.not_ilike("%mock%"),
        MarketPrice.provider_name.not_ilike("%mock%"), MarketPrice.provider_name.not_ilike("%demo%"),
        MarketPrice.adjustment_state.in_(["unadjusted", "not_applicable"]),
    ).order_by(MarketPrice.as_of_date.desc(), MarketPrice.observed_at.desc(), MarketPrice.id.desc()).limit(1))
    if row is None or not math.isfinite(float(row.price)) or row.price <= 0:
        return None
    return float(row.price), {
        "source_type": "company_actual", "claim_type": row.claim_type, "confidence": "medium",
        "label": f"{row.provider_name} {row.price_type}; quote timing may be delayed",
        "is_placeholder": False, "source_table": "market_prices", "source_record_id": row.id,
        "source_url": row.source_url, "currency": row.currency,
        "source_timestamp": row.source_timestamp.isoformat() if row.source_timestamp else None,
        "delay_minutes": row.delay_minutes, "warnings": "; ".join(row.warnings_json or []),
        **freshness(row.as_of_date, 5),
    }


def sec_draft_inputs(db: Session, company: Company) -> dict:
    rows = db.scalars(select(FinancialExtractionCandidate).where(
        FinancialExtractionCandidate.company_id == company.id,
        FinancialExtractionCandidate.extraction_method.in_(["sec_xbrl_v2", EXTRACTION_METHOD]),
        FinancialExtractionCandidate.period_type == "annual",
    ).order_by(FinancialExtractionCandidate.id.desc())).all()
    # A rejected latest version must not fall back to an earlier version.
    latest = {}
    for row in rows:
        if row.extraction_method == "sec_xbrl_v2" and row.metric_code == "debt":
            continue  # Legacy long-term-only mapping cannot become total debt.
        latest.setdefault((row.metric_code, row.fiscal_year), row)
    by_year = {}
    for (metric, year), row in latest.items():
        locator = row.source_locator_json or {}
        if row.review_status == "rejected" or year is None or not math.isfinite(row.value):
            continue
        if row.unit != ("shares" if metric in {"diluted_shares", "basic_shares"} else company.currency):
            continue
        try:
            end = date.fromisoformat(locator["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if end > date.today():
            continue
        by_year.setdefault(year, {})[metric] = row
    if not by_year:
        return {}
    # Anchor to the most recent annual period, never cherry-pick old optional data.
    year = max(by_year)
    raw = by_year[year]
    anchor = raw.get("revenue") or next(iter(raw.values()))
    end = (anchor.source_locator_json or {})["end"]
    raw = {key: row for key, row in raw.items() if (row.source_locator_json or {}).get("end") == end}

    def source(row):
        locator = row.source_locator_json or {}
        return {
            "source_type": "sec_candidate", "claim_type": "Source Summary", "confidence": "medium",
            "label": f"SEC annual candidate FY{year}: {row.reported_label}", "is_placeholder": False,
            "source_table": "financial_extraction_candidates", "source_record_id": row.id,
            "candidate_ids": [row.id], "raw_document_id": row.raw_document_id,
            "source_url": locator.get("source_url"), "source_locator": locator,
            "fiscal_year": year, "period_type": "annual", "unit": row.unit,
            "reporting_currency": company.currency, "reporting_currency_source": "unreviewed_sec_unit",
            "reporting_currency_confidence": "medium", "review_status": row.review_status,
            "warnings": "Draft suggestion only. Review the filing, period, unit and scope before saving a model.",
            **freshness(date.fromisoformat(end), 550),
        }

    values = {key: (row.value, source(row)) for key, row in raw.items()}

    def derive(key, dependencies, calculate, label, warning=""):
        if any(name not in values for name in dependencies):
            return
        basis = {name: values[name][1] for name in dependencies}
        locators = [item.get("source_locator", {}) for item in basis.values()]
        if len({(item.get("end"), item.get("accession")) for item in locators}) != 1:
            return
        try:
            value = calculate(*(values[name][0] for name in dependencies))
        except (ZeroDivisionError, ValueError):
            return
        if not math.isfinite(value):
            return
        values[key] = (value, {**source(anchor), "source_type": "calculation", "claim_type": "Calculation",
            "label": label, "calculation_basis": basis,
            "source_locator": locators[0],
            "unit": "decimal" if key in {"operating_margin", "effective_tax_rate"} else company.currency,
            "candidate_ids": sorted({i for item in basis.values() for i in item.get("candidate_ids", [])}),
            "warnings": "Derived from unreviewed SEC candidates. " + warning})

    derive("operating_margin", ["ebit", "revenue"], lambda ebit, revenue: ebit / revenue,
        "Annual operating income / revenue")
    derive("effective_tax_rate", ["tax_expense", "pre_tax_income"],
        lambda tax, income: tax / income if income > 0 and 0 <= tax / income <= 1 else float("nan"),
        "Annual tax expense / pretax income", "Effective historical tax is not a forecast marginal tax rate.")
    if "current_debt" in values and "long_term_debt_noncurrent" in values:
        derive("debt", ["current_debt", "long_term_debt_noncurrent"], lambda a, b: a + b,
            "Current debt + noncurrent long-term debt", "Check lease inclusion and other financing claims.")
    elif "long_term_debt_total" in values and "short_term_borrowings" in values:
        derive("debt", ["long_term_debt_total", "short_term_borrowings"], lambda a, b: a + b,
            "Long-term debt + short-term borrowings", "Check lease inclusion and other financing claims.")
    if "operating_leases" not in values:
        derive("operating_leases", ["operating_lease_current", "operating_lease_noncurrent"], lambda a, b: a + b,
            "Current + noncurrent operating lease liabilities", "Do not add again if already included in debt.")
    derive("invested_capital", ["book_equity", "debt", "cash"], lambda equity, debt, cash: equity + debt - cash,
        "Book equity + reported debt - cash", "Review lease, non-operating asset and accounting adjustments.")
    if values.get("invested_capital", (0,))[0] <= 0:
        values.pop("invested_capital", None)
    if "diluted_shares" in values:
        values["diluted_shares"][1]["warnings"] += " Annual weighted-average issuer shares are not current class-specific shares; check splits and share classes."
    if "book_equity" in values:
        values["book_value_of_equity"] = values["book_equity"]
    direct = {"revenue", "operating_margin", "effective_tax_rate", "cash", "debt", "invested_capital",
        "operating_leases", "minority_interests", "preferred_stock", "diluted_shares", "basic_shares",
        "net_income", "capex", "depreciation", "dividends", "buybacks", "stock_issuances",
        "new_debt_issued", "debt_repaid", "book_value_of_equity"}
    return {key: value for key, value in values.items() if key in direct}


def source_input_signature(db: Session, company: Company) -> str:
    inputs = sec_draft_inputs(db, company)
    inputs["draft_review_policy_version"] = DRAFT_REVIEW_POLICY_VERSION
    inputs["company_context"] = {"currency": company.currency, "country": company.country}
    inputs["risk_free_rate"] = stored_usd_risk_free_rate(db, company.currency)
    inputs["current_market_price"] = stored_market_price(db, company)
    # Freshness changes matter too: yesterday's reviewed rate may become stale.
    return hashlib.sha256(json.dumps(inputs, sort_keys=True, default=str).encode()).hexdigest()
