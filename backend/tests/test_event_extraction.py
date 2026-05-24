from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Company, Event, RawDocument, Source
from app.services.event_extraction import extract_events_from_raw_documents


def test_extract_events_from_raw_documents_creates_rule_based_events_and_skips_existing() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        company = Company(ticker="NVDA", name="Nvidia")
        source = Source(name="SEC EDGAR", source_type="sec", reliability_score=95)
        sec_document = RawDocument(
            company=company,
            source=source,
            document_type="sec_filing_metadata",
            title="NVDA 10-Q filed 2026-05-24",
            url="https://www.sec.gov/example",
            raw_payload_json={"form_type": "10-Q"},
            content_hash="event-extract-sec-1",
        )
        rss_document = RawDocument(
            company=company,
            source=Source(name="Example RSS", source_type="rss", reliability_score=70),
            document_type="rss_item",
            title="Nvidia supply update",
            raw_text="Supply update from a news source.",
            content_hash="event-extract-rss-1",
        )
        session.add_all([company, source, sec_document, rss_document])
        session.commit()

        first_result = extract_events_from_raw_documents(session)
        second_result = extract_events_from_raw_documents(session)
        events = list(session.scalars(select(Event).order_by(Event.id)))

    assert first_result.created == 2
    assert first_result.skipped_existing == 0
    assert second_result.created == 0
    assert second_result.skipped_existing == 2
    assert len(events) == 2
    assert events[0].event_type == "sec_filing"
    assert events[0].information_speed == "slow"
    assert events[0].credibility_score == 95
    assert events[0].priority_score == 80
    assert events[1].event_type == "rss_news"
    assert events[1].information_speed == "fast"
    assert events[1].credibility_score == 70
