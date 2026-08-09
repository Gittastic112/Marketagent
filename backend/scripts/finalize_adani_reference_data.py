from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from io import BytesIO

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import (
    Company,
    CompanySetupWorkflow,
    DocumentAsset,
    FinancialExtractionCandidate,
    FinancialStatementPeriod,
    RawDocument,
    SourceFactRevision,
    ValuationSetupDraft,
)
from app.services.accounting_normalization import (
    FinancialReconciliationService,
    NormalizedSnapshotBackfillService,
)
from app.services.financial_extraction import promote_reviewed_candidates
from app.services.financial_history_certification import build_certification_report
from app.services.industry_mapping import IndustryMappingService
from app.services.processing_runs import complete_processing_run, fail_processing_run, start_processing_run
from app.services.valuation_setup_draft import ValuationSetupDraftService


LOCAL_SYMBOL = "ADANIPORTS"
VALUATION_USER_ID = "local-user"
APPROVAL_DATE = date(2026, 8, 1)
EXPECTED_DOCUMENT_SHA256 = {
    3: "2ec4e75290acf3845677ab4a2efd64869d5c9ea5c472a3f0421d9d1611527262",
    4: "7f4ff812ea46d1d1c091e58f2161719285fee9ad39ea5e29c3b4beca13aea03f",
}
EXPECTED_SOURCE_DOCUMENT_BY_YEAR = {2023: 4, 2024: 3, 2025: 3}
EXPECTED_VALUES = {
    2023: {
        "book_equity": 45555.92,
        "cash": 1121.11,
        "debt": 50518.43,
        "depreciation": 3424.71,
        "diluted_shares": 2160138945,
        "finance_costs": 2593.62,
        "investments_in_associates": 2498.38,
        "lease_liabilities": 2749.26,
        "minority_interests": 1361.06,
        "net_income": 5390.85,
        "net_income_nci": 82.0,
        "net_income_parent": 5308.85,
        "pre_tax_income": 5486.89,
        "revenue": 20851.91,
        "tax_expense": 96.04,
        "total_assets": 114763.09,
    },
    2024: {
        "book_equity": 52944.77,
        "cash": 1575.73,
        "debt": 46279.23,
        "depreciation": 3888.46,
        "diluted_shares": 2160138945,
        "finance_costs": 2784.41,
        "investments_in_associates": 2707.26,
        "lease_liabilities": 3024.48,
        "minority_interests": 1598.23,
        "net_income": 8103.99,
        "net_income_nci": -6.65,
        "net_income_parent": 8110.64,
        "pre_tax_income": 10093.73,
        "revenue": 26710.56,
        "tax_expense": 1989.74,
        "total_assets": 118917.87,
    },
    2025: {
        "book_equity": 62435.39,
        "cash": 3406.32,
        "debt": 45810.03,
        "depreciation": 4378.93,
        "diluted_shares": 2160138945,
        "finance_costs": 2778.0,
        "investments_in_associates": 3082.64,
        "lease_liabilities": 5644.17,
        "minority_interests": 2537.95,
        "net_income": 11061.26,
        "net_income_nci": -31.05,
        "net_income_parent": 11092.31,
        "pre_tax_income": 13029.62,
        "revenue": 30475.33,
        "tax_expense": 1968.36,
        "total_assets": 135332.23,
    },
}


@dataclass(frozen=True)
class EbitReconstruction:
    fiscal_year: int
    raw_document_id: int
    source_page: int
    revenue_from_operations: float
    operating_expenses: float
    employee_benefits: float
    depreciation_and_amortisation: float
    other_expenses: float

    @property
    def value(self) -> float:
        return round(
            self.revenue_from_operations
            - self.operating_expenses
            - self.employee_benefits
            - self.depreciation_and_amortisation
            - self.other_expenses,
            2,
        )

    @property
    def period_end(self) -> date:
        return date(self.fiscal_year, 3, 31)

    @property
    def formula(self) -> str:
        return (
            f"{self.revenue_from_operations:.2f} - {self.operating_expenses:.2f} - "
            f"{self.employee_benefits:.2f} - {self.depreciation_and_amortisation:.2f} - "
            f"{self.other_expenses:.2f} = {self.value:.2f}"
        )

    @property
    def components(self) -> tuple[tuple[str, float], ...]:
        return (
            ("Revenue from Operations", self.revenue_from_operations),
            ("Operating Expenses", self.operating_expenses),
            ("Employee Benefits Expense", self.employee_benefits),
            ("Depreciation and Amortisation Expense", self.depreciation_and_amortisation),
            ("Other Expenses", self.other_expenses),
        )


