from datetime import UTC, datetime

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
    assert events[0].credibility_score == 70
    assert events[0].novelty_score == 80
    assert events[0].impact_score == 55
    assert events[0].priority_score == 67
    assert events[1].event_type == "rss_news"
    assert events[1].information_speed == "fast"
    assert events[1].credibility_score == 30
    assert events[1].priority_score == 42


def test_extract_events_from_raw_documents_creates_filing_change_event_for_comparable_sec_text() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        company = Company(ticker="MSFT", name="Microsoft")
        source = Source(name="SEC EDGAR", source_type="sec", reliability_score=95)
        prior_document = RawDocument(
            company=company,
            source=source,
            document_type="sec_filing_metadata",
            title="MSFT 10-K filed 2025-05-24",
            url="https://www.sec.gov/prior",
            published_at=datetime(2025, 5, 24, tzinfo=UTC),
            raw_text="Risk Factors\nSupply chain conditions are stable.\nRevenue growth remains strong.",
            raw_payload_json={"form_type": "10-K", "accession_number": "0000789019-25-000001"},
            content_hash="filing-change-prior",
        )
        current_document = RawDocument(
            company=company,
            source=source,
            document_type="sec_filing_metadata",
            title="MSFT 10-K filed 2026-05-24",
            url="https://www.sec.gov/current",
            published_at=datetime(2026, 5, 24, tzinfo=UTC),
            raw_text="Risk Factors\nSupply chain conditions have worsened.\nRevenue growth remains strong.",
            raw_payload_json={"form_type": "10-K", "accession_number": "0000789019-26-000001"},
            content_hash="filing-change-current",
        )
        session.add_all([company, source, prior_document, current_document])
        session.commit()

        result = extract_events_from_raw_documents(session)
        events = list(session.scalars(select(Event).order_by(Event.id)))

    assert result.created == 2
    assert events[0].event_type == "sec_filing"
    assert events[1].event_type == "filing_text_change"
    assert events[1].raw_document_id == current_document.id
    assert events[1].information_speed == "slow"
    assert events[1].priority_score >= 70
    assert "Prior RawDocument" in events[1].description
    assert f"#{prior_document.id}" in events[1].description
    assert "Current RawDocument" in events[1].description
    assert f"#{current_document.id}" in events[1].description
    assert "-Supply chain conditions are stable." in events[1].description
    assert "+Supply chain conditions have worsened." in events[1].description


def test_extract_events_from_raw_documents_does_not_flag_unchanged_comparable_sec_text() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    filing_text = "Risk Factors\nSupply chain conditions are stable."

    with Session(engine) as session:
        company = Company(ticker="MSFT", name="Microsoft")
        source = Source(name="SEC EDGAR", source_type="sec", reliability_score=95)
        prior_document = RawDocument(
            company=company,
            source=source,
            document_type="sec_filing_metadata",
            title="MSFT 10-Q filed 2026-02-24",
            published_at=datetime(2026, 2, 24, tzinfo=UTC),
            raw_text=filing_text,
            raw_payload_json={"form_type": "10-Q"},
            content_hash="filing-unchanged-prior",
        )
        current_document = RawDocument(
            company=company,
            source=source,
            document_type="sec_filing_metadata",
            title="MSFT 10-Q filed 2026-05-24",
            published_at=datetime(2026, 5, 24, tzinfo=UTC),
            raw_text=filing_text,
            raw_payload_json={"form_type": "10-Q"},
            content_hash="filing-unchanged-current",
        )
        session.add_all([company, source, prior_document, current_document])
        session.commit()

        extract_events_from_raw_documents(session)
        events = list(session.scalars(select(Event).order_by(Event.id)))

    assert [event.event_type for event in events] == ["sec_filing", "sec_filing"]
