from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Company, CompanySetupWorkflow, RawDocument, User, ValuationSetupDraft
from app.services.company_setup import get_or_start_company_setup
from app.services.pdf_financial_extraction import (
    ParsedPdf,
    ensure_pdf_source,
    ingest_pdf_financials,
    parse_pdf_financial_tables,
    validate_pdf_upload,
)
from app.services.processing_runs import complete_processing_run, fail_processing_run, start_processing_run
from app.services.valuation_setup_draft import ValuationSetupDraftService


COMPANY_NAME = "Adani Ports and Special Economic Zone Limited"
LOCAL_SYMBOL = "ADANIPORTS"
ISIN = "INE742F01042"
SOURCE_INDUSTRY_CLASSIFICATION = "Transport Infrastructure"
VALUATION_USER_ID = "local-user"

FY25_NSE_URL = (
    "https://nsearchives.nseindia.com/annual_reports/"
    "AR_26467_ADANIPORTS_2024_2025_A_30052025204446.pdf"
)
FY24_NSE_URL = (
    "https://nsearchives.nseindia.com/corporate/"
    "ADANIPORTS_28052024214257_IntimationofAnnualReport.pdf"
)
Q1_INVESTOR_URL = "https://www.adaniports.com/investors"
Q1_REVISED_CONSOLIDATED_IXBRL_URL = (
    "https://nsearchives.nseindia.com/corporate/ixbrl/"
    "INTEGRATED_FILING_INDAS_180165_29072026202624_iXBRL_WEB.html"
)


@dataclass(frozen=True)
class FilingSpec:
    key: str
    path: Path
    expected_sha256: str
    document_type: str
    title: str
    published_at: datetime
    source_url: str
    page_numbers: tuple[int, ...] | None
    retained_years: frozenset[int]
    source_assertion: str


def _specs(args: argparse.Namespace) -> tuple[FilingSpec, ...]:
    return (
        FilingSpec(
            key="fy25",
            path=Path(args.fy25_pdf),
            expected_sha256="2ec4e75290acf3845677ab4a2efd64869d5c9ea5c472a3f0421d9d1611527262",
            document_type="annual_report",
            title="APSEZ Integrated Annual Report FY2024-25",
            published_at=datetime(2025, 5, 30, tzinfo=UTC),
            source_url=FY25_NSE_URL,
            page_numbers=(465, 466, 542),
            retained_years=frozenset({2024, 2025}),
            source_assertion="real_primary_source",
        ),
        FilingSpec(
            key="fy24",
            path=Path(args.fy24_pdf),
            expected_sha256="7f4ff812ea46d1d1c091e58f2161719285fee9ad39ea5e29c3b4beca13aea03f",
            document_type="annual_report",
            title="APSEZ Integrated Annual Report FY2023-24",
            published_at=datetime(2024, 5, 28, tzinfo=UTC),
            source_url=FY24_NSE_URL,
            page_numbers=(438, 439, 514),
            retained_years=frozenset({2023}),
            source_assertion="real_primary_source",
        ),
        FilingSpec(
            key="q1_fy27",
            path=Path(args.q1_fy27_pdf),
            expected_sha256="f02e198abf211727c24adeea41b9b861dd6ff0afbb5d96664a1271dcad2edafd",
            document_type="investor_presentation",
            title="APSEZ Q1 FY2026-27 media release and investor presentation",
            published_at=datetime(2026, 7, 29, tzinfo=UTC),
            source_url=Q1_INVESTOR_URL,
            page_numbers=None,
            retained_years=frozenset(),
            source_assertion="official_source_summary",
        ),
    )


def _read_verified(spec: FilingSpec) -> bytes:
    content = spec.path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if digest != spec.expected_sha256:
        raise ValueError(f"{spec.key} SHA-256 mismatch: expected {spec.expected_sha256}, got {digest}")
    return content


