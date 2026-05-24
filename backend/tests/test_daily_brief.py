from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Alert, Company, Event, RawDocument, Source, ThesisNote
from app.services.daily_brief import generate_daily_brief


def test_generate_daily_brief_ranks_events_and_preserves_evidence() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        company = Company(ticker="AAPL", name="Apple Inc.")
        source = Source(name="SEC EDGAR", source_type="filing", reliability_score=95)
        raw_document = RawDocument(
            company=company,
            source=source,
            document_type="filing",
            title="Apple 10-Q",
            url="https://www.sec.gov/example",
            published_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
            raw_text="Risk factor language changed.",
            content_hash="brief-hash-1",
        )
        high_priority_event = Event(
            company=company,
            raw_document=raw_document,
            event_type="filing_change",
            information_speed="slow",
            title="Risk factor language changed",
            description="Supply chain risk language changed.",
            credibility_score=95,
            novelty_score=80,
            impact_score=75,
            priority_score=84,
        )
        lower_priority_event = Event(
            company=company,
            event_type="manual_event",
            information_speed="medium",
            title="Lower priority manual event",
            priority_score=20,
        )
        alert = Alert(
            company=company,
            event=high_priority_event,
            alert_type="source_backed_change",
            severity="medium",
            title="Review Apple filing change",
            confidence_bucket="high",
        )
        thesis_note = ThesisNote(
            company=company,
            title="Apple base thesis",
            thesis_text="Services growth remains important.",
        )

        session.add_all([company, source, raw_document, high_priority_event, lower_priority_event, alert, thesis_note])
        session.commit()

        brief = generate_daily_brief(session)

    assert brief["title"] == "Daily Intelligence Brief"
    assert brief["summary"] == "2 events, 1 alerts, 1 active thesis notes reviewed."
    assert brief["top_events"][0]["title"] == "Risk factor language changed"
    assert brief["top_events"][0]["company"] == "AAPL"
    assert brief["top_events"][0]["source"] == "SEC EDGAR"
    assert brief["top_events"][0]["source_url"] == "https://www.sec.gov/example"
    assert brief["top_events"][1]["title"] == "Lower priority manual event"
    assert brief["alerts"][0]["title"] == "Review Apple filing change"
    assert brief["follow_up_questions"][0] == "Does this change any active thesis assumption?"
