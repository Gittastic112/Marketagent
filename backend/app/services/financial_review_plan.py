"""Read-only source/metric work queue. Presence is never financial certification."""
import math
from collections import defaultdict
from datetime import UTC, date, datetime

from sqlalchemy import func, select, union
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.financial import FinancialExtractionCandidate, FinancialMetric, FinancialStatementPeriod
from app.models.raw_document import RawDocument
from app.models.document_asset import DocumentAsset
from app.models.source_fact_revision import SourceFactRevision
from app.services.valuation_input_units import canonical_financial_input


# These are evidence checklists, not sufficiency rules for model promotion.
COMMON = ("diluted_shares",)
TRACKS = {
    "operating": ("revenue", "ebit", "pre_tax_income", "tax_expense", "cash", "debt",
                  "capex", "depreciation", "change_in_nwc", "minority_interests", "preferred_stock",
                  "employee_options_value", *COMMON),
    "bank_equity": ("book_equity", "net_income", "net_income_parent", "net_income_nci",
                    "dividends", "preferred_stock", "employee_options_value", *COMMON),
    "equity_cash_flow": ("net_income", "capex", "depreciation", "change_in_nwc", "new_debt_issued",
                         "debt_repaid", "dividends", "buybacks", "stock_issuances", *COMMON),
}
ALIASES = {"change_in_nwc": ("change_in_nwc", "change_in_working_capital")}
LABELS = {
    "ebit": "Operating income (EBIT)", "pre_tax_income": "Profit before tax", "tax_expense": "Tax expense",
    "change_in_nwc": "Change in operating working capital", "net_income_parent": "Profit attributable to parent",
    "net_income_nci": "Profit attributable to noncontrolling interests", "book_equity": "Book equity",
    "minority_interests": "Noncontrolling-interest claim", "employee_options_value": "Employee award claim value",
    "diluted_shares": "Diluted shares and share-class scope",
}
MAX_EVIDENCE_ROWS = 2000


def _scaled(field, value, unit, currency):
    if value is None or not isinstance(value, (float, int)) or not math.isfinite(value):
        return None
    dimension = "diluted_shares" if field == "diluted_shares" else "revenue"
    return canonical_financial_input(dimension, value, {"unit": unit}, currency)[0]


