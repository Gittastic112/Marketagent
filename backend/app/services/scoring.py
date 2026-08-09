from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Alert, Event, RawDocument, ThesisNote


SLOW_TERMS = {
    "filing",
    "sec_filing",
    "sec_filing_metadata",
    "annual_report",
    "annual report",
    "10-k",
    "10k",
    "10-q",
    "10q",
    "13f",
    "industry_report",
    "industry report",
}
MEDIUM_TERMS = {
    "earnings",
    "guidance",
    "guidance_change",
    "macro",
    "macro_release",
    "product_launch",
    "management_change",
    "regulatory_action",
}
FAST_TERMS = {
    "breaking",
    "breaking_news",
    "social",
    "social_post",
    "rumor",
    "rumour",
    "sudden price",
    "sudden volume",
    "price move",
    "volume move",
    "rss_news",
}
HIGH_IMPORTANCE_EVENT_TYPES = {
    "earnings",
    "guidance_change",
    "risk_factor_change",
    "regulatory_action",
    "litigation",
    "management_change",
    "major_product_launch",
    "capital_allocation",
    "debt_refinancing",
    "margin_change",
    "revenue_warning",
    "sec_filing",
    "filing_text_change",
}
ALERT_WORTHY_TERMS = {
    "risk",
    "warning",
    "guidance",
    "lawsuit",
    "litigation",
    "regulatory",
    "margin",
    "debt",
    "revenue",
    "earnings",
    "acquisition",
    "launch",
    "downgrade",
    "refinancing",
    "cash flow",
}


@dataclass(frozen=True)
class EventScore:
    information_speed: str
    credibility_score: int
    novelty_score: int
    impact_score: int
    priority_score: int
    explanation: dict[str, Any]


@dataclass(frozen=True)
class AlertScore:
    confidence_bucket: str
    severity: str


def classify_information_speed(event_type: str | None = None, title: str | None = None, document_type: str | None = None) -> str:
    text = _combined_text(event_type, title, document_type)

    if _contains_any(text, SLOW_TERMS):
        return "slow"
    if _contains_any(text, FAST_TERMS):
        return "fast"
    if _contains_any(text, MEDIUM_TERMS):
        return "medium"
    return "medium"


def calculate_credibility_score(event: Event) -> int:
    score = 0
    document = _event_document(event)
    source = document.source if document is not None else None
    payload = _payload(document)

    if _is_primary_source(document):
        score += 30
    if source is not None and ((source.reliability_score or 0) >= 70 or source.source_type in {"sec", "news", "rss"}):
        score += 20
    if document is not None and document.url:
        score += 10
    if document is not None:
        score += 10

    # The schema does not have first-class corroboration or contradiction fields yet.
    # If ingestion later stores those facts in raw_payload_json, this scorer uses them.
    if _numeric_payload_value(payload, "corroboration_count") > 0:
        score += 15
    if payload.get("contradiction_flag") is False:
        score += 15

    return _bound_score(score)


def calculate_novelty_score(db: Session | None, event: Event) -> int:
    if db is None:
        return 70 if event.raw_document_id else 60

    if event.raw_document_id and _count_matching_events(db, event, raw_document_id=event.raw_document_id) > 0:
        return 10

    if event.company_id and _count_matching_events(db, event, company_id=event.company_id, event_type=event.event_type) > 0:
        return 45

    if event.company_id and _count_matching_events(db, event, company_id=event.company_id) == 0:
        return 80

    if event.raw_document_id:
        return 70

    return 60


def calculate_impact_score(db: Session | None, event: Event, credibility_score: int | None = None) -> int:
    score = 0
    document = _event_document(event)
    text = _combined_text(event.event_type, event.title, event.description, document.document_type if document else None)

    if event.company_id is not None:
        score += 20
    if db is not None and event.company_id is not None and _has_active_thesis_note(db, event.company_id):
        score += 20
    if event.event_type in HIGH_IMPORTANCE_EVENT_TYPES or _contains_any(text, HIGH_IMPORTANCE_EVENT_TYPES):
        score += 25
    if _contains_any(text, ALERT_WORTHY_TERMS):
        score += 15
    if _is_recent(event, document):
        score += 10
    if (credibility_score or 0) >= 70:
        score += 10

    return _bound_score(score)