EBIT_RECONSTRUCTIONS = {
    2023: EbitReconstruction(2023, 4, 439, 20851.91, 5654.56, 1178.17, 3424.71, 1185.73),
    2024: EbitReconstruction(2024, 3, 466, 26710.56, 7116.34, 1896.40, 3888.46, 1833.90),
    2025: EbitReconstruction(2025, 3, 466, 30475.33, 8069.75, 2008.66, 4378.93, 1975.55),
}


def _company(db) -> Company:
    company = db.scalar(
        select(Company).where(
            Company.market == "IN",
            Company.primary_exchange == "NSE",
            Company.local_symbol == LOCAL_SYMBOL,
        )
    )
    if company is None:
        raise ValueError("The staged NSE ADANIPORTS company was not found")
    return company


def _documents(db, company_id: int) -> dict[int, RawDocument]:
    documents = {
        document.id: document
        for document in db.scalars(
            select(RawDocument).where(
                RawDocument.company_id == company_id,
                RawDocument.id.in_(EXPECTED_DOCUMENT_SHA256),
            )
        )
    }
    if set(documents) != set(EXPECTED_DOCUMENT_SHA256):
        raise ValueError("The approved APSEZ annual-report documents are not present")
    for document_id, expected_sha256 in EXPECTED_DOCUMENT_SHA256.items():
        asset = documents[document_id].asset
        if asset is None or asset.sha256 != expected_sha256:
            raise ValueError(f"APSEZ document {document_id} does not match its approved SHA-256")
    return documents


def _repair_asset_page_counts(db, documents: dict[int, RawDocument]) -> int:
    import pdfplumber

    correction_count = 0
    for document in documents.values():
        asset = document.asset
        if asset is None:
            raise ValueError(f"APSEZ document {document.id} has no stored asset")
        with pdfplumber.open(BytesIO(asset.content)) as pdf:
            actual_page_count = len(pdf.pages)
        if actual_page_count < 1:
            raise ValueError(f"APSEZ document {document.id} has no physical PDF pages")
        max_locator_page = db.scalar(
            select(FinancialExtractionCandidate.source_page)
            .where(
                FinancialExtractionCandidate.raw_document_id == document.id,
                FinancialExtractionCandidate.source_page.is_not(None),
            )
            .order_by(FinancialExtractionCandidate.source_page.desc())
            .limit(1)
        )
        if max_locator_page and max_locator_page > actual_page_count:
            raise ValueError(
                f"APSEZ document {document.id} locator page {max_locator_page} "
                f"exceeds physical page count {actual_page_count}"
            )
        if asset.page_count != actual_page_count:
            asset.page_count = actual_page_count
            correction_count += 1
        payload = dict(document.raw_payload_json or {})
        payload["page_count"] = actual_page_count
        scanned_pages = payload.get("scanned_pages")
        if isinstance(scanned_pages, list):
            payload["extraction_scope"] = (
                "targeted_pages" if len(scanned_pages) < actual_page_count else "full_document"
            )
        document.raw_payload_json = payload
    return correction_count


