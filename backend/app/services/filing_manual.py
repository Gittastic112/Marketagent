from datetime import UTC, datetime
from hashlib import sha256

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, RawDocument, Source
from app.providers.filings import ALLOWED_MANUAL_FILING_TYPES, ManualFilingCreate


def create_manual_filing(db: Session, company: Company, payload: ManualFilingCreate) -> RawDocument:
    if payload.document_type not in ALLOWED_MANUAL_FILING_TYPES:
        raise HTTPException(status_code=422, detail="Unsupported manual filing document_type")

    source = _get_or_create_manual_filing_source(db)
    content_hash = _manual_filing_hash(company, payload)
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
    db.commit()
    db.refresh(document)
    return document


def _get_or_create_manual_filing_source(db: Session) -> Source:
    source = db.scalar(select(Source).where(Source.name == "Manual Filings"))
    if source is not None:
        return source

    source = Source(name="Manual Filings", source_type="manual", reliability_score=70, active=True)
    db.add(source)
    db.flush()
    return source


def _manual_filing_hash(company: Company, payload: ManualFilingCreate) -> str:
    stable = "|".join(
        [
            str(company.id),
            company.market or "",
            company.primary_exchange or "",
            company.local_symbol or company.ticker,
            payload.document_type,
            payload.title,
            payload.url or "",
            payload.published_at.isoformat() if payload.published_at is not None else "",
            payload.raw_text or "",
            datetime.now(UTC).isoformat(),
        ]
    )
    return f"manual-filing:{sha256(stable.encode('utf-8')).hexdigest()}"
