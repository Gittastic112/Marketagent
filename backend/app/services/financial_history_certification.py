from __future__ import annotations

import math
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, DocumentAsset, FinancialExtractionCandidate, FinancialStatementPeriod, RawDocument
from app.services.accounting_normalization import (
    FinancialReconciliationService,
    NormalizedSnapshotBackfillService,
)
from app.services.financial_statement_identity import FinancialStatementIdentityService


SUPPORTED_MARKETS = {"US", "IN"}
REQUIRED_CORE_METRICS = {
    "revenue",
    "ebit",
    "net_income",
    "cash",
    "debt",
    "diluted_shares",
}
NON_PRODUCTION_MARKERS = {"mock", "fixture", "synthetic", "test data", "demo data"}


def resolve_certification_manifest(db: Session, manifest: dict[str, Any]) -> dict[str, Any]:
    """Resolve portable company/source selectors into the strict ID manifest."""
    candidates = manifest.get("candidates") if isinstance(manifest, dict) else None
    if not isinstance(candidates, list):
        raise ValueError("Certification manifest must contain a candidates list")

    resolved: list[dict[str, Any]] = []
    for item in candidates:
        if not isinstance(item, dict):
            raise ValueError("Certification manifest candidates must be objects")
        if isinstance(item.get("company_id"), int) and isinstance(item.get("source_document_ids"), list):
            resolved.append(dict(item))
            continue

        selector = item.get("company_selector")
        source_selectors = item.get("source_selectors")
        if not isinstance(selector, dict) or not isinstance(source_selectors, list) or not source_selectors:
            raise ValueError("Portable candidates require company_selector and source_selectors")
        query = select(Company).where(
            Company.market == str(selector.get("market") or "").upper(),
            Company.local_symbol == str(selector.get("local_symbol") or "").upper(),
        )
        if selector.get("primary_exchange"):
            query = query.where(Company.primary_exchange == str(selector["primary_exchange"]).upper())
        if selector.get("regulatory_id"):
            query = query.where(Company.regulatory_id == str(selector["regulatory_id"]))
        companies = list(db.scalars(query))
        if len(companies) != 1:
            raise ValueError(f"Company selector must resolve exactly once: {selector}")
        company = companies[0]

        document_ids: list[int] = []
        for source_selector in source_selectors:
            if not isinstance(source_selector, dict):
                raise ValueError("Source selectors must be objects")
            documents: list[RawDocument]
            if source_selector.get("asset_sha256"):
                documents = list(
                    db.scalars(
                        select(RawDocument)
                        .join(DocumentAsset, DocumentAsset.raw_document_id == RawDocument.id)
                        .where(
                            RawDocument.company_id == company.id,
                            DocumentAsset.sha256 == source_selector["asset_sha256"],
                        )
                    )
                )
            elif source_selector.get("url") and source_selector.get("payload_sha256"):
                documents = list(
                    db.scalars(
                        select(RawDocument).where(
                            RawDocument.company_id == company.id,
                            RawDocument.url == source_selector["url"],
                        )
                    )
                )
                documents = [
                    document
                    for document in documents
                    if (document.raw_payload_json or {}).get("payload_sha256")
                    == source_selector["payload_sha256"]
                ]
            else:
                raise ValueError("Source selector requires asset_sha256 or URL plus payload_sha256")
            if len(documents) != 1:
                raise ValueError(f"Source selector must resolve exactly once: {source_selector}")
            document_ids.append(documents[0].id)

        resolved.append(
            {
                key: value
                for key, value in item.items()
                if key not in {"company_selector", "source_selectors"}
            }
            | {
                "company_id": company.id,
                "market": company.market,
                "source_document_ids": sorted(set(document_ids)),
            }
        )
    return {**manifest, "candidates": resolved}


def _has_non_production_marker(*values: str | None) -> bool:
    text = " ".join(value or "" for value in values).lower()
    return any(marker in text for marker in NON_PRODUCTION_MARKERS)


