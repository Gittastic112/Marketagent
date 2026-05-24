from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Alert, DailyBrief, Event, ThesisNote


def generate_daily_brief(db: Session, brief_date: date | None = None, limit: int = 10) -> dict[str, Any]:
    events = list(
        db.scalars(
            select(Event)
            .options(
                selectinload(Event.company),
                selectinload(Event.raw_document).selectinload("*"),
            )
            .order_by(Event.priority_score.desc().nullslast(), Event.created_at.desc())
            .limit(limit)
        )
    )
    alerts = list(
        db.scalars(
            select(Alert)
            .options(selectinload(Alert.company), selectinload(Alert.event))
            .order_by(Alert.created_at.desc())
            .limit(limit)
        )
    )
    thesis_notes = list(db.scalars(select(ThesisNote).where(ThesisNote.status == "active")))

    brief_day = brief_date or date.today()

    return {
        "title": "Daily Intelligence Brief",
        "date": brief_day.isoformat(),
        "summary": f"{len(events)} events, {len(alerts)} alerts, {len(thesis_notes)} active thesis notes reviewed.",
        "top_events": [_event_to_brief_item(event) for event in events],
        "alerts": [_alert_to_brief_item(alert) for alert in alerts],
        "follow_up_questions": [
            "Does this change any active thesis assumption?",
            "What source would confirm or falsify the interpretation?",
            "Is this new information or repeated noise?",
        ],
    }


def save_daily_brief(db: Session, brief_date: date | None = None, limit: int = 10) -> DailyBrief:
    payload = generate_daily_brief(db, brief_date=brief_date, limit=limit)
    record = DailyBrief(
        brief_date=date.fromisoformat(payload["date"]),
        title=payload["title"],
        summary=payload["summary"],
        payload_json=payload,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _event_to_brief_item(event: Event) -> dict[str, Any]:
    raw_document = event.raw_document
    source = raw_document.source if raw_document is not None else None

    return {
        "id": event.id,
        "company": event.company.ticker if event.company is not None else None,
        "title": event.title,
        "event_type": event.event_type,
        "information_speed": event.information_speed,
        "description": event.description,
        "credibility_score": event.credibility_score,
        "novelty_score": event.novelty_score,
        "impact_score": event.impact_score,
        "priority_score": event.priority_score,
        "source": source.name if source is not None else None,
        "source_url": raw_document.url if raw_document is not None else None,
    }


def _alert_to_brief_item(alert: Alert) -> dict[str, Any]:
    return {
        "id": alert.id,
        "company": alert.company.ticker if alert.company is not None else None,
        "title": alert.title,
        "severity": alert.severity,
        "confidence_bucket": alert.confidence_bucket,
        "review_status": alert.review_status,
        "summary": alert.summary,
    }