def _ensure_company(db) -> Company:
    company = db.scalar(
        select(Company).where(
            Company.market == "IN",
            Company.primary_exchange == "NSE",
            Company.local_symbol == LOCAL_SYMBOL,
        )
    )
    if company is None:
        company = Company(
            ticker=LOCAL_SYMBOL,
            local_symbol=LOCAL_SYMBOL,
            name=COMPANY_NAME,
            market="IN",
            primary_exchange="NSE",
            exchange="NSE",
            isin=ISIN,
            regulatory_id=ISIN,
            regulatory_id_type="ISIN",
            currency="INR",
            country="India",
            region="Asia",
            asset_type="equity",
            security_type="common_stock",
            aliases_json=["APSEZ", COMPANY_NAME],
            active=True,
        )
        db.add(company)
        db.commit()
        db.refresh(company)
    elif company.isin not in {None, ISIN}:
        raise ValueError(f"Existing {LOCAL_SYMBOL} company has conflicting ISIN {company.isin}")

    if not company.industry:
        company.industry = SOURCE_INDUSTRY_CLASSIFICATION

    get_or_start_company_setup(db, company.id)
    workflow = db.scalar(select(CompanySetupWorkflow).where(CompanySetupWorkflow.company_id == company.id))
    assert workflow is not None
    workflow.identity_status = "reviewed"
    workflow.source_status = "manual_only"
    workflow.security_review_status = "local_only"
    if workflow.current_step == "identity":
        workflow.current_step = "source_setup"
    if company.damodaran_industry == "Advertising" and workflow.industry_mapping_status != "reviewed":
        # Remove the former alphabetical fallback; a benchmark mapping still needs human confirmation.
        company.damodaran_industry = None
        workflow.industry_mapping_status = "missing"
        workflow.valuation_readiness_status = "blocked"
    db.commit()
    return company


def _filtered_parse(content: bytes, spec: FilingSpec) -> ParsedPdf:
    candidate_period_type = "annual" if spec.document_type == "annual_report" else "unknown"
    parsed = parse_pdf_financial_tables(
        content,
        page_numbers=spec.page_numbers,
        period_type=candidate_period_type,
    )
    retained = tuple(
        candidate for candidate in parsed.candidates if candidate.fiscal_year in spec.retained_years
    )
    warning = (
        "comparative_periods_excluded_in_favor_of_latest_audit"
        if spec.document_type == "annual_report"
        else "investor_presentation_not_certification_evidence"
    )
    return replace(
        parsed,
        candidates=retained,
        warnings=tuple(sorted(set(parsed.warnings) | {warning})),
    )


def _assert_annual_candidate_set(parsed: ParsedPdf, spec: FilingSpec) -> None:
    if spec.document_type != "annual_report":
        return
    required = {
        "revenue",
        "net_income",
        "cash",
        "debt",
        "diluted_shares",
        "minority_interests",
    }
    by_year: dict[int, set[str]] = {}
    for candidate in parsed.candidates:
        by_year.setdefault(candidate.fiscal_year, set()).add(candidate.metric_code)
    failures = {
        year: sorted(required - by_year.get(year, set()))
        for year in spec.retained_years
        if required - by_year.get(year, set())
    }
    if failures:
        raise ValueError(f"{spec.key} is missing required review candidates: {failures}")
    if any(candidate.metric_code == "ebit" for candidate in parsed.candidates):
        raise ValueError("APSEZ EBIT must remain unresolved until operating/non-operating adjustments are reviewed")