def _xbrl_locator_matches_payload(
    candidate: FinancialExtractionCandidate,
    locator: dict[str, Any],
) -> bool:
    required = ("namespace", "concept", "unit", "end", "filed", "accession", "form", "payload_sha256", "source_url")
    if any(not locator.get(field) for field in required):
        return False
    document = candidate.raw_document
    payload = document.raw_payload_json or {}
    if payload.get("payload_sha256") != locator["payload_sha256"]:
        return False
    if document.url != locator["source_url"]:
        return False
    companyfacts = payload.get("companyfacts")
    if not isinstance(companyfacts, dict):
        return False
    observations = (
        companyfacts.get("facts", {})
        .get(locator["namespace"], {})
        .get(locator["concept"], {})
        .get("units", {})
        .get(locator["unit"], [])
    )
    for observation in observations:
        if not isinstance(observation, dict):
            continue
        if any(
            observation.get(observation_key) != locator.get(locator_key)
            for locator_key, observation_key in (
                ("start", "start"),
                ("end", "end"),
                ("filed", "filed"),
                ("accession", "accn"),
                ("form", "form"),
            )
        ):
            continue
        try:
            return math.isclose(float(observation["val"]), float(candidate.value), rel_tol=0, abs_tol=1e-9)
        except (KeyError, TypeError, ValueError):
            return False
    return False


def _candidate_has_exact_locator(candidate: FinancialExtractionCandidate) -> bool:
    if candidate.source_page is not None:
        return True
    locator = candidate.source_locator_json or {}
    if locator.get("type") == "xbrl_fact":
        return _xbrl_locator_matches_payload(candidate, locator)
    if locator.get("cell_reference") or locator.get("bounding_box"):
        return True
    raw_text = candidate.raw_document.raw_text or ""
    return bool(candidate.source_text and candidate.source_text in raw_text)


