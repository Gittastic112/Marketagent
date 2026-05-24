from datetime import date

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Company, DailyBrief, Event
from app.services.daily_brief import save_daily_brief


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

        saved = save_daily_brief(session, brief_date=date(2026, 5, 24))

        persisted = session.scalar(select(DailyBrief).where(DailyBrief.id == saved.id))

    assert persisted is not None
    assert persisted.brief_date == date(2026, 5, 24)
    assert persisted.title == "Daily Intelligence Brief"
    assert persisted.summary == "1 events, 0 alerts, 0 active thesis notes reviewed."
    assert persisted.payload_json["top_events"][0]["title"] == "Azure growth note"