def _stage_filing(db, company: Company, spec: FilingSpec, content: bytes) -> dict[str, object]:
    upload = validate_pdf_upload(spec.path.name, "application/pdf", content)
    content_hash = f"pdf-filing:{company.id}:{upload.sha256}"
    existing = db.scalar(select(RawDocument).where(RawDocument.content_hash == content_hash))
    if existing is not None:
        return {"key": spec.key, "raw_document_id": existing.id, "status": "existing"}

    source = ensure_pdf_source(db)
    run = start_processing_run(
        db,
        run_type="reference_filing_stage",
        source_type=source.source_type,
        source_id=source.id,
        company_id=company.id,
        metadata={
            "filing_key": spec.key,
            "source_assertion": spec.source_assertion,
            "source_url": spec.source_url,
            "promotion_authorized": False,
        },
    )
    try:
        parsed = _filtered_parse(content, spec)
        _assert_annual_candidate_set(parsed, spec)
        result = ingest_pdf_financials(
            db,
            company=company,
            source=source,
            upload=upload,
            parsed=parsed,
            document_type=spec.document_type,
            title=spec.title,
            published_at=spec.published_at,
            source_url=spec.source_url,
        )
        document = db.get(RawDocument, result.raw_document_id)
        assert document is not None
        payload = dict(document.raw_payload_json or {})
        payload.update(
            {
                "source_assertion": spec.source_assertion,
                "claim_type": "Source Summary" if spec.document_type == "investor_presentation" else "Fact",
                "promotion_authorized": False,
                "retained_fiscal_years": sorted(spec.retained_years),
            }
        )
        if spec.key == "q1_fy27":
            payload["related_revised_consolidated_ixbrl_url"] = Q1_REVISED_CONSOLIDATED_IXBRL_URL
            payload["statutory_filing_status"] = "available_separately"
        document.raw_payload_json = payload
        db.commit()
        complete_processing_run(
            db,
            run,
            fetched_count=len(parsed.scanned_pages),
            created_count=result.created_count,
            metadata_patch={
                "raw_document_id": result.raw_document_id,
                "asset_id": result.asset.id,
                "sha256": upload.sha256,
                "page_count": parsed.page_count,
                "scanned_pages": list(parsed.scanned_pages),
                "retained_fiscal_years": sorted(spec.retained_years),
                "candidate_count": result.created_count,
                "promotion_authorized": False,
                "warnings": list(parsed.warnings),
            },
        )
        return {
            "key": spec.key,
            "raw_document_id": result.raw_document_id,
            "processing_run_id": run.id,
            "candidate_count": result.created_count,
            "status": "staged_needs_review" if result.created_count else "stored_source_only",
        }
    except Exception as exc:
        db.rollback()
        persisted = db.get(type(run), run.id)
        if persisted is not None and persisted.status == "running":
            fail_processing_run(db, persisted, error_type=type(exc).__name__)
        raise


def _set_cutoff_date(db, company: Company, cutoff: date) -> ValuationSetupDraft:
    if db.get(User, VALUATION_USER_ID) is None:
        raise ValueError(f"Required local valuation user {VALUATION_USER_ID!r} does not exist")
    draft = ValuationSetupDraftService.create_or_reopen(db, company.id, VALUATION_USER_ID)
    source_metadata = dict(draft.source_metadata_json or {})
    source_metadata.update(
        {
            "valuation_cutoff_date": cutoff.isoformat(),
            "valuation_cutoff_timezone": "Asia/Kolkata",
            "financial_history_status": "needs_review",
            "latest_statutory_financial_source": Q1_REVISED_CONSOLIDATED_IXBRL_URL,
        }
    )
    warnings = list(draft.warnings_json or [])
    for warning in (
        "APSEZ financial extraction candidates require explicit review before promotion.",
        "Operating EBIT is unresolved; do not derive a valuation margin from profit before tax.",
        "Q1 FY27 investor materials are supplementary; use the revised consolidated NSE iXBRL as the statutory source.",
    ):
        if warning not in warnings:
            warnings.append(warning)
    draft.source_metadata_json = source_metadata
    draft.warnings_json = warnings
    draft.status = "draft"
    db.commit()
    db.refresh(draft)
    return draft


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage APSEZ primary-source evidence without promotion.")
    parser.add_argument("--fy25-pdf", required=True)
    parser.add_argument("--fy24-pdf", required=True)
    parser.add_argument("--q1-fy27-pdf", required=True)
    parser.add_argument("--valuation-cutoff-date", type=date.fromisoformat, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        raise SystemExit("Refusing to write without --apply")

    specs = _specs(args)
    contents = {spec.key: _read_verified(spec) for spec in specs}
    with SessionLocal() as db:
        company = _ensure_company(db)
        staged = [_stage_filing(db, company, spec, contents[spec.key]) for spec in specs]
        draft = _set_cutoff_date(db, company, args.valuation_cutoff_date)
        workflow = db.scalar(select(CompanySetupWorkflow).where(CompanySetupWorkflow.company_id == company.id))
        summary = {
            "company_id": company.id,
            "company": company.name,
            "market": company.market,
            "symbol": company.local_symbol,
            "isin": company.isin,
            "valuation_cutoff_date": args.valuation_cutoff_date.isoformat(),
            "valuation_draft_id": draft.id,
            "workflow": {
                "identity_status": workflow.identity_status if workflow else None,
                "filing_status": workflow.filing_status if workflow else None,
                "financial_extraction_status": workflow.financial_extraction_status if workflow else None,
                "industry_mapping_status": workflow.industry_mapping_status if workflow else None,
                "valuation_readiness_status": workflow.valuation_readiness_status if workflow else None,
            },
            "filings": staged,
            "promotion_authorized": False,
            "known_blocker": "operating_ebit_requires_review",
        }
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
