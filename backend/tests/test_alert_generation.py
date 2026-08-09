from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Alert, Company, Event
from app.services.alert_generation import generate_alerts_from_events


def test_generate_alerts_from_events_creates_alerts_for_high_priority_events_only() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        company = Company(ticker="AAPL", name="Apple")
        high_priority = Event(
            company=company,
            event_type="sec_filing",
            information_speed="slow",
            title="Apple 10-K filed",
            description="Source URL: https://www.sec.gov/example",
            credibility_score=95,
            novelty_score=70,
            impact_score=75,
            priority_score=80,
        )
        low_priority = Event(
            company=company,
            event_type="rss_news",
            information_speed="fast",
            title="Low priority headline",
            priority_score=40,
        )
        session.add_all([company, high_priority, low_priority])
        session.commit()

        first_result = generate_alerts_from_events(session, user_id="researcher-1")
        second_result = generate_alerts_from_events(session, user_id="researcher-1")
        other_user_result = generate_alerts_from_events(session, user_id="researcher-2")
        alerts = list(session.scalars(select(Alert).order_by(Alert.id)))

    assert first_result.created == 1
    assert first_result.skipped_existing == 0
    assert first_result.skipped_below_threshold == 1
    assert second_result.created == 0
    assert second_result.skipped_existing == 1
    assert second_result.skipped_below_threshold == 1
    assert other_user_result.created == 1
    assert len(alerts) == 2
    assert {alert.user_id for alert in alerts} == {"researcher-1", "researcher-2"}
    assert alerts[0].event_id == high_priority.id
    assert alerts[0].company_id == company.id
    assert alerts[0].alert_type == "priority_event"
    assert alerts[0].severity == "high"
    assert alerts[0].confidence_bucket == "high"
    assert alerts[0].review_status == "unreviewed"


def test_generate_alerts_from_events_uses_configured_default_threshold(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    class Settings:
        alert_priority_threshold = 85

    monkeypatch.setattr("app.services.alert_generation.get_settings", lambda: Settings())

    with Session(engine) as session:
        company = Company(ticker="AAPL", name="Apple")
        event = Event(
            company=company,
            event_type="sec_filing",
            information_speed="slow",
            title="Apple 10-K filed",
            credibility_score=95,
            priority_score=80,
        )
        session.add_all([company, event])
        session.commit()

        result = generate_alerts_from_events(session, user_id="researcher-1")
        alerts = list(session.scalars(select(Alert)))

    assert result.created == 0
    assert result.skipped_below_threshold == 1
    assert alerts == []