def calculate_priority_score(
    db: Session | None = None,
    credibility_score: int | None = None,
    novelty_score: int | None = None,
    impact_score: int | None = None,
    information_speed: str | None = None,
) -> int:
    speed_bonus = {"slow": 60, "medium": 75, "fast": 80}.get(information_speed or "medium", 75)

    w_credibility = 0.35
    w_novelty = 0.25
    w_impact = 0.35
    w_speed = 0.05

    if db is not None:
        from app.models.scoring_config import ScoringConfig
        config = db.scalar(select(ScoringConfig).order_by(ScoringConfig.id).limit(1))
        if config:
            w_credibility = config.weight_credibility
            w_novelty = config.weight_novelty
            w_impact = config.weight_impact
            w_speed = config.weight_speed

    score = (
        (credibility_score or 0) * w_credibility
        + (novelty_score or 0) * w_novelty
        + (impact_score or 0) * w_impact
        + speed_bonus * w_speed
    )
    return _bound_score(round(score))


def get_confidence_bucket(score: int | None) -> str:
    bounded = _bound_score(score or 0)
    if bounded >= 70:
        return "high"
    if bounded >= 40:
        return "medium"
    return "low"


def score_event(db: Session | None, event: Event) -> EventScore:
    document = _event_document(event)
    information_speed = classify_information_speed(
        event_type=event.event_type,
        title=event.title,
        document_type=document.document_type if document else None,
    )
    credibility_score = calculate_credibility_score(event)
    novelty_score = calculate_novelty_score(db, event)
    impact_score = calculate_impact_score(db, event, credibility_score)
    priority_score = calculate_priority_score(db, credibility_score, novelty_score, impact_score, information_speed)
    explanation = explain_event_score(db, event, information_speed, credibility_score, novelty_score, impact_score, priority_score)

    event.information_speed = information_speed
    event.credibility_score = credibility_score
    event.novelty_score = novelty_score
    event.impact_score = impact_score
    event.priority_score = priority_score
    event.score_explanation_json = explanation

    return EventScore(
        information_speed=information_speed,
        credibility_score=credibility_score,
        novelty_score=novelty_score,
        impact_score=impact_score,
        priority_score=priority_score,
        explanation=explanation,
    )


def explain_event_score(
    db: Session | None,
    event: Event,
    information_speed: str,
    credibility_score: int,
    novelty_score: int,
    impact_score: int,
    priority_score: int,
) -> dict[str, Any]:
    w_credibility = 0.35
    w_novelty = 0.25
    w_impact = 0.35
    w_speed = 0.05

    if db is not None:
        from app.models.scoring_config import ScoringConfig
        config = db.scalar(select(ScoringConfig).order_by(ScoringConfig.id).limit(1))
        if config:
            w_credibility = config.weight_credibility
            w_novelty = config.weight_novelty
            w_impact = config.weight_impact
            w_speed = config.weight_speed

    return {
        "information_speed": {
            "value": information_speed,
            "factors": _information_speed_factors(event, information_speed),
        },
        "credibility": {
            "score": credibility_score,
            "factors": _credibility_factors(event),
        },
        "novelty": {
            "score": novelty_score,
            "factors": _novelty_factors(db, event, novelty_score),
        },
        "impact": {
            "score": impact_score,
            "factors": _impact_factors(db, event, credibility_score),
        },
        "priority": {
            "score": priority_score,
            "formula": f"credibility * {w_credibility} + novelty * {w_novelty} + impact * {w_impact} + speed_bonus * {w_speed}",
            "weights": {"credibility": w_credibility, "novelty": w_novelty, "impact": w_impact, "speed_bonus": w_speed},
            "speed_bonus": {"slow": 60, "medium": 75, "fast": 80}.get(information_speed, 75),
        },
    }


def score_alert(alert: Alert) -> AlertScore:
    priority_score = alert.event.priority_score if alert.event else None
    credibility_score = alert.event.credibility_score if alert.event else None
    severity = _severity_for_priority(priority_score)
    confidence_bucket = get_confidence_bucket(credibility_score)

    alert.severity = severity
    alert.confidence_bucket = confidence_bucket

    return AlertScore(confidence_bucket=confidence_bucket, severity=severity)


def _information_speed_factors(event: Event, information_speed: str) -> list[str]:
    document = _event_document(event)
    factors = [f"Classified as {information_speed} information"]
    if document is not None:
        factors.append(f"Document type: {document.document_type}")
    if event.event_type:
        factors.append(f"Event type: {event.event_type}")
    return factors