def build_financial_review_plan(db: Session, company_id: int, *, track: str = "operating",
                                latest_year: int | None = None, as_of: date | None = None) -> dict:
    if track not in TRACKS:
        raise ValueError("Unknown financial review track")
    company = db.execute(select(Company.id, Company.ticker, Company.market, Company.currency)
                         .where(Company.id == company_id)).one_or_none()
    if company is None:
        raise LookupError("Company not found")
    today = as_of or datetime.now(UTC).date()
    if latest_year is not None and not 1900 <= latest_year <= today.year:
        raise ValueError("Review year must be a historical or current calendar year")
    source_count = db.scalar(select(func.count(RawDocument.id)).where(RawDocument.company_id == company_id)) or 0
    if latest_year is None:
        years_query = union(
            select(FinancialStatementPeriod.year.label("year")).where(
                FinancialStatementPeriod.company_id == company_id, FinancialStatementPeriod.period_type == "annual",
                FinancialStatementPeriod.year <= today.year),
            select(FinancialExtractionCandidate.fiscal_year.label("year")).where(
                FinancialExtractionCandidate.company_id == company_id, FinancialExtractionCandidate.period_type == "annual",
                FinancialExtractionCandidate.fiscal_year <= today.year),
        ).subquery()
        latest_year = db.scalar(select(func.max(years_query.c.year)))
    years = list(range(latest_year, latest_year - 3, -1)) if latest_year else []
    period_rows = list(db.execute(select(FinancialStatementPeriod.id, FinancialStatementPeriod.year,
        FinancialStatementPeriod.currency, FinancialStatementPeriod.currency_confidence, FinancialStatementPeriod.currency_source,
        FinancialStatementPeriod.report_date).where(FinancialStatementPeriod.company_id == company_id,
        FinancialStatementPeriod.period_type == "annual", FinancialStatementPeriod.year.in_(years))))
    period_ids = [row.id for row in period_rows]
    metrics = list(db.execute(select(FinancialMetric.id, FinancialMetric.period_id, FinancialMetric.metric_name,
        FinancialMetric.value, FinancialMetric.unit).where(FinancialMetric.period_id.in_(period_ids))
        .order_by(FinancialMetric.id).limit(MAX_EVIDENCE_ROWS + 1)))
    candidates = list(db.execute(select(FinancialExtractionCandidate.id, FinancialExtractionCandidate.fiscal_year,
        FinancialExtractionCandidate.metric_code, FinancialExtractionCandidate.value, FinancialExtractionCandidate.unit,
        FinancialExtractionCandidate.review_status, FinancialExtractionCandidate.raw_document_id,
        RawDocument.content_hash, DocumentAsset.id.label("asset_id"))
        .join(RawDocument, RawDocument.id == FinancialExtractionCandidate.raw_document_id)
        .outerjoin(DocumentAsset, DocumentAsset.raw_document_id == RawDocument.id)
        .where(FinancialExtractionCandidate.company_id == company_id, RawDocument.company_id == company_id,
            FinancialExtractionCandidate.period_type == "annual", FinancialExtractionCandidate.fiscal_year.in_(years))
        .order_by(FinancialExtractionCandidate.id).limit(MAX_EVIDENCE_ROWS + 1)))
    revisions = list(db.execute(select(SourceFactRevision.id, SourceFactRevision.financial_candidate_id,
        SourceFactRevision.fact_key, SourceFactRevision.value, SourceFactRevision.unit, SourceFactRevision.effective_at)
        .where(SourceFactRevision.company_id == company_id, SourceFactRevision.period_type == "annual",
            SourceFactRevision.superseded_at.is_(None), SourceFactRevision.effective_at >= date(years[-1], 1, 1) if years else False,
            SourceFactRevision.effective_at <= date(years[0], 12, 31) if years else False)
        .order_by(SourceFactRevision.id).limit(MAX_EVIDENCE_ROWS + 1)))
    truncated = any(len(rows) > MAX_EVIDENCE_ROWS for rows in (metrics, candidates, revisions))
    metrics, candidates, revisions = (rows[:MAX_EVIDENCE_ROWS] for rows in (metrics, candidates, revisions))
    periods_by_year, metrics_by_period, candidates_by_year = defaultdict(list), defaultdict(list), defaultdict(list)
    for row in period_rows: periods_by_year[row.year].append(row)
    for row in metrics: metrics_by_period[row.period_id].append(row)
    for row in candidates: candidates_by_year[row.fiscal_year].append(row)
    revision_by_candidate = {row.financial_candidate_id: row for row in revisions}
    periods = []
    for year in years:
        stored_periods = periods_by_year[year]
        period = stored_periods[0] if len(stored_periods) == 1 else None
        currency = period.currency if period else company.currency
        notes = []
        if len(stored_periods) > 1: notes.append("Multiple annual periods share this year; reconcile their reporting scopes.")
        if period and (period.currency != company.currency or period.currency_confidence != "high"):
            notes.append("Review reporting currency against the security and source unit.")
        if period and (period.report_date > today or (today - period.report_date).days > 550):
            notes.append("Review the reporting date and whether a newer annual source is needed.")
        fields = []
        for field in TRACKS[track]:
            aliases = ALIASES.get(field, (field,))
            recorded = [row for row in metrics_by_period[period.id] if row.metric_name in aliases] if period else []
            evidence = [row for row in candidates_by_year[year] if row.metric_code in aliases and row.review_status != "rejected"]
            scaled = [_scaled(field, row.value, row.unit, currency) for row in recorded]
            candidate_ids = [row.id for row in evidence]
            source_ids = sorted({row.raw_document_id for row in evidence})
            status, action = "missing", "Locate this item and its scope in the annual report or notes. An undisclosed amount is not zero."
            linked = []
            if len(stored_periods) > 1 or len(recorded) > 1:
                status, action = "ambiguous", "Resolve duplicate periods or metrics before selecting a value."
            elif recorded and scaled[0] is None:
                status, action = "unit_review", "Review the source currency, scale or share unit; the stored value cannot be aligned."
            elif recorded:
                for candidate in evidence:
                    revision = revision_by_candidate.get(candidate.id)
                    if (revision and candidate.content_hash and candidate.review_status in {"reviewed", "overridden", "promoted"}
                        and revision.fact_key in aliases and revision.effective_at.year == year
                        and _scaled(field, candidate.value, candidate.unit, currency) == scaled[0]
                        and _scaled(field, revision.value, revision.unit, currency) == scaled[0]):
                        linked.append(candidate)
                if linked:
                    status, action = "recorded_with_source", "Inspect the linked source, period and scope. This is traceability, not independent certification."
                else:
                    status, action = "source_review", "Trace this recorded value to reviewed source evidence; a manual value or normalized row alone is insufficient."
            elif any(row.review_status == "promoted" for row in evidence):
                status, action = "source_review", "A promoted source has no matching recorded metric. Inspect source history and period scope; do not promote it again."
            elif evidence:
                reviewed = [row for row in evidence if row.review_status in {"reviewed", "overridden"}]
                reviewed_values = {_scaled(field, row.value, row.unit, currency) for row in reviewed}
                if len(reviewed_values - {None}) > 1:
                    status, action = "ambiguous", "Reviewed candidates disagree after unit alignment. Resolve their period and statement scope before promotion."
                elif len(reviewed) == len(evidence) and None not in reviewed_values:
                    status, action = "promotion_review", "Review period and statement scope, then use the existing reviewed-candidate promotion workflow."
                else:
                    status, action = "candidate_review", "Review candidate values, units and exact source evidence before promotion."
            fields.append({"metric": field, "label": LABELS.get(field, field.replace("_", " ").capitalize()),
                "status": status, "action": action, "recorded_metric_ids": [row.id for row in recorded],
                "candidate_ids": candidate_ids[:20], "candidate_count": len(candidate_ids), "source_document_ids": source_ids[:20],
                "source_links": [{"candidate_id": row.id, "document_id": row.raw_document_id,
                    "href": (f"/documents/{row.raw_document_id}/financial-evidence?candidate_id={row.id}" if row.asset_id
                             else f"/documents/{row.raw_document_id}/sections")} for row in evidence[:5]]})
        periods.append({"year": year, "period_id": period.id if period else None, "currency": currency,
            "report_date": period.report_date if period else None, "notes": notes, "fields": fields,
            "source_linked_count": sum(field["status"] == "recorded_with_source" for field in fields),
            "checklist_count": len(fields)})
    actions = [
        {"label": "Add or inspect annual filings", "href": f"/companies/{company_id}/filings",
         "reason": "Keep consolidated/standalone scope, reporting period, currency and scale with each source."},
        {"label": "Review extracted candidates", "href": f"/companies/{company_id}/fundamentals#financial-candidate-review",
         "reason": "Review exact evidence before promotion; candidates and counts are not verified company facts."},
        {"label": "Review valuation assumptions", "href": f"/companies/{company_id}/valuation",
         "reason": "Forecasts, discount rates and complete equity claims require separate judgment."},
    ]
    return {"version": "financial-review-plan-v1", "company_id": company_id, "ticker": company.ticker,
        "track": track, "generated_at": datetime.now(UTC), "claim_type": "Calculation", "source_document_count": source_count,
        "latest_year": latest_year, "periods": periods, "actions": actions, "truncated": truncated,
        "basis": "Three consecutive annual years ending at the selected year, or the latest year present in stored evidence.",
        "limitations": [
            "This checklist cannot certify statement completeness, economic claim values, forecasts or valuation suitability.",
            "An explicit sourced zero differs from an absent disclosure. Share averages, closing awards and subsidiary claims require scope review.",
            "Bank equity review does not treat deposits as FCFF debt; capital adequacy and parent/subsidiary claims need separate review.",
            "Stored source links are not independent verification. Normalization and accounting-identity checks remain separate.",
            *([f"Evidence exceeds {MAX_EVIDENCE_ROWS} rows per source class; this bounded report is incomplete."] if truncated else []),
        ]}
