import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import FilingDiscoveryRead
from app.api.errors import PublicApiError
from app.models import Company, RawDocument
from app.models.company_setup import CompanySetupWorkflow
from app.providers.filings import ManualFilingCreate, get_filing_provider
from app.services.filing_manual import create_manual_filing


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
        filings = provider.preview_filings(
            company,
            form_type=form_type,
            filing_year=filing_year,
            limit=limit,
        )
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
    document = create_manual_filing(db, company, payload)
    _mark_setup_filing_needs_review(db, company_id)
    db.refresh(document)
    return document


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


def _mark_setup_filing_needs_review(db: Session, company_id: int) -> None:
    workflow = db.scalar(select(CompanySetupWorkflow).where(CompanySetupWorkflow.company_id == company_id))
    if workflow is None:
        return

    workflow.filing_status = "needs_review"
    workflow.current_step = "financial_extraction"
    db.commit()