def _approved_candidates(db, company_id: int) -> list[FinancialExtractionCandidate]:
    candidates = list(
        db.scalars(
            select(FinancialExtractionCandidate).where(
                FinancialExtractionCandidate.company_id == company_id,
                FinancialExtractionCandidate.raw_document_id.in_(EXPECTED_DOCUMENT_SHA256),
                FinancialExtractionCandidate.fiscal_year.in_(EXPECTED_VALUES),
                FinancialExtractionCandidate.period_type == "annual",
                FinancialExtractionCandidate.metric_code != "ebit",
            )
        )
    )
    keyed = {(candidate.fiscal_year, candidate.metric_code): candidate for candidate in candidates}
    expected_keys = {
        (year, metric_code)
        for year, metrics in EXPECTED_VALUES.items()
        for metric_code in metrics
    }
    if len(candidates) != len(keyed) or set(keyed) != expected_keys:
        missing = sorted(expected_keys - set(keyed))
        unexpected = sorted(set(keyed) - expected_keys)
        raise ValueError(f"Approved APSEZ candidate set mismatch; missing={missing}, unexpected={unexpected}")

    for (year, metric_code), expected_value in (
        (key, EXPECTED_VALUES[key[0]][key[1]]) for key in sorted(expected_keys)
    ):
        candidate = keyed[(year, metric_code)]
        if candidate.raw_document_id != EXPECTED_SOURCE_DOCUMENT_BY_YEAR[year]:
            raise ValueError(f"{year} {metric_code} is linked to an unexpected source document")
        if not math.isclose(candidate.value, expected_value, rel_tol=0, abs_tol=1e-6):
            raise ValueError(
                f"{year} {metric_code} differs from the approved value: "
                f"expected {expected_value}, found {candidate.value}"
            )
        expected_unit = "shares" if metric_code == "diluted_shares" else "INR crore"
        if candidate.unit != expected_unit or candidate.source_page is None:
            raise ValueError(f"{year} {metric_code} lacks the approved unit or exact PDF page")
        if candidate.review_status not in {"needs_review", "reviewed", "overridden", "promoted"}:
            raise ValueError(f"{year} {metric_code} has unsupported review status {candidate.review_status}")
    return candidates


def _set_period_end(candidate: FinancialExtractionCandidate) -> None:
    locator = dict(candidate.source_locator_json or {})
    locator["end"] = date(candidate.fiscal_year, 3, 31).isoformat()
    candidate.source_locator_json = locator


def _ebit_locator(item: EbitReconstruction) -> dict[str, object]:
    return {
        "type": "pdf_formula",
        "claim_type": "Calculation",
        "page": item.source_page,
        "end": item.period_end.isoformat(),
        "fiscal_year": item.fiscal_year,
        "formula": item.formula,
        "methodology": "revenue_less_operating_employee_depreciation_and_other_expenses",
        "components": [
            {"label": label, "value": value}
            for label, value in item.components
        ],
        "excluded": [
            "other income",
            "finance costs and finance-related gains/losses",
            "share of profit or loss from associates and joint ventures",
            "exceptional items",
            "gain on sale of equity stake included in FY2025 total income",
        ],
    }


def _pdf_page_text(raw_text: str, page_number: int) -> str:
    match = re.search(
        rf"(?:^|\n)\[Page {page_number}\]\n(?P<page>.*?)(?=\n\[Page \d+\]\n|\Z)",
        raw_text,
        flags=re.DOTALL,
    )
    if match is None:
        raise ValueError(f"Stored PDF text does not contain page {page_number}")
    return match.group("page")


def _assert_ebit_components_on_page(raw_text: str, item: EbitReconstruction) -> None:
    lines = [line.strip() for line in _pdf_page_text(raw_text, item.source_page).splitlines()]
    for label, value in item.components:
        value_token = f"{value:,.2f}"
        if not any(label.casefold() in line.casefold() and value_token in line for line in lines):
            raise ValueError(
                f"FY{item.fiscal_year} EBIT component {label!r}={value_token} "
                f"is not present on PDF page {item.source_page}"
            )


