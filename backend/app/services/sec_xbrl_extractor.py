from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, date, datetime
from typing import Any, Callable

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialExtractionCandidate, RawDocument, Source
from app.models.company_setup import CompanySetupWorkflow
from app.providers.safe_http import fetch_public_json
from app.services.sec_ingestion import _normalize_cik, _sec_headers


SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
EXTRACTION_METHOD = "sec_xbrl_v3"
FLOW_METRICS = {"revenue", "ebit", "net_income", "capex", "diluted_shares", "basic_shares",
    "depreciation", "dividends", "buybacks", "stock_issuances", "tax_expense", "pre_tax_income",
    "long_term_debt_issued", "long_term_debt_repaid", "new_debt_issued", "debt_repaid", "interest_expense"}
CORE_METRICS = {"revenue", "ebit", "net_income", "cash", "debt", "diluted_shares"}
DEFAULT_ANNUAL_PERIODS = 5
MAX_COMPANY_FACTS_BYTES = 32 * 1024 * 1024

# Prefer the latest filing, then this concept order. Components keep explicit
# names: a long-term balance or cash flow is not total debt or total borrowing.
US_GAAP_MAPPING = {
    "RevenueFromContractWithCustomerExcludingAssessedTax": "revenue",
    "Revenues": "revenue",
    "SalesRevenueNet": "revenue",
    "SalesRevenueGoodsNet": "revenue",
    "OperatingIncomeLoss": "ebit",
    "NetIncomeLoss": "net_income",
    "ProfitLoss": "net_income",
    "CashAndCashEquivalentsAtCarryingValue": "cash",
    "Cash": "cash",
    "LongTermDebt": "long_term_debt_total",
    "LongTermDebtCurrent": "long_term_debt_current",
    "LongTermDebtNoncurrent": "long_term_debt_noncurrent",
    "DebtCurrent": "current_debt",
    "ShortTermBorrowings": "short_term_borrowings",
    "CommercialPaper": "commercial_paper",
    "PaymentsToAcquirePropertyPlantAndEquipment": "capex",
    "WeightedAverageNumberOfDilutedSharesOutstanding": "diluted_shares",
    "WeightedAverageNumberOfSharesOutstandingBasic": "basic_shares",
    "DepreciationDepletionAndAmortization": "depreciation",
    "DepreciationAndAmortization": "depreciation",
    "DepreciationDepletionAndAmortizationPropertyPlantAndEquipment": "depreciation",
    "PaymentsOfDividendsCommonStock": "dividends",
    "PaymentsOfDividends": "dividends",
    "PaymentsForRepurchaseOfCommonStock": "buybacks",
    "ProceedsFromStockIssuance": "stock_issuances",
    "ProceedsFromIssuanceOfCommonStock": "stock_issuances",
    "ProceedsFromIssuanceOfLongTermDebt": "long_term_debt_issued",
    "RepaymentsOfLongTermDebt": "long_term_debt_repaid",
    "ProceedsFromIssuanceOfDebt": "new_debt_issued",
    "RepaymentsOfDebt": "debt_repaid",
    "IncomeTaxExpenseBenefit": "tax_expense",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest": "pre_tax_income",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments": "pre_tax_income",
    "InterestExpense": "interest_expense",
    "StockholdersEquity": "book_equity",
    "AssetsCurrent": "current_assets",
    "LiabilitiesCurrent": "current_liabilities",
    "MinorityInterest": "minority_interests",
    "PreferredStockValue": "preferred_stock",
    "OperatingLeaseLiability": "operating_leases",
    "OperatingLeaseLiabilityCurrent": "operating_lease_current",
    "OperatingLeaseLiabilityNoncurrent": "operating_lease_noncurrent",
}
CONCEPT_PRIORITY = {
    metric: {
        concept: index
        for index, concept in enumerate(
            candidate_concept
            for candidate_concept, candidate_metric in US_GAAP_MAPPING.items()
            if candidate_metric == metric
        )
    }
    for metric in set(US_GAAP_MAPPING.values())
}


