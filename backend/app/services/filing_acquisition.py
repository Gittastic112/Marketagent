import logging
from collections.abc import Callable

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import FilingDiscoveryRead
from app.api.errors import PublicApiError
from app.models import Company, RawDocument
from app.providers.filings import ManualFilingCreate, get_filing_provider
from app.services.filing_manual import create_manual_filing
from app.services.processing_runs import start_processing_run, complete_processing_run, fail_processing_run


FILING_DOCUMENT_TYPES = {
    "10-K",
    "10-Q",
    "8-K",
    "annual_report",
    "quarterly_result",
    "investor_presentation",
    "exchange_announcement",
    "shareholding_pattern",
    "corporate_action",
}
logger = logging.getLogger(__name__)


def audited_filing_preview(db: Session, company: Company, provider_name: str,
                          fetch: Callable, *, form_type: str | None, filing_year: int | None, limit: int):
    if not 1 <= limit <= 100 or (filing_year is not None and not 1900 <= filing_year <= 2200):
        raise HTTPException(status_code=422, detail="Use a limit of 1-100 and a valid filing year")
    if form_type is not None and len(form_type) > 40:
        raise HTTPException(status_code=422, detail="Invalid filing form type")
    run = start_processing_run(db, run_type="filing_discovery", source_type=provider_name,
        company_id=company.id, metadata={"form_type": form_type, "filing_year": filing_year,
                                       "limit": limit, "stores_financials": False})
    try:
        filings = fetch()
        complete_processing_run(db, run, fetched_count=len(filings))
        return filings
    except Exception:
        db.rollback()
        fail_processing_run(db, run, error_type="FILING_DISCOVERY_FAILED",
                            message="Filing metadata could not be retrieved.")
        raise


def discover_company_filings(
    db: Session,
    company_id: int,
    form_type: str | None = "10-K",
    filing_year: int | None = None,
    limit: int = 20,
) -> FilingDiscoveryRead:
    company = _get_company(db, company_id)
    market = (company.market or "US").upper()
    provider = get_filing_provider(company, source="auto")

    if market == "IN":
        return FilingDiscoveryRead(
            company_id=company.id,
            market=market,
            provider_name=provider.provider_name,
            mode="manual",
            manual_required=True,
            filings=[],
            next_action="Add a reviewed annual report, quarterly result, or exchange announcement manually.",
        )

    try:
        filings = audited_filing_preview(db, company, provider.provider_name,
            lambda: provider.preview_filings(company, form_type=form_type, filing_year=filing_year, limit=limit),
            form_type=form_type, filing_year=filing_year, limit=limit)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Filing discovery provider failed",
            extra={"provider": provider.provider_name, "exception_type": type(exc).__name__},
        )
        raise PublicApiError(
            status_code=502,
            code="FILING_DISCOVERY_FAILED",
            message="Filing discovery is temporarily unavailable.",
            retryable=True,
            provider=provider.provider_name,
        ) from exc

    return FilingDiscoveryRead(
        company_id=company.id,
        market=market,
        provider_name=provider.provider_name,
        mode="automated",
        manual_required=False,
        filings=filings,
        next_action="Review filing candidates before ingestion or add a manual filing if the source is not available.",
    )


def create_manual_company_filing_link(db: Session, company_id: int, payload: ManualFilingCreate) -> RawDocument:
    company = _get_company(db, company_id)
    return create_manual_filing(db, company, payload)


def list_company_filings(db: Session, company_id: int) -> list[RawDocument]:
    _get_company(db, company_id)
    documents = list(
        db.scalars(
            select(RawDocument)
            .where(RawDocument.company_id == company_id)
            .order_by(RawDocument.published_at.desc().nullslast(), RawDocument.id.desc())
        )
    )
    return [document for document in documents if _is_filing_document(document)]


def get_filing_document(db: Session, filing_id: int) -> RawDocument:
    document = db.get(RawDocument, filing_id)
    if document is None or not _is_filing_document(document):
        raise HTTPException(status_code=404, detail="Filing not found")
    return document


def _get_company(db: Session, company_id: int) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


def _is_filing_document(document: RawDocument) -> bool:
    payload = document.raw_payload_json or {}
    return payload.get("source_kind") == "manual_filing" or document.document_type in FILING_DOCUMENT_TYPES
