from app.models import Company, Event
from app.models.thesis_note import ThesisAssumption, ThesisNote
from app.services.thesis_evidence_engine import ThesisEvidenceEngine


def _records(db):
    company = Company(ticker="RULE", name="Rule Test")
    thesis = ThesisNote(
        company=company,
        title="Margin thesis",
        thesis_text="Margins should remain durable.",
        status="active",
    )
    matching = ThesisAssumption(
        thesis_note=thesis,
        description="Pricing supports margins",
        falsification_trigger="gross margin declines below 30 percent",
        status="active",
    )
    no_trigger = ThesisAssumption(
        thesis_note=thesis,
        description="Distribution remains broad",
        status="active",
    )
    event = Event(
        company=company,
        event_type="filing",
        information_speed="fast",
        title="Quarterly margin update",
        description="Gross margin declined below 30 percent during the quarter.",
    )
    db.add_all([company, thesis, matching, no_trigger, event])
    db.commit()
    return thesis, matching, event


def test_detector_uses_explicit_falsification_trigger_and_source_text(db):
    thesis, assumption, event = _records(db)

    impacts = ThesisEvidenceEngine.detect_contradictions(db, event.id, thesis.id)

    assert len(impacts) == 1
    assert impacts[0].thesis_assumption_id == assumption.id
    assert impacts[0].impact_classification == "Weakens"
    assert impacts[0].claim == f"{event.title} {event.description}"
    assert impacts[0].confidence == "low"
    assert "user-authored falsification trigger" in impacts[0].rationale
    assert ThesisEvidenceEngine.detect_confirmations(db, event.id, thesis.id) == []


def test_detector_does_not_invent_claims_without_trigger_match(db):
    thesis, _, event = _records(db)
    event.description = "Revenue beat expectations and distribution grew."
    db.commit()

    assert ThesisEvidenceEngine.detect_contradictions(db, event.id, thesis.id) == []


def test_detector_is_idempotent(db):
    thesis, _, event = _records(db)

    first = ThesisEvidenceEngine.detect_contradictions(db, event.id, thesis.id)
    second = ThesisEvidenceEngine.detect_contradictions(db, event.id, thesis.id)

    assert [impact.id for impact in first] == [impact.id for impact in second]
