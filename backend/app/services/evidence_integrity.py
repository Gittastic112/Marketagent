from datetime import date, datetime, timezone
from hashlib import sha256
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Company,
    DocumentAsset,
    Event,
    EventEvidenceReference,
    FinancialExtractionCandidate,
    FinancialStatementPeriod,
    PeerValuationSet,
    RawDocument,
)
from app.services.financial_history_certification import (
    SUPPORTED_MARKETS,
    _candidate_has_exact_locator,
    assess_history_candidate,
)
from app.services.pdf_page_rendering import validate_pdf_region_against_asset
from app.services.peer_valuation_sets import (
    calculate_peer_diagnostics,
    peer_set_calculation_eligibility,
    peer_set_members,
    peer_set_target_context,
)


MAX_REPORTED_ISSUES = 200


def build_peer_review_receipt_health(
    db: Session,
    *,
    user_id: str,
    limit: int = 50,
    after_id: int = 0,
) -> dict[str, Any]:
    if not 1 <= limit <= 100 or after_id < 0:
        raise ValueError("Invalid receipt-health pagination")
    generated_at = datetime.now(timezone.utc)
    total_owned = db.scalar(select(func.count()).select_from(PeerValuationSet).where(
        PeerValuationSet.user_id == user_id,
    )) or 0
    peer_sets = list(db.scalars(
        select(PeerValuationSet)
        .options(
            selectinload(PeerValuationSet.member_records),
            selectinload(PeerValuationSet.target_profile),
        )
        .where(PeerValuationSet.user_id == user_id, PeerValuationSet.id > after_id)
        .order_by(PeerValuationSet.id)
        .limit(limit + 1)
    ))
    has_more = len(peer_sets) > limit
    peer_sets = peer_sets[:limit]
    active_reviewed = [
        peer_set
        for peer_set in peer_sets
        if peer_set.is_active and peer_set.review_status == "reviewed"
    ]
    attention: list[dict[str, Any]] = []
    ready_count = 0
    missing_count = 0
    stale_count = 0
    storage_blocked_count = 0
    coverage_blocked_count = 0

    for peer_set in active_reviewed:
        diagnostics = calculate_peer_diagnostics(
            peer_set_members(peer_set),
            target_context=peer_set_target_context(peer_set),
            as_of=generated_at.date(),
        )
        eligibility = peer_set_calculation_eligibility(peer_set, diagnostics=diagnostics)
        receipt_status = eligibility["receiptStatus"]
        if receipt_status == "missing":
            missing_count += 1
        elif receipt_status == "stale":
            stale_count += 1
        storage_blocked = any("storage_mismatch" in code for code in eligibility["blockers"])
        coverage_blocked = "insufficient_method_coverage" in eligibility["blockers"]
        storage_blocked_count += int(storage_blocked)
        coverage_blocked_count += int(coverage_blocked)
        if eligibility["canCalculate"]:
            ready_count += 1
            continue
        action = (
            "Repair conflicting peer or target evidence by saving verified source values, then review again."
            if storage_blocked else
            "Supply at least three included positive multiples for one method, then review again."
            if coverage_blocked else
            "Open the peer workspace and acknowledge the current peer diagnostics."
        )

        attention.append(
            {
                "peer_set_id": peer_set.id,
                "company_id": peer_set.company_id,
                "name": peer_set.name,
                "version": peer_set.version,
                "review_status": peer_set.review_status,
                "receipt_status": receipt_status,
                "blockers": eligibility["blockers"],
                "usable_methods": eligibility["usableMethods"],
                "current_diagnostics_as_of": date.fromisoformat(diagnostics["asOf"]),
                "receipt_diagnostics_as_of": peer_set.review_diagnostics_as_of,
                "current_warning_codes": diagnostics["warningCodes"],
                "acknowledged_warning_codes": peer_set.review_warning_codes_json or [],
                "action": action,
            }
        )

    return {
        "status": "attention_required" if attention else "healthy",
        "scope": "page",
        "total_owned_set_count": total_owned,
        "after_id": after_id,
        "limit": limit,
        "has_more": has_more,
        "next_after_id": peer_sets[-1].id if has_more else None,
        "checked_set_count": len(peer_sets),
        "active_reviewed_set_count": len(active_reviewed),
        "ready_for_valuation_count": ready_count,
        "missing_receipt_count": missing_count,
        "stale_receipt_count": stale_count,
        "storage_blocked_count": storage_blocked_count,
        "coverage_blocked_count": coverage_blocked_count,
        "draft_set_count": sum(
            peer_set.is_active and peer_set.review_status == "draft"
            for peer_set in peer_sets
        ),
        "archived_set_count": sum(not peer_set.is_active for peer_set in peer_sets),
        "sets_requiring_attention": attention,
        "generated_at": generated_at,
    }


