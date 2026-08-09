from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Alert, Company, Event, RawDocument, Source, ThesisNote, DailyBrief
from app.services.morning_briefing_engine import MorningBriefingEngine


USER_ID = "brief-owner"


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
            user_id=USER_ID,
            company=company,
            event=high_priority_event,
            alert_type="source_backed_change",
            severity="medium",
            title="Review Apple filing change",
            confidence_bucket="high",
        )
        thesis_note = ThesisNote(
            user_id=USER_ID,
            company=company,
            title="Apple base thesis",
            thesis_text="Services growth remains important.",
        )

        session.add_all([company, source, raw_document, high_priority_event, lower_priority_event, alert, thesis_note])
        session.commit()

        session.add_all(
            [
                Alert(
                    user_id="another-user",
                    company=company,
                    alert_type="private_alert",
                    severity="high",
                    title="Another user's alert",
                ),
                ThesisNote(
                    user_id="another-user",
                    company=company,
                    title="Another user's thesis",
                    thesis_text="Private thesis content.",
                ),
            ]
        )
        session.commit()

        brief_orm = MorningBriefingEngine.generate_briefing(session, user_id=USER_ID)
        brief = brief_orm.payload_json

    assert brief_orm.title == "Daily Intelligence Brief"
    assert brief_orm.review_status == "new"

    # We should have high_materiality_events
    high_mat = brief["high_materiality_events"]
    assert len(high_mat) > 0
    assert high_mat[0]["headline"] == "Risk factor language changed"
    assert high_mat[0]["priority"] == "high"


def test_generate_daily_brief_respects_last_review_date() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Create an old reviewed brief
        old_brief = DailyBrief(
            user_id=USER_ID,
            brief_date=date(2026, 1, 1),
            title="Old Brief",
            summary="Old",
            payload_json={},
            review_status="reviewed",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        session.add(old_brief)
        session.commit()

        # Event created before the review should be ignored
        company = Company(ticker="AAPL", name="Apple Inc.")
        event_old = Event(
            company=company,
            event_type="manual",
            information_speed="medium",
            title="Old Event",
            priority_score=90,
            created_at=datetime(2025, 12, 1, tzinfo=timezone.utc),
        )
        # Event created after review should be included
        event_new = Event(
            company=company,
            event_type="manual",
            information_speed="medium",
            title="New Event",
            priority_score=90,
            created_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )
        session.add_all([company, event_old, event_new])
        session.commit()

        # Generate brief
        new_brief_orm = MorningBriefingEngine.generate_briefing(session, user_id=USER_ID)
        new_brief = new_brief_orm.payload_json

    # Should only contain 'New Event'
    high_mat = new_brief["high_materiality_events"]
    assert len(high_mat) == 1
    assert high_mat[0]["headline"] == "New Event"
