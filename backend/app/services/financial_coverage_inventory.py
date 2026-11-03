"""Read-only inventory for a fixed research scope. Counts never confer certification."""
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialExtractionCandidate, FinancialStatementPeriod, RawDocument
from app.models.financial import NormalizedFinancialSnapshot
from app.models.company_industry import CompanyIndustryMix


def build_financial_coverage_inventory(db: Session, scope: dict, checklist: dict) -> dict[str, Any]:
    securities = scope.get("securities", [])
    if not isinstance(securities, list) or not 1 <= len(securities) <= 50:
        raise ValueError("A fixed scope of 1-50 securities is required")
    requirements = {item["ticker"]: item for item in checklist["securities"]}
    if len(requirements) != len(checklist["securities"]) or any(s["ticker"] not in requirements for s in securities):
        raise ValueError("Each scoped security requires one review checklist")
    # Select scalar fields so this report never loads original PDF bytes or large
    # XBRL payloads through eager ORM relationships.
    companies = db.execute(select(Company.id, Company.ticker, Company.market,
        Company.primary_exchange, Company.currency, Company.security_type)
        .where(Company.ticker.in_([item["ticker"] for item in securities]))).all()
    identities = defaultdict(list)
    for company in companies:
        identities[(company.market, company.primary_exchange, company.ticker)].append(company)
    ids = [row.id for row in companies]
    sources = defaultdict(list)
    for row in db.execute(select(RawDocument.company_id, RawDocument.id, RawDocument.title, RawDocument.url,
        RawDocument.document_type, RawDocument.published_at, RawDocument.content_hash,
        RawDocument.raw_payload_json["payload_sha256"].as_string().label("payload_sha256"),
        RawDocument.raw_payload_json["sha256"].as_string().label("asset_sha256"))
        .where(RawDocument.company_id.in_(ids))).mappings():
        sources[row["company_id"]].append(dict(row))
    candidates = defaultdict(list)
    for row in db.execute(select(FinancialExtractionCandidate.company_id, FinancialExtractionCandidate.fiscal_year,
        FinancialExtractionCandidate.period_type, FinancialExtractionCandidate.metric_code,
        FinancialExtractionCandidate.unit, FinancialExtractionCandidate.review_status,
        FinancialExtractionCandidate.raw_document_id).where(FinancialExtractionCandidate.company_id.in_(ids))):
        candidates[row.company_id].append(row)
    periods = defaultdict(list)
    for row in db.execute(select(FinancialStatementPeriod.company_id, FinancialStatementPeriod.year,
        FinancialStatementPeriod.period_type, FinancialStatementPeriod.currency,
        FinancialStatementPeriod.currency_confidence).where(FinancialStatementPeriod.company_id.in_(ids))):
        periods[row.company_id].append(dict(row._mapping))
    normalized = Counter(db.scalars(select(NormalizedFinancialSnapshot.company_id)
                                   .where(NormalizedFinancialSnapshot.company_id.in_(ids))))
    mappings = set(db.scalars(select(CompanyIndustryMix.company_id).where(CompanyIndustryMix.company_id.in_(ids))))
    rows = []
    for security in securities:
        selected = identities[(security["market"], security["exchange"], security["ticker"])]
        requirement = requirements[security["ticker"]]
        base = {"ticker": security["ticker"], "market": security["market"], "exchange": security["exchange"],
            "expected_currency": security["currency"], "security_type": security["security_type"],
            "research_universe": security["research_universe"], "review_checklist": requirement,
            "certification_status": "not_assessed", "model_suitability": "requires_review"}
        if len(selected) != 1:
            rows.append({**base, "identity_status": "missing" if not selected else "ambiguous",
                         "company_id": None, "blockers": ["Resolve security identity before assessing coverage."]})
            continue
        company = selected[0]
        items = candidates[company.id]
        years = sorted({item.fiscal_year for item in items if item.fiscal_year is not None and item.period_type == "annual"})
        by_year = {}
        for year in years:
            annual = [item for item in items if item.fiscal_year == year and item.period_type == "annual"]
            by_year[str(year)] = {"metrics": sorted({item.metric_code for item in annual}),
                "review_status_counts": dict(Counter(item.review_status for item in annual)),
                "units": sorted({item.unit for item in annual if item.unit}),
                "missing_unit_count": sum(not item.unit or not item.unit.strip() for item in annual),
                "source_document_ids": sorted({item.raw_document_id for item in annual})}
        blockers = ["Review source units, period/scope, reconciliation, borrowing/share components and model suitability."]
        if not items:
            blockers.append("No extracted financial candidates for this security.")
        if any(item.review_status == "needs_review" for item in items):
            blockers.append("Unreviewed candidates remain; extraction is not approval.")
        if not normalized[company.id]:
            blockers.append("No normalized financial snapshots.")
        if company.id not in mappings:
            blockers.append("No stored weighted industry mapping; priors remain unconfirmed.")
        if requirement["review_track"] == "bank_equity":
            blockers.append("Bank equity/capital review required; do not infer FCFF debt from deposits.")
        if company.currency != security["currency"]:
            blockers.append("Stored currency conflicts with the selected security.")
        rows.append({**base, "company_id": company.id, "identity_status": "matched",
            "stored_currency": company.currency, "sources": sources[company.id],
            "candidate_count": len(items), "candidate_status_counts": dict(Counter(item.review_status for item in items)),
            "annual_candidates": by_year, "stored_periods": periods[company.id],
            "normalized_snapshot_count": normalized[company.id], "industry_mapping_present": company.id in mappings,
            "blockers": blockers})
    return {"report_version": "financial-coverage-inventory-v1", "generated_at": datetime.now(UTC).isoformat(),
        "scope_version": scope["version"], "scope_date": scope["selection_date"], "companies": rows,
        "claim_type": "Calculation", "basis": "Counts of stored evidence and explicit review gaps, not certification.",
        "limitations": ["Presence of sources, reviewed flags or normalized rows does not independently verify them.",
                        "No provider calls, candidate promotion, source modification or model approval performed."]}
