from datetime import date

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Company, DailyBrief, Event
from app.services.morning_briefing_engine import MorningBriefingEngine


def test_save_daily_brief_persists_generated_snapshot() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        company = Company(ticker="MSFT", name="Microsoft")
        event = Event(
            company=company,
            event_type="manual_event",
            information_speed="medium",
            title="Azure growth note",
            priority_score=72,
        )
        session.add_all([company, event])
        session.commit()

        saved = MorningBriefingEngine.generate_briefing(
            session,
            user_id="brief-owner",
            target_date=date(2026, 5, 24),
        )

        persisted = session.scalar(select(DailyBrief).where(DailyBrief.id == saved.id))

    assert persisted is not None
    assert persisted.user_id == "brief-owner"
    assert persisted.brief_date == date(2026, 5, 24)
    assert persisted.title == "Daily Intelligence Brief"
    assert persisted.summary == "1 event since the last reviewed brief; 0 unresolved contradiction alerts; 0 affected held companies."
    assert persisted.payload_json["calculation_status"] == "complete"
    assert persisted.payload_json["valuation_analysis_status"] == "not_required"
    assert persisted.payload_json["new_since_last_review"]["filings"] == []
    assert persisted.payload_json["high_materiality_events"] == []
