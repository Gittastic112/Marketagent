from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models import Alert, Event
from app.services.scoring import score_alert


@dataclass(frozen=True)
class AlertGenerationResult:
    created: int
    skipped_existing: int
    skipped_below_threshold: int


def generate_alerts_from_events(db: Session, priority_threshold: int | None = None, limit: int | None = 100) -> AlertGenerationResult:
    threshold = priority_threshold if priority_threshold is not None else get_settings().alert_priority_threshold
    query = (
        select(Event)
        .options(selectinload(Event.company), selectinload(Event.alerts))
        .order_by(Event.priority_score.desc().nullslast(), Event.id)
    )
    if limit is not None:
        query = query.limit(limit)
    events = list(db.scalars(query))

    created = 0
    skipped_existing = 0
    skipped_below_threshold = 0

    for event in events:
        if (event.priority_score or 0) < threshold:
            skipped_below_threshold += 1
            continue
        if event.alerts:
            skipped_existing += 1
            continue

        db.add(_alert_from_event(event))
        created += 1

    db.commit()
    return AlertGenerationResult(
        created=created,
        skipped_existing=skipped_existing,
        skipped_below_threshold=skipped_below_threshold,
    )


def _alert_from_event(event: Event) -> Alert:
    alert = Alert(
        event=event,
        company=event.company,
        event_id=event.id,
        company_id=event.company_id,
        alert_type="priority_event",
        severity="low",
        title=f"Review: {event.title}",
        summary=event.description,
        why_it_matters="This event passed the rule-based priority threshold.",
        what_changed=event.title,
        evidence=event.description,
        confidence_bucket="low",
        review_status="unreviewed",
    )
    score_alert(alert)
    return alert
