from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Alert, Company, Event, RawDocument, Source, ThesisNote
from app.services.scoring import (
    calculate_priority_score,
    classify_information_speed,
    get_confidence_bucket,
    score_alert,
    score_event,
)


def test_classify_information_speed_uses_document_and_event_clues() -> None:
    assert classify_information_speed(event_type="sec_filing", document_type="10-K") == "slow"
    assert classify_information_speed(event_type="guidance_change", title="Company updates guidance") == "medium"
    assert classify_information_speed(event_type="rss_news", title="Breaking rumor hits shares") == "fast"


def test_priority_score_is_weighted_and_bounded() -> None:
    assert calculate_priority_score(credibility_score=100, novelty_score=100, impact_score=100, information_speed="fast") == 99
    assert calculate_priority_score(credibility_score=200, novelty_score=-10, impact_score=100, information_speed="slow") == 100


def test_confidence_bucket_uses_expected_ranges() -> None:
    assert get_confidence_bucket(39) == "low"
    assert get_confidence_bucket(40) == "medium"
    assert get_confidence_bucket(69) == "medium"
    assert get_confidence_bucket(70) == "high"


def test_score_event_persists_deterministic_scores_from_source_document_and_thesis() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        company = Company(ticker="NVDA", name="Nvidia")
        source = Source(name="SEC EDGAR", source_type="sec", reliability_score=95)
        document = RawDocument(
            company=company,
            source=source,
            document_type="sec_filing_metadata",
            title="NVDA 10-Q filed with margin change",
            url="https://www.sec.gov/example",
            published_at=datetime.now(UTC),
            raw_payload_json={"form_type": "10-Q", "contradiction_flag": False},
            content_hash="score-event-sec-1",
        )
        thesis = ThesisNote(company=company, title="Margin thesis", thesis_text="Margins matter.", status="active")
        event = Event(
            company=company,
            raw_document=document,
            event_type="margin_change",
            information_speed="medium",
            title="NVDA 10-Q filed with margin change",
            description="Company reported margin change in its quarterly filing.",
        )
        session.add_all([company, source, document, thesis, event])
        session.commit()

        result = score_event(session, event)

    assert result.information_speed == "slow"
    assert result.credibility_score == 85
    assert result.novelty_score == 80
    assert result.impact_score >= 90
    assert 0 <= result.priority_score <= 100
    assert event.information_speed == result.information_speed
    assert event.priority_score == result.priority_score
    assert event.score_explanation_json is not None
    assert "credibility" in event.score_explanation_json
    assert "Primary source" in event.score_explanation_json["credibility"]["factors"]
    assert "priority" in event.score_explanation_json
    assert event.score_explanation_json["priority"]["weights"]["credibility"] == 0.35


def test_score_event_lowers_novelty_for_repeated_recent_company_event_type() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        company = Company(ticker="AAPL", name="Apple")
        source = Source(name="Example News", source_type="news", reliability_score=80)
        old_document = RawDocument(
            company=company,
            source=source,
            document_type="news",
            title="Apple guidance update",
            content_hash="score-event-news-1",
        )
        new_document = RawDocument(
            company=company,
            source=source,
            document_type="news",
            title="Apple guidance update follow-up",
            content_hash="score-event-news-2",
        )
        old_event = Event(
            company=company,
            raw_document=old_document,
            event_type="guidance_change",
            information_speed="medium",
            title="Apple guidance update",
            created_at=datetime.now(UTC) - timedelta(days=1),
        )
        repeated_event = Event(
            company=company,
            raw_document=new_document,
            event_type="guidance_change",
            information_speed="medium",
            title="Apple guidance update follow-up",
        )
        session.add_all([company, source, old_document, new_document, old_event, repeated_event])
        session.commit()

        result = score_event(session, repeated_event)

    assert result.novelty_score == 45


def test_score_alert_derives_confidence_and_severity_from_event_scores() -> None:
    event = Event(
        event_type="guidance_change",
        information_speed="medium",
        title="Guidance reduced",
        credibility_score=72,
        priority_score=83,
    )
    alert = Alert(event=event, alert_type="priority_event", title="Review: Guidance reduced")

    result = score_alert(alert)

    assert result.confidence_bucket == "high"
    assert result.severity == "high"
    assert alert.confidence_bucket == "high"
    assert alert.severity == "high"