def build_evidence_integrity_report(
    db: Session,
    *,
    deep_asset_validation: bool = True,
) -> dict[str, Any]:
    documents = {
        row.id: row
        for row in db.execute(
            select(
                RawDocument.id,
                RawDocument.company_id,
                RawDocument.document_type,
                RawDocument.published_at,
                RawDocument.ingested_at,
                RawDocument.raw_text,
            )
        )
    }
    event_companies = dict(db.execute(select(Event.id, Event.company_id)).all())
    asset_columns = [
        DocumentAsset.id,
        DocumentAsset.raw_document_id,
        DocumentAsset.size_bytes,
        DocumentAsset.sha256,
        DocumentAsset.page_count,
    ]
    if deep_asset_validation:
        asset_columns.append(DocumentAsset.content)
    assets = list(db.execute(select(*asset_columns)))
    assets_by_document = {asset.raw_document_id: asset for asset in assets}
    references = list(
        db.execute(
            select(
                EventEvidenceReference.id,
                EventEvidenceReference.event_id,
                EventEvidenceReference.raw_document_id,
                EventEvidenceReference.locator_type,
                EventEvidenceReference.source_page,
                EventEvidenceReference.start_char,
                EventEvidenceReference.end_char,
                EventEvidenceReference.quote,
                EventEvidenceReference.bounding_box_json,
                EventEvidenceReference.confidence_label,
            )
        )
    )
    financial_periods = list(
        db.scalars(
            select(FinancialStatementPeriod).where(
                FinancialStatementPeriod.period_type == "annual"
            )
        )
    )
    financial_periods_by_key: dict[tuple[int, str, int], list[FinancialStatementPeriod]] = {}
    for period in financial_periods:
        financial_periods_by_key.setdefault(
            (period.company_id, period.period_type, period.year), []
        ).append(period)
    promoted_financial_candidates = list(
        db.scalars(
            select(FinancialExtractionCandidate).where(
                FinancialExtractionCandidate.review_status == "promoted"
            )
        )
    )

    issues: list[dict[str, Any]] = []

    def add_issue(
        code: str,
        severity: str,
        entity_type: str,
        entity_id: int,
        message: str,
        action: str,
        *,
        company_id: int | None = None,
        document_id: int | None = None,
        reference_id: int | None = None,
    ) -> None:
        issues.append(
            {
                "code": code,
                "severity": severity,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "message": message,
                "action": action,
                "company_id": company_id,
                "document_id": document_id,
                "reference_id": reference_id,
            }
        )

    for document in documents.values():
        is_retrieval_snapshot = (
            document.document_type == "xbrl_facts"
            and document.ingested_at is not None
        )
        if document.published_at is None and not is_retrieval_snapshot:
            add_issue(
                "DOCUMENT_SOURCE_TIMESTAMP_MISSING",
                "warning",
                "document",
                document.id,
                "The document has no source publication timestamp.",
                "Add or re-ingest the source publication timestamp before relying on freshness.",
                company_id=document.company_id,
                document_id=document.id,
            )

    if deep_asset_validation:
        for asset in assets:
            actual_size = len(asset.content)
            if actual_size != asset.size_bytes:
                add_issue(
                    "ASSET_SIZE_MISMATCH",
                    "error",
                    "asset",
                    asset.id,
                    "Stored asset bytes do not match the recorded size.",
                    "Re-import the original document asset and verify storage integrity.",
                    document_id=asset.raw_document_id,
                )
            actual_hash = sha256(asset.content).hexdigest()
            if actual_hash.lower() != asset.sha256.lower():
                add_issue(
                    "ASSET_HASH_MISMATCH",
                    "error",
                    "asset",
                    asset.id,
                    "Stored asset bytes do not match the recorded SHA-256 digest.",
                    "Quarantine the asset and re-import it from the original source.",
                    document_id=asset.raw_document_id,
                )

    for reference in references:
        document = documents.get(reference.raw_document_id)
        event_company_id = event_companies.get(reference.event_id)
        if document is None:
            add_issue(
                "EVIDENCE_DOCUMENT_MISSING",
                "error",
                "evidence_reference",
                reference.id,
                "The evidence reference points to a missing document.",
                "Remove the orphaned reference or restore the source document.",
                document_id=reference.raw_document_id,
                reference_id=reference.id,
            )
            continue

        if event_company_id and document.company_id and event_company_id != document.company_id:
            add_issue(
                "EVIDENCE_COMPANY_MISMATCH",
                "error",
                "evidence_reference",
                reference.id,
                "The evidence document belongs to a different company than the event.",
                "Relink the event to evidence from the correct company.",
                company_id=event_company_id,
                document_id=document.id,
                reference_id=reference.id,
            )

        if reference.locator_type == "text_span":
            raw_text = document.raw_text
            start = reference.start_char
            end = reference.end_char
            if raw_text is None:
                add_issue(
                    "EVIDENCE_SOURCE_TEXT_MISSING",
                    "error",
                    "evidence_reference",
                    reference.id,
                    "The text-span reference has no stored source text.",
                    "Re-ingest source text or replace the locator with supported evidence.",
                    company_id=document.company_id,
                    document_id=document.id,
                    reference_id=reference.id,
                )
            elif start is None or end is None or start < 0 or end <= start or end > len(raw_text):
                add_issue(
                    "EVIDENCE_SPAN_INVALID",
                    "error",
                    "evidence_reference",
                    reference.id,
                    "The text-span coordinates are outside the stored source text.",
                    "Recreate the locator against the current stored document.",
                    company_id=document.company_id,
                    document_id=document.id,
                    reference_id=reference.id,
                )
            elif raw_text[start:end] != reference.quote:
                add_issue(
                    "EVIDENCE_QUOTE_MISMATCH",
                    "error",
                    "evidence_reference",
                    reference.id,
                    "The saved quote no longer matches its stored text span.",
                    "Revalidate the source document and recreate the exact locator.",
                    company_id=document.company_id,
                    document_id=document.id,
                    reference_id=reference.id,
                )

        if reference.locator_type == "pdf_region":
            asset = assets_by_document.get(document.id)
            if asset is None:
                add_issue(
                    "EVIDENCE_PDF_ASSET_MISSING",
                    "error",
                    "evidence_reference",
                    reference.id,
                    "The PDF-region reference has no stored PDF asset.",
                    "Re-import the source PDF or replace the unsupported locator.",
                    company_id=document.company_id,
                    document_id=document.id,
                    reference_id=reference.id,
                )
            elif reference.source_page is None or reference.source_page > asset.page_count:
                add_issue(
                    "EVIDENCE_PDF_PAGE_INVALID",
                    "error",
                    "evidence_reference",
                    reference.id,
                    "The referenced PDF page is outside the stored page range.",
                    "Recreate the locator against the stored PDF asset.",
                    company_id=document.company_id,
                    document_id=document.id,
                    reference_id=reference.id,
                )
            if not reference.bounding_box_json:
                add_issue(
                    "EVIDENCE_PDF_BOUNDS_MISSING",
                    "warning",
                    "evidence_reference",
                    reference.id,
                    "The PDF-region reference has no bounding coordinates.",
                    "Capture the exact region before treating the reference as high precision.",
                    company_id=document.company_id,
                    document_id=document.id,
                    reference_id=reference.id,
                )
            elif (
                deep_asset_validation
                and asset is not None
                and reference.source_page is not None
                and reference.source_page <= asset.page_count
            ):
                try:
                    validate_pdf_region_against_asset(
                        reference.bounding_box_json,
                        source_page=reference.source_page,
                        content=asset.content,
                    )
                except (IndexError, ValueError) as exc:
                    add_issue(
                        "EVIDENCE_PDF_BOUNDS_INVALID",
                        "error",
                        "evidence_reference",
                        reference.id,
                        f"The PDF-region geometry is not reproducible: {exc}",
                        "Recreate the exact region against the stored PDF asset.",
                        company_id=document.company_id,
                        document_id=document.id,
                        reference_id=reference.id,
                    )

        if reference.confidence_label == "low":
            add_issue(
                "EVIDENCE_CONFIDENCE_LOW",
                "warning",
                "evidence_reference",
                reference.id,
                "The evidence locator is explicitly marked low confidence.",
                "Review the locator and source before using it for a material conclusion.",
                company_id=document.company_id,
                document_id=document.id,
                reference_id=reference.id,
            )

    promoted_documents_by_company: dict[int, set[int]] = {}
    exact_financial_candidate_ids: set[int] = set()
    for candidate in promoted_financial_candidates:
        promoted_documents_by_company.setdefault(candidate.company_id, set()).add(
            candidate.raw_document_id
        )
        if not _candidate_has_exact_locator(candidate):
            add_issue(
                "FINANCIAL_EVIDENCE_LOCATOR_INEXACT",
                "error",
                "financial_candidate",
                candidate.id,
                "The promoted financial fact cannot be reproduced from an exact source locator.",
                "Return the fact to review and attach a verifiable XBRL fact, PDF page, cell, or text span.",
                company_id=candidate.company_id,
                document_id=candidate.raw_document_id,
            )
        else:
            exact_financial_candidate_ids.add(candidate.id)

        if candidate.source_page is not None:
            asset = assets_by_document.get(candidate.raw_document_id)
            if asset is None:
                add_issue(
                    "FINANCIAL_PDF_ASSET_MISSING",
                    "error",
                    "financial_candidate",
                    candidate.id,
                    "The promoted page-located financial fact has no stored PDF asset.",
                    "Restore the source PDF or return the fact to review.",
                    company_id=candidate.company_id,
                    document_id=candidate.raw_document_id,
                )
            elif candidate.source_page < 1 or candidate.source_page > asset.page_count:
                add_issue(
                    "FINANCIAL_PDF_PAGE_INVALID",
                    "error",
                    "financial_candidate",
                    candidate.id,
                    "The promoted financial fact points outside the stored PDF page range.",
                    "Recreate the locator against the stored source PDF.",
                    company_id=candidate.company_id,
                    document_id=candidate.raw_document_id,
                )

        if candidate.fiscal_year is None:
            add_issue(
                "FINANCIAL_FISCAL_YEAR_MISSING",
                "error",
                "financial_candidate",
                candidate.id,
                "The promoted financial fact has no fiscal year.",
                "Return the fact to review and assign its audited fiscal period.",
                company_id=candidate.company_id,
                document_id=candidate.raw_document_id,
            )
            continue

        matching_periods = financial_periods_by_key.get(
            (candidate.company_id, candidate.period_type, candidate.fiscal_year), []
        )
        if len(matching_periods) != 1:
            add_issue(
                "FINANCIAL_PERIOD_NOT_UNIQUE",
                "error",
                "financial_candidate",
                candidate.id,
                "The promoted financial fact does not resolve to exactly one stored fiscal period.",
                "Create or reconcile the annual fiscal period before using this fact in valuation.",
                company_id=candidate.company_id,
                document_id=candidate.raw_document_id,
            )
            continue

        locator_end = (candidate.source_locator_json or {}).get("end")
        if not locator_end:
            add_issue(
                "FINANCIAL_PERIOD_END_UNVERIFIED",
                "warning",
                "financial_candidate",
                candidate.id,
                "The promoted financial locator does not state its fiscal period end date.",
                "Add the source period end to the locator and re-review the fact.",
                company_id=candidate.company_id,
                document_id=candidate.raw_document_id,
            )
            continue
        try:
            locator_end_date = date.fromisoformat(str(locator_end))
        except ValueError:
            add_issue(
                "FINANCIAL_PERIOD_END_INVALID",
                "error",
                "financial_candidate",
                candidate.id,
                "The promoted financial locator has an invalid fiscal period end date.",
                "Replace the locator end with an ISO date from the primary source.",
                company_id=candidate.company_id,
                document_id=candidate.raw_document_id,
            )
            continue
        if locator_end_date != matching_periods[0].report_date:
            add_issue(
                "FINANCIAL_PERIOD_END_MISMATCH",
                "error",
                "financial_candidate",
                candidate.id,
                "The promoted source period end does not match the stored financial period.",
                "Reconcile the source locator and financial period before valuation autofill.",
                company_id=candidate.company_id,
                document_id=candidate.raw_document_id,
            )

    certification_results: list[dict[str, Any]] = []
    for company_id, document_ids in sorted(promoted_documents_by_company.items()):
        company = db.get(Company, company_id)
        if company is None:
            continue
        result = assess_history_candidate(
            db,
            {
                "label": company.ticker,
                "company_id": company.id,
                "market": company.market,
                "source_document_ids": sorted(document_ids),
                "is_mock": False,
                "source_assertion": "real_primary_source",
            },
            accepted_review_statuses=("promoted",),
            prevalidated_exact_candidate_ids=exact_financial_candidate_ids,
        )
        certification_results.append(result)
        if result["statement_identity_status"] == "failed":
            add_issue(
                "FINANCIAL_STATEMENT_IDENTITY_FAILED",
                "warning",
                "financial_history",
                company.id,
                f"{company.ticker} has source financial facts that fail an accounting identity.",
                "Reconcile the failed identity and its exact source facts before valuation use.",
                company_id=company.id,
            )
        if not result["eligible_for_certification"]:
            add_issue(
                "FINANCIAL_HISTORY_NOT_CERTIFIABLE",
                "warning",
                "financial_history",
                company.id,
                f"{company.ticker} has promoted facts but does not pass the real-source history gate.",
                "Resolve: " + ", ".join(result.get("failures", [])),
                company_id=company.id,
            )

    eligible_histories = [
        item for item in certification_results if item["eligible_for_certification"]
    ]
    certified_markets = sorted({item["market"] for item in eligible_histories})
    if not certification_results:
        financial_certification_status = "not_available"
    elif set(certified_markets) == SUPPORTED_MARKETS:
        financial_certification_status = "passed"
    elif eligible_histories:
        financial_certification_status = "partial"
    else:
        financial_certification_status = "blocked"
    if certification_results and set(certified_markets) != SUPPORTED_MARKETS:
        missing_markets = sorted(SUPPORTED_MARKETS - set(certified_markets))
        add_issue(
            "FINANCIAL_CERTIFICATION_MARKET_GAP",
            "warning",
            "financial_history",
            0,
            "Real-source financial certification does not cover every required market.",
            "Add an eligible promoted history for: " + ", ".join(missing_markets),
        )

    issues.sort(key=lambda issue: (issue["severity"] != "error", issue["code"], issue["entity_id"]))
    error_count = sum(issue["severity"] == "error" for issue in issues)
    warning_count = len(issues) - error_count
    reported_issues = issues[:MAX_REPORTED_ISSUES]
    checked_at = datetime.now(timezone.utc)
    limitations = (
        []
        if deep_asset_validation
        else [
            "Asset byte/hash verification and PDF-region geometry checks were not run in metadata scope."
        ]
    )
    return {
        "status": "issues_found" if issues else "healthy",
        "verification_scope": "deep" if deep_asset_validation else "metadata",
        "asset_content_verification_status": "checked" if deep_asset_validation else "not_run",
        "limitations": limitations,
        "checked_documents": len(documents),
        "checked_assets": len(assets),
        "checked_references": len(references),
        "checked_financial_candidates": len(promoted_financial_candidates),
        "checked_financial_periods": len(financial_periods),
        "financial_history_candidate_count": len(certification_results),
        "certified_financial_history_count": len(eligible_histories),
        "certified_markets": certified_markets,
        "financial_certification_status": financial_certification_status,
        "financial_histories": certification_results,
        "error_count": error_count,
        "warning_count": warning_count,
        "reported_issue_count": len(reported_issues),
        "is_truncated": len(reported_issues) < len(issues),
        "checked_at": checked_at,
        "issues": reported_issues,
    }