def _ensure_ebit_candidates(
    db,
    company_id: int,
    documents: dict[int, RawDocument],
) -> tuple[list[FinancialExtractionCandidate], int]:
    existing = {
        candidate.fiscal_year: candidate
        for candidate in db.scalars(
            select(FinancialExtractionCandidate).where(
                FinancialExtractionCandidate.company_id == company_id,
                FinancialExtractionCandidate.metric_code == "ebit",
                FinancialExtractionCandidate.period_type == "annual",
                FinancialExtractionCandidate.fiscal_year.in_(EBIT_RECONSTRUCTIONS),
            )
        )
    }
    if len(existing) not in {0, 3}:
        raise ValueError("APSEZ has a partial or duplicate EBIT candidate set")

    created_count = 0
    result: list[FinancialExtractionCandidate] = []
    for year, item in EBIT_RECONSTRUCTIONS.items():
        candidate = existing.get(year)
        document = documents[item.raw_document_id]
        if not document.raw_text:
            raise ValueError(f"FY{year} source PDF has no stored text")
        _assert_ebit_components_on_page(document.raw_text, item)
        if candidate is None:
            candidate = FinancialExtractionCandidate(
                company_id=company_id,
                raw_document_id=item.raw_document_id,
                metric_code="ebit",
                reported_label="Operating EBIT (reconstructed)",
                value=item.value,
                unit="INR crore",
                fiscal_year=year,
                period_type="annual",
                source_text=f"Operating EBIT calculation: {item.formula}",
                source_page=item.source_page,
                source_section="Consolidated Statement of Profit and Loss",
                source_table_name="Consolidated Statement of Profit and Loss",
                source_row_label="Revenue less operating, employee, depreciation, and other expenses",
                source_column_label=f"FY{year}",
                source_cell_reference=f"P{item.source_page}:CALC:EBIT:{year}",
                source_locator_json=_ebit_locator(item),
                extraction_warnings=(
                    "calculated_metric; excludes non-operating income, finance items, "
                    "equity-accounted results, and exceptional items"
                ),
                extraction_method="reviewed_pdf_formula_v1",
                confidence_label="high",
                review_status="reviewed",
            )
            db.add(candidate)
            created_count += 1
        else:
            if (
                candidate.raw_document_id != item.raw_document_id
                or not math.isclose(candidate.value, item.value, rel_tol=0, abs_tol=1e-6)
                or candidate.unit != "INR crore"
                or candidate.source_page != item.source_page
                or candidate.review_status not in {"reviewed", "promoted"}
            ):
                raise ValueError(f"Existing FY{year} EBIT candidate does not match the approved calculation")
            candidate.source_locator_json = _ebit_locator(item)
        result.append(candidate)
    db.flush()
    return result, created_count


def _assert_no_unexpected_promotable_candidates(
    db,
    company_id: int,
    approved: list[FinancialExtractionCandidate],
) -> None:
    approved_ids = {candidate.id for candidate in approved}
    promotable_ids = set(
        db.scalars(
            select(FinancialExtractionCandidate.id).where(
                FinancialExtractionCandidate.company_id == company_id,
                FinancialExtractionCandidate.review_status.in_(("reviewed", "overridden")),
            )
        )
    )
    unexpected = sorted(promotable_ids - approved_ids)
    if unexpected:
        raise ValueError(f"Unexpected reviewed APSEZ candidates would be promoted: {unexpected}")


def _correct_fiscal_dates(db, company_id: int, candidates: list[FinancialExtractionCandidate]) -> int:
    periods = list(
        db.scalars(
            select(FinancialStatementPeriod).where(
                FinancialStatementPeriod.company_id == company_id,
                FinancialStatementPeriod.period_type == "annual",
                FinancialStatementPeriod.year.in_(EXPECTED_VALUES),
            )
        )
    )
    if {period.year for period in periods} != set(EXPECTED_VALUES):
        raise ValueError("APSEZ promotion did not create all three annual financial periods")
    for period in periods:
        period.report_date = date(period.year, 3, 31)

    candidate_ids = {candidate.id for candidate in candidates}
    revisions = list(
        db.scalars(
            select(SourceFactRevision).where(SourceFactRevision.financial_candidate_id.in_(candidate_ids))
        )
    )
    for revision in revisions:
        fiscal_year = revision.financial_candidate.fiscal_year
        revision.effective_at = date(fiscal_year, 3, 31)
    db.commit()
    return len(revisions)


