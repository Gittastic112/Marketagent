from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, RawDocument


@dataclass(frozen=True)
class SecIngestionResult:
    created: int
    skipped_duplicates: int


@dataclass(frozen=True)
class SecFilingMetadata:
    accession_number: str
    form_type: str
    filing_date: date
    report_date: date | None = None
    primary_document: str | None = None
    filing_url: str | None = None


def ingest_sec_filing_metadata(
    db: Session,
    source_id: int,
    company_id: int,
    filings: list[SecFilingMetadata],
) -> SecIngestionResult:
    company = db.get(Company, company_id)
    ticker = company.ticker if company is not None else f"company-{company_id}"
    created = 0
    skipped_duplicates = 0

    for filing in filings:
        content_hash = build_sec_content_hash(filing)
        existing = db.scalar(select(RawDocument).where(RawDocument.content_hash == content_hash))
        if existing is not None:
            skipped_duplicates += 1
            continue

        db.add(
            RawDocument(
                company_id=company_id,
                source_id=source_id,
                document_type="sec_filing_metadata",
                title=f"{ticker} {filing.form_type} filed {filing.filing_date.isoformat()}",
                url=filing.filing_url,
                published_at=datetime.combine(filing.filing_date, time.min, tzinfo=timezone.utc),
                raw_text=None,
                raw_payload_json={
                    "source_kind": "sec_edgar",
                    "accession_number": filing.accession_number,
                    "form_type": filing.form_type,
                    "filing_date": filing.filing_date.isoformat(),
                    "report_date": filing.report_date.isoformat() if filing.report_date is not None else None,
                    "primary_document": filing.primary_document,
                    "filing_url": filing.filing_url,
                },
                content_hash=content_hash,
            )
        )
        created += 1

    db.commit()
    return SecIngestionResult(created=created, skipped_duplicates=skipped_duplicates)


def build_sec_content_hash(filing: SecFilingMetadata) -> str:
    stable_parts = [filing.accession_number, filing.form_type, filing.filing_date.isoformat()]
    return sha256("|".join(stable_parts).encode("utf-8")).hexdigest()
