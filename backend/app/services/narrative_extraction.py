from dataclasses import dataclass
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.narrative import NarrativeClaim, NarrativeCluster, NarrativeMention
from app.services.ai_contract import AIProvenance, execute_ai_generation


NARRATIVE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "cluster_name": {"type": "STRING"},
        "claim_text": {"type": "STRING"},
        "context_text": {"type": "STRING"},
    },
    "required": ["cluster_name", "claim_text", "context_text"],
}


@dataclass(frozen=True)
class NarrativeExtractionResult:
    created_clusters: int
    created_claims: int
    created_mentions: int
    skipped_existing: int


def extract_narratives_from_events(
    db: Session,
    *,
    user_id: str,
    limit: int | None = 100,
) -> NarrativeExtractionResult:
    query = (
        select(Event)
        .outerjoin(NarrativeMention, Event.id == NarrativeMention.event_id)
        .where(NarrativeMention.id.is_(None))
        .order_by(Event.id)
    )
    if limit is not None:
        query = query.limit(limit)
    events = list(db.scalars(query))

    created_clusters = 0
    created_claims = 0
    created_mentions = 0
    for event in events:
        input_text = f"Title: {event.title}\nDescription: {event.description or ''}"
        prompt = (
            "Extract one primary market narrative from the supplied event. Use only "
            "the supplied event text and return the requested JSON fields.\n\n"
            f"{input_text}"
        )

        def generate(provider):
            result = provider.generate_structured_response(prompt, NARRATIVE_SCHEMA)
            parsed = json.loads(result.output_text)
            if not all(parsed.get(field) for field in NARRATIVE_SCHEMA["required"]):
                raise ValueError("AI narrative response omitted required fields")
            return result

        output = execute_ai_generation(
            db,
            provenance=AIProvenance(
                user_id=user_id,
                prompt_version="v1.1.0-narrative-extraction-contract",
                input_text=prompt,
                reference_type="event",
                reference_id=event.id,
                source_ids=(f"event:{event.id}",),
                source_scope="event_title_and_description",
                external_data_classes=("event_text",),
            ),
            generate=generate,
        )
        parsed = json.loads(output.output_text)
        cluster_name = parsed["cluster_name"]
        claim_text = parsed["claim_text"]
        context_text = parsed["context_text"]
        if output.is_mock and not cluster_name.startswith("Mock Data:"):
            cluster_name = f"Mock Data: {cluster_name}"
            claim_text = f"Mock Data: {claim_text}"
            context_text = f"Mock Data: {context_text}"

        cluster = db.scalar(
            select(NarrativeCluster).where(NarrativeCluster.name == cluster_name)
        )
        if cluster is None:
            cluster = NarrativeCluster(
                name=cluster_name,
                description=f"Narrative related to {cluster_name}",
            )
            db.add(cluster)
            db.flush()
            created_clusters += 1

        claim = db.scalar(
            select(NarrativeClaim).where(
                NarrativeClaim.cluster_id == cluster.id,
                NarrativeClaim.claim_text == claim_text,
            )
        )
        if claim is None:
            db.add(NarrativeClaim(cluster_id=cluster.id, claim_text=claim_text))
            db.flush()
            created_claims += 1

        db.add(
            NarrativeMention(
                cluster_id=cluster.id,
                event_id=event.id,
                context_text=context_text,
            )
        )
        created_mentions += 1
        db.commit()

    return NarrativeExtractionResult(
        created_clusters,
        created_claims,
        created_mentions,
        0,
    )