def _preserve_single_industry_mapping(db, company: Company, cutoff: date) -> dict[str, object] | None:
    existing = IndustryMappingService.get_industry_mix(db, company.id)
    if existing is None and company.damodaran_industry:
        existing = IndustryMappingService.save_industry_mix(
            db,
            company.id,
            basis="revenue",
            as_of_date=cutoff,
            notes="Migrated from the previously approved single-industry mapping; edit the mix when segment weights are available.",
            allocations=[
                {
                    "segment_name": "Core operations",
                    "industry_name": company.damodaran_industry,
                    "weight_percent": 100.0,
                }
            ],
        )
    return IndustryMappingService.serialize_industry_mix(db, existing) if existing else None


def _refresh_workflow_and_draft(db, company: Company, cutoff: date) -> ValuationSetupDraft | None:
    workflow = db.scalar(select(CompanySetupWorkflow).where(CompanySetupWorkflow.company_id == company.id))
    if workflow is not None:
        workflow.filing_status = "complete"
        workflow.financial_extraction_status = "reviewed"
        workflow.current_step = "valuation_review"
        workflow.valuation_readiness_status = "blocked"
        db.commit()

    draft = db.scalar(
        select(ValuationSetupDraft)
        .where(
            ValuationSetupDraft.company_id == company.id,
            ValuationSetupDraft.user_id == VALUATION_USER_ID,
            ValuationSetupDraft.status.in_(("draft", "ready_to_value")),
        )
        .order_by(ValuationSetupDraft.updated_at.desc(), ValuationSetupDraft.id.desc())
    )
    if draft is None:
        return None
    draft = ValuationSetupDraftService.refresh(db, draft)
    metadata = dict(draft.source_metadata_json or {})
    metadata.update(
        {
            "valuation_cutoff_date": cutoff.isoformat(),
            "valuation_cutoff_timezone": "Asia/Kolkata",
            "financial_history_status": "complete",
            "operating_ebit_claim_type": "Calculation",
            "operating_ebit_method": "revenue_less_operating_employee_depreciation_and_other_expenses",
            "operating_ebit_source_document_ids": [3, 4],
        }
    )
    removed_prefixes = (
        "APSEZ financial extraction candidates require explicit review",
        "Operating EBIT is unresolved",
        "Company has no extracted actuals",
    )
    draft.source_metadata_json = metadata
    draft.warnings_json = [
        warning
        for warning in (draft.warnings_json or [])
        if not warning.startswith(removed_prefixes)
    ]
    db.commit()
    db.refresh(draft)
    return draft


def _two_market_report(db, company: Company) -> dict[str, object]:
    aapl = db.scalar(select(Company).where(Company.ticker == "AAPL", Company.market == "US"))
    if aapl is None:
        raise ValueError("AAPL reference history is required for the two-market certification")
    aapl_document_ids = sorted(
        {
            document_id
            for document_id in db.scalars(
                select(FinancialExtractionCandidate.raw_document_id).where(
                    FinancialExtractionCandidate.company_id == aapl.id,
                    FinancialExtractionCandidate.fiscal_year.in_((2022, 2023, 2024, 2025)),
                    FinancialExtractionCandidate.review_status == "promoted",
                )
            )
        }
    )
    return build_certification_report(
        db,
        {
            "candidates": [
                {
                    "label": "AAPL FY2022-FY2025",
                    "company_id": aapl.id,
                    "market": "US",
                    "source_document_ids": aapl_document_ids,
                    "is_mock": False,
                    "source_assertion": "real_primary_source",
                },
                {
                    "label": "APSEZ FY2023-FY2025",
                    "company_id": company.id,
                    "market": "IN",
                    "source_document_ids": sorted(EXPECTED_DOCUMENT_SHA256),
                    "is_mock": False,
                    "source_assertion": "real_primary_source",
                },
            ]
        },
    )


