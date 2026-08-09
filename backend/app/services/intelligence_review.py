from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased, selectinload

from app.models import Event
from app.models.event import EventContradiction
from app.models.sec_parsing import FilingSection, FilingSectionDiff


def _change_severity(added: int, removed: int) -> str:
    changed = added + removed
    if changed >= 250:
        return "high"
    if changed >= 50:
        return "medium"
    return "low"


def build_intelligence_review_queue(
    db: Session,
    *,
    company_id: int | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    source_event = aliased(Event)
    target_event = aliased(Event)
    contradiction_query = (
        select(EventContradiction, source_event, target_event)
        .join(source_event, EventContradiction.source_event_id == source_event.id)
        .join(target_event, EventContradiction.target_event_id == target_event.id)
        .order_by(EventContradiction.created_at.desc())
    )
    if company_id is not None:
        contradiction_query = contradiction_query.where(source_event.company_id == company_id)

    items: list[dict[str, Any]] = []
    for link, source, target in db.execute(contradiction_query.limit(limit)).all():
        items.append({
            "item_type": "contradiction",
            "item_id": f"contradiction:{source.id}:{target.id}",
            "company_id": source.company_id,
            "title": source.title,
            "summary": f"Marked as contradicting: {target.title}",
            "severity": "high",
            "claim_type": "User Assumption",
            "source_event_id": source.id,
            "target_event_id": target.id,
            "evidence_href": f"/events?event_id={source.id}",
            "source_timestamp": link.created_at,
        })

    diff_query = (
        select(FilingSectionDiff)
        .options(
            selectinload(FilingSectionDiff.current_section).selectinload(FilingSection.raw_document),
            selectinload(FilingSectionDiff.prior_section).selectinload(FilingSection.raw_document),
        )
        .where((FilingSectionDiff.added_words + FilingSectionDiff.removed_words) > 0)
        .order_by(FilingSectionDiff.created_at.desc(), FilingSectionDiff.id.desc())
    )
    diffs = list(db.scalars(diff_query.limit(limit)))
    for diff in diffs:
        current_document = diff.current_section.raw_document
        prior_document = diff.prior_section.raw_document if diff.prior_section else None
        if company_id is not None and current_document.company_id != company_id:
            continue
        items.append({
            "item_type": "filing_language_change",
            "item_id": f"filing_diff:{diff.id}",
            "company_id": current_document.company_id,
            "title": f"{diff.current_section.item_name}: filing language changed",
            "summary": f"{diff.added_words} words added and {diff.removed_words} words removed.",
            "severity": _change_severity(diff.added_words, diff.removed_words),
            "claim_type": "Calculation",
            "current_document_id": current_document.id,
            "prior_document_id": prior_document.id if prior_document else None,
            "section_name": diff.current_section.item_name,
            "added_words": diff.added_words,
            "removed_words": diff.removed_words,
            "evidence_href": f"/documents/{current_document.id}/sections?diff={diff.id}",
            "source_timestamp": diff.created_at,
        })
    return sorted(items, key=lambda item: item["source_timestamp"], reverse=True)[:limit]
