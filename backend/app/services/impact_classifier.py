import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai import AiOutput
from app.models.event import Event
from app.models.thesis_note import ThesisNote
from app.services.ai_contract import AIProvenance, execute_ai_generation


IMPACT_CLASSIFIER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "impacts": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "thesis_assumption_id": {"type": "INTEGER"},
                    "impact_classification": {"type": "STRING"},
                    "rationale": {"type": "STRING"},
                },
                "required": [
                    "thesis_assumption_id",
                    "impact_classification",
                    "rationale",
                ],
            },
        }
    },
    "required": ["impacts"],
}


def classify_event_impact(
    db: Session,
    event_id: int,
    *,
    user_id: str,
) -> tuple[list[dict], AiOutput | None]:
    event = db.get(Event, event_id)
    if event is None:
        raise ValueError(f"Event {event_id} not found")

    thesis_note = db.scalar(
        select(ThesisNote)
        .where(
            ThesisNote.user_id == user_id,
            ThesisNote.company_id == event.company_id,
            ThesisNote.status == "active",
        )
        .order_by(ThesisNote.created_at.desc(), ThesisNote.id.desc())
    )
    if thesis_note is None or not thesis_note.assumptions:
        return [], None

    assumptions = [
        {
            "id": assumption.id,
            "category": assumption.category,
            "description": assumption.description,
            "falsification_trigger": assumption.falsification_trigger,
        }
        for assumption in thesis_note.assumptions
    ]
    prompt = (
        "Assess whether the supplied event supports, weakens, invalidates, or is "
        "neutral to each supplied thesis assumption. Use only the supplied text, "
        "do not invent evidence, and return the requested JSON.\n\n"
        f"Event title: {event.title}\n"
        f"Event description: {event.description or ''}\n\n"
        f"Thesis assumptions: {json.dumps(assumptions, ensure_ascii=False)}"
    )

    valid_assumption_ids = {assumption.id for assumption in thesis_note.assumptions}

    def generate(provider):
        result = provider.generate_structured_response(prompt, IMPACT_CLASSIFIER_SCHEMA)
        parsed = json.loads(result.output_text)
        for impact in parsed.get("impacts", []):
            if impact.get("thesis_assumption_id") not in valid_assumption_ids:
                raise ValueError("AI impact referenced an assumption outside the source set")
        return result

    output = execute_ai_generation(
        db,
        provenance=AIProvenance(
            user_id=user_id,
            prompt_version="v1.1.0-thesis-impact-contract",
            input_text=prompt,
            reference_type="event",
            reference_id=event.id,
            source_ids=(
                f"event:{event.id}",
                f"thesis_note:{thesis_note.id}",
                *(f"thesis_assumption:{item['id']}" for item in assumptions),
            ),
            source_scope="event_and_owned_active_thesis_assumptions",
            external_data_classes=("event_text", "private_thesis_assumptions"),
        ),
        generate=generate,
    )
    return json.loads(output.output_text).get("impacts", []), output