def finalize(db, *, cutoff: date) -> dict[str, object]:
    company = _company(db)
    documents = _documents(db, company.id)
    run = start_processing_run(
        db,
        run_type="reference_financial_promotion",
        source_type="manual_financial_upload",
        source_id=documents[3].source_id,
        company_id=company.id,
        metadata={
            "approval_date": APPROVAL_DATE.isoformat(),
            "valuation_cutoff_date": cutoff.isoformat(),
            "approved_source_document_ids": sorted(EXPECTED_DOCUMENT_SHA256),
            "expected_reviewed_source_fact_count": 48,
        },
    )
    try:
        asset_page_count_corrections = _repair_asset_page_counts(db, documents)
        approved = _approved_candidates(db, company.id)
        for candidate in approved:
            _set_period_end(candidate)
            if candidate.review_status != "promoted":
                candidate.review_status = "reviewed"
        ebit_candidates, created_ebit_count = _ensure_ebit_candidates(db, company.id, documents)
        _assert_no_unexpected_promotable_candidates(db, company.id, approved + ebit_candidates)
        for document in documents.values():
            payload = dict(document.raw_payload_json or {})
            payload.update(
                {
                    "promotion_authorized": True,
                    "approval_date": APPROVAL_DATE.isoformat(),
                    "approval_scope": "FY2023-FY2025 reviewed annual facts and documented operating EBIT calculations",
                }
            )
            document.raw_payload_json = payload
        db.commit()

        promoted_count = promote_reviewed_candidates(db, company.id)
        all_candidates = approved + ebit_candidates
        corrected_revision_count = _correct_fiscal_dates(db, company.id, all_candidates)

        workflow = db.scalar(select(CompanySetupWorkflow).where(CompanySetupWorkflow.company_id == company.id))
        if workflow is not None:
            workflow.financial_extraction_status = "reviewed"
            db.commit()
        industry_mix = _preserve_single_industry_mapping(db, company, cutoff)
        draft = _refresh_workflow_and_draft(db, company, cutoff)
        coverage = NormalizedSnapshotBackfillService.summarize(db, company.id)
        reconciliation = FinancialReconciliationService.reconcile(db, company.id)
        certification = _two_market_report(db, company)
        if certification["status"] != "passed":
            raise ValueError(f"Two-market certification remains blocked: {certification}")

        if draft is not None:
            metadata = dict(draft.source_metadata_json or {})
            metadata["financial_history_certification_status"] = "passed"
            metadata["financial_history_certified_at"] = datetime.now(UTC).isoformat()
            draft.source_metadata_json = metadata
            db.commit()

        complete_processing_run(
            db,
            run,
            fetched_count=51,
            created_count=created_ebit_count,
            skipped_duplicate_count=3 - created_ebit_count,
            metadata_patch={
                "promoted_count": promoted_count,
                "fiscal_date_corrections": 3,
                "source_fact_revision_date_corrections": corrected_revision_count,
                "asset_page_count_corrections": asset_page_count_corrections,
                "ebit_values_inr_crore": {
                    str(year): item.value for year, item in EBIT_RECONSTRUCTIONS.items()
                },
                "normalized_coverage_status": coverage["status"],
                "reconciliation_status": reconciliation["status"],
                "two_market_certification_status": certification["status"],
            },
        )
        return {
            "company_id": company.id,
            "approved_source_fact_count": len(approved),
            "ebit_values_inr_crore": {
                str(year): item.value for year, item in EBIT_RECONSTRUCTIONS.items()
            },
            "created_ebit_candidate_count": created_ebit_count,
            "asset_page_count_corrections": asset_page_count_corrections,
            "promoted_count": promoted_count,
            "report_dates": {str(year): f"{year}-03-31" for year in EXPECTED_VALUES},
            "industry_mix": industry_mix,
            "valuation_draft_id": draft.id if draft else None,
            "coverage": coverage,
            "reconciliation": reconciliation,
            "certification": certification,
        }
    except Exception as exc:
        db.rollback()
        persisted = db.get(type(run), run.id)
        if persisted is not None and persisted.status == "running":
            fail_processing_run(db, persisted, error_type=type(exc).__name__, message=str(exc))
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Finalize the explicitly approved APSEZ FY2023-FY2025 real-source history."
    )
    parser.add_argument("--valuation-cutoff-date", type=date.fromisoformat, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        raise SystemExit("Refusing to write without --apply")
    if args.valuation_cutoff_date < APPROVAL_DATE:
        raise SystemExit("Valuation cutoff cannot predate the approval checkpoint")

    with SessionLocal() as db:
        print(json.dumps(finalize(db, cutoff=args.valuation_cutoff_date), indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