def assess_history_candidate(
    db: Session,
    candidate: dict[str, Any],
    *,
    accepted_review_statuses: tuple[str, ...] = ("reviewed", "overridden", "promoted"),
    prevalidated_exact_candidate_ids: set[int] | None = None,
) -> dict[str, Any]:
    failures: list[str] = []
    company_id = candidate.get("company_id")
    market = str(candidate.get("market") or "").upper()
    document_ids = {int(item) for item in candidate.get("source_document_ids", [])}
    company = db.get(Company, company_id) if isinstance(company_id, int) else None

    if candidate.get("is_mock") is not False:
        failures.append("manifest_must_explicitly_set_is_mock_false")
    if candidate.get("source_assertion") != "real_primary_source":
        failures.append("source_assertion_must_be_real_primary_source")
    if market not in SUPPORTED_MARKETS:
        failures.append("market_must_be_US_or_IN")
    if company is None:
        failures.append("company_not_found")
        return {
            "label": candidate.get("label"),
            "company_id": company_id,
            "market": market,
            "eligible_for_certification": False,
            "failures": failures,
            "limitations": [],
            "statement_identity_status": "not_available",
            "statement_identity_check_count": 0,
            "statement_identity_failed_count": 0,
        }
    if company.market.upper() != market:
        failures.append("company_market_does_not_match_manifest")
    if _has_non_production_marker(company.ticker, company.name):
        failures.append("company_identity_contains_non_production_marker")

    documents = list(
        db.scalars(
            select(RawDocument).where(
                RawDocument.id.in_(document_ids),
                RawDocument.company_id == company.id,
            )
        )
    ) if document_ids else []
    if not document_ids:
        failures.append("source_documents_are_required")
    elif {document.id for document in documents} != document_ids:
        failures.append("source_document_missing_or_linked_to_another_company")
    if any(
        _has_non_production_marker(
            document.title,
            document.document_type,
            document.source.name if document.source else None,
            document.source.source_type if document.source else None,
        )
        for document in documents
    ):
        failures.append("source_contains_non_production_marker")

    periods = list(
        db.scalars(
            select(FinancialStatementPeriod)
            .where(
                FinancialStatementPeriod.company_id == company.id,
                FinancialStatementPeriod.period_type == "annual",
            )
            .order_by(FinancialStatementPeriod.year)
        )
    )
    if len(periods) < 3:
        failures.append("at_least_three_annual_periods_are_required")

    coverage = NormalizedSnapshotBackfillService.summarize(db, company.id)
    if coverage["status"] != "complete" or coverage["trust_ready_period_count"] != coverage["period_count"]:
        failures.append("normalized_history_is_not_trust_ready")
    reconciliation = FinancialReconciliationService.reconcile(db, company.id)
    if reconciliation["status"] != "complete":
        failures.append("financial_reconciliation_is_not_complete")
    statement_identities = FinancialStatementIdentityService.evaluate_company(db, company.id)
    if statement_identities["status"] == "failed":
        failures.append("financial_statement_identity_failed")
    limitations: list[str] = []
    if statement_identities["status"] == "not_available":
        limitations.append(
            "No annual financial-statement identity can be evaluated from the promoted fact set."
        )
    elif statement_identities["status"] == "partial":
        limitations.append(
            "Only part of the annual history has enough facts for financial-statement identity checks."
        )

    reviewed_candidates = list(
        db.scalars(
            select(FinancialExtractionCandidate).where(
                FinancialExtractionCandidate.company_id == company.id,
                FinancialExtractionCandidate.raw_document_id.in_(document_ids or {-1}),
                FinancialExtractionCandidate.review_status.in_(accepted_review_statuses),
            )
        )
    )
    evidence_by_year: dict[int, set[str]] = {}
    locator_failures = 0
    for item in reviewed_candidates:
        if item.fiscal_year is None:
            continue
        has_exact_locator = (
            item.id in prevalidated_exact_candidate_ids
            if prevalidated_exact_candidate_ids is not None
            else _candidate_has_exact_locator(item)
        )
        if not has_exact_locator:
            locator_failures += 1
            continue
        evidence_by_year.setdefault(item.fiscal_year, set()).add(item.metric_code)
    uncovered = {
        period.year: sorted(REQUIRED_CORE_METRICS - evidence_by_year.get(period.year, set()))
        for period in periods
        if REQUIRED_CORE_METRICS - evidence_by_year.get(period.year, set())
    }
    if uncovered:
        failures.append("core_financial_metrics_lack_reviewed_exact_evidence")
    if locator_failures:
        failures.append("reviewed_candidates_have_inexact_locators")

    return {
        "label": candidate.get("label"),
        "company_id": company.id,
        "company": company.name,
        "market": market,
        "eligible_for_certification": not failures,
        "failures": failures,
        "limitations": limitations,
        "period_count": len(periods),
        "source_document_count": len(documents),
        "reviewed_evidence_count": sum(len(items) for items in evidence_by_year.values()),
        "uncovered_core_metrics_by_year": uncovered,
        "coverage_status": coverage["status"],
        "reconciliation_status": reconciliation["status"],
        "statement_identity_status": statement_identities["status"],
        "statement_identity_check_count": statement_identities["applicable_check_count"],
        "statement_identity_failed_count": statement_identities["failed_check_count"],
    }


def build_certification_report(db: Session, manifest: dict[str, Any]) -> dict[str, Any]:
    candidates = manifest.get("candidates") if isinstance(manifest, dict) else None
    if not isinstance(candidates, list):
        raise ValueError("Certification manifest must contain a candidates list")
    results = [assess_history_candidate(db, item) for item in candidates]
    certified = sum(item["eligible_for_certification"] for item in results)
    represented_markets = {
        item["market"] for item in results if item["eligible_for_certification"]
    }
    limitations = (
        []
        if represented_markets == SUPPORTED_MARKETS
        else ["At least one eligible real-source history is required for both US and IN."]
    )
    limitations.extend(
        f"{item.get('label')}: {limitation}"
        for item in results
        for limitation in item.get("limitations", [])
    )
    return {
        "report_version": "financial-history-certification-v2",
        "status": "passed" if represented_markets == SUPPORTED_MARKETS else "blocked",
        "certified_count": certified,
        "required_markets": sorted(SUPPORTED_MARKETS),
        "certified_markets": sorted(represented_markets),
        "limitations": limitations,
        "candidates": results,
    }
