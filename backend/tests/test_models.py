from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, selectinload

from app.db.base import Base
from app.models import Alert, Company, Event, RawDocument, Source, ThesisNote


def test_mvp_models_can_be_persisted_with_relationships() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        company = Company(ticker="AAPL", name="Apple Inc.", sector="Technology")
        source = Source(name="SEC EDGAR", source_type="filing", reliability_score=95)
        raw_document = RawDocument(
            company=company,
            source=source,
            document_type="filing",
            title="Apple 10-Q",
            url="https://www.sec.gov/example",
            published_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
            raw_text="Risk factor text",
            raw_payload_json={"form": "10-Q"},
            content_hash="hash-123",
        )
        event = Event(
            company=company,
            raw_document=raw_document,
            event_type="filing_change",
            information_speed="slow",
            title="Risk factor changed",
            description="Supply chain language changed.",
            credibility_score=95,
            novelty_score=80,
            impact_score=70,
            priority_score=82,
        )
        alert = Alert(
            company=company,
            event=event,
            alert_type="source_backed_change",
            severity="medium",
            title="Review supply chain risk",
            summary="A filing risk factor changed.",
            why_it_matters="It may affect the thesis.",
            what_changed="New supply chain language appeared.",
            evidence="Apple 10-Q",
            confidence_bucket="high",
        )
        thesis_note = ThesisNote(
            company=company,
            title="Base thesis",
            thesis_text="Services revenue remains resilient.",
            assumptions_json={"services_growth": "resilient"},
        )

        session.add_all([company, source, raw_document, event, alert, thesis_note])
        session.commit()

        # Detached consumers declare the graph they need before closing a session.
        saved_company = session.scalar(select(Company).where(Company.ticker == "AAPL").options(
            selectinload(Company.raw_documents).selectinload(RawDocument.source),
            selectinload(Company.events).selectinload(Event.alerts),
            selectinload(Company.thesis_notes),
        ))

    assert saved_company is not None
    assert saved_company.raw_documents[0].source.name == "SEC EDGAR"
    assert saved_company.events[0].alerts[0].confidence_bucket == "high"
    assert saved_company.thesis_notes[0].status == "active"
