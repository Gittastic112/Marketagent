from datetime import date

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Company, RawDocument, Source
from app.services.sec_ingestion import SecFilingMetadata, ingest_sec_filing_metadata


def test_ingest_sec_filing_metadata_stores_raw_documents_and_skips_duplicates() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    filing = SecFilingMetadata(
        accession_number="0000320193-26-000001",
        form_type="10-K",
        filing_date=date(2026, 5, 24),
        report_date=date(2026, 3, 31),
        primary_document="aapl-20260331.htm",
        filing_url="https://www.sec.gov/Archives/edgar/data/320193/000032019326000001/aapl-20260331.htm",
    )

    with Session(engine) as session:
        company = Company(ticker="AAPL", name="Apple Inc.", cik="0000320193")
        source = Source(name="SEC EDGAR", source_type="sec")
        session.add_all([company, source])
        session.commit()

        first_result = ingest_sec_filing_metadata(session, source_id=source.id, company_id=company.id, filings=[filing])
        second_result = ingest_sec_filing_metadata(session, source_id=source.id, company_id=company.id, filings=[filing])
        documents = list(session.scalars(select(RawDocument).order_by(RawDocument.id)))

    assert first_result.created == 1
    assert first_result.skipped_duplicates == 0
    assert second_result.created == 0
    assert second_result.skipped_duplicates == 1
    assert len(documents) == 1
    assert documents[0].document_type == "sec_filing_metadata"
    assert documents[0].title == "AAPL 10-K filed 2026-05-24"
    assert documents[0].url == filing.filing_url
    assert documents[0].published_at.date() == date(2026, 5, 24)
    assert documents[0].raw_payload_json["accession_number"] == "0000320193-26-000001"
