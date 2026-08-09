from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Event
from app.models.thesis_note import EventThesisImpact, ThesisAssumption, ThesisNote


class ThesisEvidenceEngine:
    """
    Engine to detect evidence that supports or contradicts active thesis assumptions.
    In a fully realized system, this would use an AI inference layer to parse the text of an
    event and compare it against the structured thesis assumptions.
    """

    @staticmethod
    def detect_contradictions(db: Session, event_id: int, thesis_id: int) -> List[EventThesisImpact]:
        """
        Analyzes an event against a thesis to detect any contradictory evidence.
        """
        event = db.scalar(select(Event).where(Event.id == event_id))
        thesis = db.scalar(select(ThesisNote).where(ThesisNote.id == thesis_id))

        if not event or not thesis:
            return []

        assumptions = db.scalars(
            select(ThesisAssumption).where(
                ThesisAssumption.thesis_note_id == thesis.id,
                ThesisAssumption.status == "active"
            )
        ).all()

        impacts = []

        # MOCK IMPLEMENTATION:
        # In a real system, we would prompt an LLM:
        # "Does the following event: {event.content} contradict any of these assumptions: {assumptions}?"
        # For now, we will create a mock contradiction if the event text contains "decline" or "miss".

        event_text = (event.title or "") + " " + (event.description or "")
        event_text = event_text.lower()

        if "decline" in event_text or "miss" in event_text:
            for assumption in assumptions:
                # Mock a contradiction
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
                    rationale="The event text contains negative keywords ('decline' or 'miss') which may weaken this assumption.",
                    claim="Mock claim: Management guides lower.",
                    importance="high",
                    confidence="medium",
                    review_status="unreviewed"
                )
                db.add(impact)
                impacts.append(impact)

        db.commit()
        return impacts

    @staticmethod
    def detect_confirmations(db: Session, event_id: int, thesis_id: int) -> List[EventThesisImpact]:
        """
        Analyzes an event against a thesis to detect any confirming evidence.
        """
        event = db.scalar(select(Event).where(Event.id == event_id))
        thesis = db.scalar(select(ThesisNote).where(ThesisNote.id == thesis_id))

        if not event or not thesis:
            return []

        assumptions = db.scalars(
            select(ThesisAssumption).where(
                ThesisAssumption.thesis_note_id == thesis.id,
                ThesisAssumption.status == "active"
            )
        ).all()

        impacts = []

        # MOCK IMPLEMENTATION:
        event_text = (event.title or "") + " " + (event.description or "")
        event_text = event_text.lower()

        if "grow" in event_text or "beat" in event_text:
            for assumption in assumptions:
                # Mock a confirmation
                existing = db.scalar(
                    select(EventThesisImpact).where(
                        EventThesisImpact.event_id == event.id,
                        EventThesisImpact.thesis_assumption_id == assumption.id,
                        EventThesisImpact.impact_classification == "Supports",
                    )
                )
                if existing is not None:
                    impacts.append(existing)
                    continue
                impact = EventThesisImpact(
                    event_id=event.id,
                    thesis_assumption_id=assumption.id,
                    impact_classification="Supports",
                    rationale="The event text contains positive keywords ('grow' or 'beat') which may support this assumption.",
                    claim="Mock claim: Management reported growth.",
                    importance="high",
                    confidence="medium",
                    review_status="unreviewed"
                )
                db.add(impact)
                impacts.append(impact)

        db.commit()
        return impacts
