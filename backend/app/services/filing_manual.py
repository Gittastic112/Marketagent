from hashlib import sha256
import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Company, RawDocument, Source
from app.models.company_setup import CompanySetupWorkflow
from app.providers.filings import ALLOWED_MANUAL_FILING_TYPES, ManualFilingCreate


def create_manual_filing(db: Session, company: Company, payload: ManualFilingCreate) -> RawDocument:
    if payload.document_type not in ALLOWED_MANUAL_FILING_TYPES:
        raise HTTPException(status_code=422, detail="Unsupported manual filing document_type")

    # Serialize retries for one issuer and keep review invalidation atomic with
    # creation. Network is never performed by manual intake.
    company = db.scalar(select(Company).where(Company.id == company.id)
                        .with_for_update().execution_options(populate_existing=True))
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    content_hash = _manual_filing_hash(company, payload)
    existing = db.scalar(select(RawDocument).where(RawDocument.content_hash == content_hash))
    if existing is not None:
        db.commit()
        return existing
    source = _get_or_create_manual_filing_source(db)
    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type=payload.document_type,
        title=payload.title,
        url=payload.url,
        published_at=payload.published_at,
        raw_text=payload.raw_text,
        raw_payload_json={
            **(payload.raw_payload_json or {}),
            "source_kind": "manual_filing",
            "filing_system": "MANUAL_UPLOAD",
            "market": company.market,
            "primary_exchange": company.primary_exchange,
            "local_symbol": company.local_symbol or company.ticker,
        },
        content_hash=content_hash,
    )
    db.add(document)
    workflow = db.scalar(select(CompanySetupWorkflow).where(CompanySetupWorkflow.company_id == company.id))
    if workflow is not None:
        workflow.filing_status = "needs_review"
        workflow.current_step = "financial_extraction"
    db.commit()
    db.refresh(document)
    return document


def _get_or_create_manual_filing_source(db: Session) -> Source:
    source = db.scalar(select(Source).where(Source.name == "Manual Filings"))
    if source is not None:
        return source

    source = Source(name="Manual Filings", source_type="manual", reliability_score=70, active=True)
    try:
        # Two different issuers may create the shared source concurrently.
        with db.begin_nested():
            db.add(source)
            db.flush()
    except IntegrityError:
        source = db.scalar(select(Source).where(Source.name == "Manual Filings"))
        if source is None:
            raise
    return source


def _manual_filing_hash(company: Company, payload: ManualFilingCreate) -> str:
    # Versioned, unambiguous, stable bytes; leave historical hashes untouched.
    stable = json.dumps({"company_id": company.id, "payload": payload.model_dump(mode="json")},
                        sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return f"manual-filing:v2:{sha256(stable.encode('utf-8')).hexdigest()}"
