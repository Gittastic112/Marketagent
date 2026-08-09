import re
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Event
from app.models.thesis_note import EventThesisImpact, ThesisAssumption, ThesisNote


_STOP_WORDS = {
    "about", "after", "again", "against", "below", "could", "from", "have",
    "into", "more", "over", "should", "than", "that", "their", "there", "these",
    "they", "this", "through", "under", "when", "where", "which", "with", "would",
}


def _material_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.casefold())
        if len(token) >= 4 and token not in _STOP_WORDS
    }


def _trigger_matches(trigger: str, evidence: str) -> tuple[bool, list[str]]:
    normalized_trigger = " ".join(trigger.casefold().split())
    normalized_evidence = " ".join(evidence.casefold().split())
    if normalized_trigger and normalized_trigger in normalized_evidence:
        return True, sorted(_material_tokens(trigger))

    trigger_tokens = _material_tokens(trigger)
    if len(trigger_tokens) < 2:
        return False, []
    matched = sorted(trigger_tokens.intersection(_material_tokens(evidence)))
    required = max(2, (len(trigger_tokens) + 1) // 2)
    return len(matched) >= required, matched


class ThesisEvidenceEngine:
    """Create review candidates from explicit user-authored falsification triggers."""

    @staticmethod
    def detect_contradictions(
        db: Session,
        event_id: int,
        thesis_id: int,
    ) -> list[EventThesisImpact]:
        event = db.scalar(select(Event).where(Event.id == event_id))
        thesis = db.scalar(select(ThesisNote).where(ThesisNote.id == thesis_id))
        if event is None or thesis is None or event.company_id != thesis.company_id:
            return []

        evidence = " ".join(part for part in (event.title, event.description) if part).strip()
        if not evidence:
            return []

        assumptions: Iterable[ThesisAssumption] = db.scalars(
            select(ThesisAssumption).where(
                ThesisAssumption.thesis_note_id == thesis.id,
                ThesisAssumption.status == "active",
                ThesisAssumption.falsification_trigger.is_not(None),
            )
        ).all()

        impacts: list[EventThesisImpact] = []
        for assumption in assumptions:
            trigger = (assumption.falsification_trigger or "").strip()
            matches, terms = _trigger_matches(trigger, evidence)
            if not matches:
                continue
            existing = db.scalar(
                select(EventThesisImpact).where(
                    EventThesisImpact.event_id == event.id,
                    EventThesisImpact.thesis_assumption_id == assumption.id,
                    EventThesisImpact.impact_classification == "Weakens",
                )
            )
            if existing is not None:
                impacts.append(existing)
                continue
            impact = EventThesisImpact(
                event_id=event.id,
                thesis_assumption_id=assumption.id,
                impact_classification="Weakens",
                rationale=(
                    "Deterministic candidate: stored event evidence overlaps the user-authored "
                    f"falsification trigger on these terms: {', '.join(terms)}. User review is required."
                ),
                claim=evidence,
                importance=assumption.importance or "medium",
                confidence="low",
                review_status="unreviewed",
            )
            db.add(impact)
            impacts.append(impact)

        db.commit()
        for impact in impacts:
            if impact.id is not None:
                db.refresh(impact)
        return impacts

    @staticmethod
    def detect_confirmations(
        db: Session,
        event_id: int,
        thesis_id: int,
    ) -> list[EventThesisImpact]:
        # A falsification trigger can identify a weakening candidate. It cannot
        # establish confirmation without a separate user-authored support rule.
        return []