def _select_primary_unit(
    metric_code: str,
    units: dict[str, list[dict[str, Any]]],
    reporting_currency: str | None,
) -> str | None:
    preferred = (
        ("shares",)
        if metric_code in {"basic_shares", "diluted_shares"}
        else ((reporting_currency or "USD").upper(),)
    )
    for unit in preferred:
        if unit in units:
            return unit
    return None


def _parse_iso_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _annual_period_year(metric_code: str, observation: dict[str, Any]) -> int | None:
    if observation.get("form") not in {"10-K", "10-K/A"} or observation.get("fp") not in {None, "FY"}:
        return None
    end = _parse_iso_date(observation.get("end"))
    value = observation.get("val")
    filed = _parse_iso_date(observation.get("filed"))
    if (end is None or end > date.today() or (filed and filed > date.today())
        or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
        return None
    if metric_code in FLOW_METRICS:
        start = _parse_iso_date(observation.get("start"))
        if start is None or not 300 <= (end - start).days <= 380:
            return None
    return end.year


def _selection_quality(metric_code: str, concept: str, observation: dict[str, Any]) -> tuple[str, int, str]:
    concept_rank = CONCEPT_PRIORITY[metric_code][concept]
    return (
        str(observation.get("filed") or ""),
        -concept_rank,
        str(observation.get("accn") or ""),
    )


def select_annual_facts(
    us_gaap_facts: dict[str, Any],
    reporting_currency: str | None,
    max_years: int = DEFAULT_ANNUAL_PERIODS,
) -> dict[tuple[str, int], dict[str, Any]]:
    selected: dict[tuple[str, int], dict[str, Any]] = {}
    for concept, metric_code in US_GAAP_MAPPING.items():
        concept_data = us_gaap_facts.get(concept)
        if not isinstance(concept_data, dict):
            continue
        units = concept_data.get("units")
        if not isinstance(units, dict) or not units:
            continue
        unit = _select_primary_unit(metric_code, units, reporting_currency)
        if unit is None or not isinstance(units.get(unit), list):
            continue
        for observation in units.get(unit, []):
            if not isinstance(observation, dict):
                continue
            fiscal_year = _annual_period_year(metric_code, observation)
            if fiscal_year is None:
                continue
            item = {
                "metric_code": metric_code,
                "concept": concept,
                "concept_label": concept_data.get("label", concept),
                "unit": unit,
                "fiscal_year": fiscal_year,
                "observation": observation,
            }
            key = (metric_code, fiscal_year)
            current = selected.get(key)
            if current is None or _selection_quality(metric_code, concept, observation) > _selection_quality(
                metric_code,
                current["concept"],
                current["observation"],
            ):
                selected[key] = item
    selected_years = set(sorted({year for _, year in selected}, reverse=True)[:max_years])
    return {key: item for key, item in selected.items() if key[1] in selected_years}


def get_or_create_sec_source(db: Session) -> Source:
    source = db.scalar(select(Source).where(Source.name == "SEC EDGAR"))
    if source:
        return source
    source = Source(
        name="SEC EDGAR",
        source_type="sec",
        base_url="https://www.sec.gov",
        reliability_score=100,
    )
    db.add(source)
    db.flush()
    return source


def _download_company_facts(url: str, headers: dict[str, str]) -> Any:
    return fetch_public_json(url, headers=headers, max_bytes=MAX_COMPANY_FACTS_BYTES)


def fetch_company_facts(
    cik: str,
    http_get: Callable[..., Any] | None = None,
    user_agent: str | None = None,
) -> dict[str, Any]:
    normalized_cik = _normalize_cik(cik)
    url = SEC_COMPANY_FACTS_URL.format(cik=normalized_cik)
    headers = _sec_headers(user_agent)
    if http_get is not None:
        # Retain the existing explicit test/in-process injection contract.
        response = http_get(url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
    else:
        data = _download_company_facts(url, headers)
    if not isinstance(data, dict):
        raise ValueError("SEC company facts response must be a JSON object")
    if _normalize_cik(str(data.get("cik", ""))) != normalized_cik:
        raise ValueError("SEC returned facts for a different issuer")
    return data


def company_sec_cik(company: Company) -> str | None:
    # Alternate listed share classes can share an issuer CIK. Do not copy prices
    # or class-specific shares from another security.
    if company.cik:
        return company.cik
    if company.market == "US" and (company.regulatory_id_type or "").upper() == "CIK":
        value = company.regulatory_id or ""
        if value.isdigit() and 0 < len(value) <= 10:
            return value
    return None


def _payload_snapshot(db: Session, company: Company, facts_data: dict[str, Any]) -> tuple[RawDocument, str, str]:
    normalized_cik = _normalize_cik(company_sec_cik(company) or "")
    source_url = SEC_COMPANY_FACTS_URL.format(cik=normalized_cik)
    canonical_payload = json.dumps(facts_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload_sha256 = hashlib.sha256(canonical_payload).hexdigest()
    # RawDocument hashes are globally unique, while two listed share classes can
    # legitimately carry the same issuer payload. Keep their evidence ownership
    # separate and continue recognizing pre-v3 snapshot hashes.
    content_hash = f"sec-companyfacts:{company.id}:{payload_sha256}"
    document = db.scalar(
        select(RawDocument).where(
            RawDocument.company_id == company.id,
            RawDocument.content_hash.in_([content_hash, f"sec-companyfacts:{payload_sha256}"]),
        )
    )
    if document is None:
        source = get_or_create_sec_source(db)
        document = RawDocument(
            company_id=company.id,
            source_id=source.id,
            document_type="xbrl_facts",
            title=f"{company.ticker} SEC XBRL Company Facts",
            url=source_url,
            raw_payload_json={
                "provider": "SEC EDGAR",
                "source_url": source_url,
                "retrieved_at": datetime.now(UTC).isoformat(),
                "payload_sha256": payload_sha256,
                "companyfacts": facts_data,
            },
            content_hash=content_hash,
        )
        db.add(document)
        db.flush()
    return document, payload_sha256, source_url


def _candidate_locator(
    *,
    item: dict[str, Any],
    payload_sha256: str,
    source_url: str,
) -> dict[str, Any]:
    observation = item["observation"]
    return {
        "type": "xbrl_fact",
        "namespace": "us-gaap",
        "concept": item["concept"],
        "unit": item["unit"],
        "fiscal_year": item["fiscal_year"],
        "reported_fy": observation.get("fy"),
        "form": observation.get("form"),
        "start": observation.get("start"),
        "end": observation.get("end"),
        "filed": observation.get("filed"),
        "accession": observation.get("accn"),
        "frame": observation.get("frame"),
        "fact_value": observation.get("val"),
        "payload_sha256": payload_sha256,
        "source_url": source_url,
        "selection_policy": "period_end_year_latest_filing_concept_priority",
    }


def extract_xbrl_candidates(
    db: Session,
    company_id: int,
    http_get: Callable[..., Any] | None = None,
    user_agent: str | None = None,
) -> dict[str, Any]:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    cik = company_sec_cik(company)
    if not cik:
        raise HTTPException(status_code=400, detail="Company has no CIK configured")

    facts_data = fetch_company_facts(cik, http_get, user_agent)
    facts = facts_data.get("facts")
    us_gaap_facts = facts.get("us-gaap", {}) if isinstance(facts, dict) else {}
    if not isinstance(us_gaap_facts, dict) or not us_gaap_facts:
        return {
            "fetched_count": 0,
            "created_count": 0,
            "skipped_existing_count": 0,
            "selected_fiscal_years": [],
            "missing_core_metrics_by_year": {},
            "warnings": ["No us-gaap facts found in the SEC response."],
        }

    selected = select_annual_facts(us_gaap_facts, company.currency)
    document, payload_sha256, source_url = _payload_snapshot(db, company, facts_data)
    existing_records = db.scalars(
        select(FinancialExtractionCandidate).where(
            FinancialExtractionCandidate.company_id == company_id,
            FinancialExtractionCandidate.extraction_method.in_(("sec_xbrl_v1", "sec_xbrl_v2", EXTRACTION_METHOD)),
        )
    ).all()
    for record in existing_records:
        if record.extraction_method in {"sec_xbrl_v1", "sec_xbrl_v2"} and record.metric_code == "debt":
            warning = "Legacy SEC mapping contains a long-term debt component, not verified total debt. Review current and noncurrent borrowing components."
            if warning not in (record.extraction_warnings or ""):
                record.extraction_warnings = " ".join(filter(None, [record.extraction_warnings, warning]))
    def identity(metric, year, value, unit, locator):
        return (metric, year, value, unit, *(locator.get(key) for key in
            ("concept", "start", "end", "filed", "accession")))

    existing_keys = {identity(record.metric_code, record.fiscal_year, record.value, record.unit,
        record.source_locator_json or {}) for record in existing_records}

    created_count = 0
    skipped_existing_count = 0
    for key, item in sorted(selected.items(), key=lambda pair: (pair[0][1], pair[0][0])):
        observation = item["observation"]
        locator = _candidate_locator(item=item, payload_sha256=payload_sha256, source_url=source_url)
        fact_key = identity(item["metric_code"], item["fiscal_year"], float(observation["val"]), item["unit"], locator)
        if fact_key in existing_keys:
            skipped_existing_count += 1
            continue
        candidate = FinancialExtractionCandidate(
            company_id=company_id,
            raw_document_id=document.id,
            metric_code=item["metric_code"],
            reported_label=item["concept_label"],
            value=float(observation["val"]),
            unit=item["unit"],
            fiscal_year=item["fiscal_year"],
            period_type="annual",
            source_text=f"XBRL us-gaap:{item['concept']}",
            source_row_label=item["concept_label"],
            source_column_label=f"FY{item['fiscal_year']}",
            source_locator_json=locator,
            extraction_method=EXTRACTION_METHOD,
            confidence_label="high",
            review_status="needs_review",
        )
        db.add(candidate)
        existing_keys.add(fact_key)
        created_count += 1

    if created_count > 0:
        workflow = db.scalar(
            select(CompanySetupWorkflow).where(CompanySetupWorkflow.company_id == company_id)
        )
        if workflow:
            workflow.financial_extraction_status = "needs_review"
            workflow.current_step = "financial_review"

    db.commit()
    selected_fiscal_years = sorted({year for _, year in selected})
    metrics_by_year = {
        year: {metric for metric, metric_year in selected if metric_year == year}
        for year in selected_fiscal_years
    }
    missing_core_metrics_by_year = {
        str(year): sorted(CORE_METRICS - metrics_by_year[year])
        for year in selected_fiscal_years
        if CORE_METRICS - metrics_by_year[year]
    }
    warnings: list[str] = []
    if missing_core_metrics_by_year:
        gap_summary = "; ".join(
            f"FY{year}: {', '.join(metrics)}"
            for year, metrics in missing_core_metrics_by_year.items()
        )
        warnings.append(
            f"Partial SEC facts extracted. Missing critical metrics by fiscal year: {gap_summary}"
        )
    return {
        "fetched_count": len(selected),
        "created_count": created_count,
        "skipped_existing_count": skipped_existing_count,
        "selected_fiscal_years": selected_fiscal_years,
        "missing_core_metrics_by_year": missing_core_metrics_by_year,
        "warnings": warnings,
    }