def _credibility_factors(event: Event) -> list[str]:
    document = _event_document(event)
    source = document.source if document is not None else None
    payload = _payload(document)
    factors: list[str] = []
    if _is_primary_source(document):
        factors.append("Primary source")
    if source is not None and ((source.reliability_score or 0) >= 70 or source.source_type in {"sec", "news", "rss"}):
        factors.append("Reputable source")
    if document is not None and document.url:
        factors.append("Source URL exists")
    if document is not None:
        factors.append("Raw document exists")
    if _numeric_payload_value(payload, "corroboration_count") > 0:
        factors.append("Corroboration count available")
    if payload.get("contradiction_flag") is False:
        factors.append("No contradiction flag")
    return factors or ["No source evidence available"]


def _novelty_factors(db: Session | None, event: Event, novelty_score: int) -> list[str]:
    if db is None:
        return ["No database context available for novelty comparison"]
    if novelty_score == 10:
        return ["Existing event already links to this raw document"]
    if novelty_score == 45:
        return ["Similar event type already exists for this company"]
    if novelty_score == 80:
        return ["First stored event for this company"]
    if event.raw_document_id:
        return ["New raw document"]
    return ["No raw document link available"]


def _impact_factors(db: Session | None, event: Event, credibility_score: int | None = None) -> list[str]:
    document = _event_document(event)
    text = _combined_text(event.event_type, event.title, event.description, document.document_type if document else None)
    factors: list[str] = []
    if event.company_id is not None:
        factors.append("Linked to tracked company")
    if db is not None and event.company_id is not None and _has_active_thesis_note(db, event.company_id):
        factors.append("Linked company has active thesis note")
    if event.event_type in HIGH_IMPORTANCE_EVENT_TYPES or _contains_any(text, HIGH_IMPORTANCE_EVENT_TYPES):
        factors.append("High-importance event type")
    if _contains_any(text, ALERT_WORTHY_TERMS):
        factors.append("Alert-worthy language")
    if _is_recent(event, document):
        factors.append("Recent event")
    if (credibility_score or 0) >= 70:
        factors.append("High-credibility source")
    return factors or ["No high-impact factors matched"]


def _severity_for_priority(priority_score: int | None) -> str:
    score = priority_score or 0
    if score >= 80:
        return "high"
    if score >= 70:
        return "medium"
    return "low"


def _bound_score(score: int | float) -> int:
    return max(0, min(100, int(score)))


def _combined_text(*values: object) -> str:
    return " ".join(str(value).lower().replace("_", " ") for value in values if value)


def _contains_any(text: str, terms: set[str]) -> bool:
    normalized_terms = {term.lower().replace("_", " ") for term in terms}
    return any(term in text for term in normalized_terms)


def _event_document(event: Event) -> RawDocument | None:
    return event.raw_document


def _payload(document: RawDocument | None) -> dict[str, Any]:
    if document is None or not isinstance(document.raw_payload_json, dict):
        return {}
    return document.raw_payload_json


def _numeric_payload_value(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int | float):
        return int(value)
    return 0


def _is_primary_source(document: RawDocument | None) -> bool:
    if document is None:
        return False
    source_type = document.source.source_type if document.source else ""
    return source_type in {"sec", "filing", "company", "manual"} or document.document_type in {
        "sec_filing_metadata",
        "filing",
        "annual_report",
    }


def _count_matching_events(
    db: Session,
    event: Event,
    *,
    raw_document_id: int | None = None,
    company_id: int | None = None,
    event_type: str | None = None,
) -> int:
    query = select(Event.id)
    if raw_document_id is not None:
        query = query.where(Event.raw_document_id == raw_document_id)
    if company_id is not None:
        query = query.where(Event.company_id == company_id)
    if event_type is not None:
        query = query.where(Event.event_type == event_type)
    if event.id is not None:
        query = query.where(Event.id != event.id)
    with db.no_autoflush:
        return len(list(db.scalars(query.limit(2))))


def _has_active_thesis_note(db: Session, company_id: int) -> bool:
    query = select(ThesisNote.id).where(ThesisNote.company_id == company_id, ThesisNote.status == "active").limit(1)
    with db.no_autoflush:
        return db.scalar(query) is not None


def _is_recent(event: Event, document: RawDocument | None) -> bool:
    timestamp = event.event_time or (document.published_at if document else None) or event.created_at
    if timestamp is None:
        return False
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return timestamp >= datetime.now(UTC) - timedelta(days=30)
