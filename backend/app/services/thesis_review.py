"""Record owned evidence-review decisions without altering the evidence or thesis."""
from fastapi import HTTPException
from sqlalchemy import select

from app.models.thesis_note import EventThesisImpact, ThesisAssumption, ThesisChange, ThesisNote


def review_thesis_impact(db, impact_id, user_id, payload):
    impact = db.scalar(select(EventThesisImpact)
        .join(ThesisAssumption, ThesisAssumption.id == EventThesisImpact.thesis_assumption_id)
        .join(ThesisNote, ThesisNote.id == ThesisAssumption.thesis_note_id)
        .where(EventThesisImpact.id == impact_id, ThesisNote.user_id == user_id)
        .with_for_update(of=EventThesisImpact).execution_options(populate_existing=True))
    if impact is None:
        raise HTTPException(status_code=404, detail="Thesis impact not found")
    if impact.review_status != payload.expected_status:
        raise HTTPException(status_code=409, detail="This evidence review changed. Reload it before recording a decision.")
    before = impact.review_status
    impact.review_status = "reviewed" if payload.decision == "no_change" else "needs_review"
    db.add(ThesisChange(thesis_note_id=impact.thesis_assumption.thesis_note_id, drift_score=0,
        change_summary=(f"Evidence review: impact {impact.id}, event {impact.event_id}, assumption {impact.thesis_assumption_id}. "
            f"Decision: {payload.decision}. State: {before} -> {impact.review_status}. "
            f"Reason: {payload.reason.strip()}\nOriginal interpretation ({impact.impact_classification}): {impact.rationale}\n"
            "Thesis text, confidence, financial facts and valuation inputs were not changed.")))
    db.commit()
    db.refresh(impact)
    return impact
