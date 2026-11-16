"""Claim origin is shared with the claim; complete AI output remains owner-only."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai import AiOutput
from app.models.narrative import NarrativeClaim


def claims_with_origin(db: Session, claims: list[NarrativeClaim], user_id: str) -> list[dict]:
    identities = {claim.ai_output_id for claim in claims if claim.ai_output_id is not None}
    outputs = {output.id: output for output in db.scalars(select(AiOutput).where(
        AiOutput.id.in_(identities), AiOutput.user_id == user_id))} if identities else {}
    return [{"id": claim.id, "cluster_id": claim.cluster_id, "claim_text": claim.claim_text,
        "created_at": claim.created_at, "origin": claim.origin or "legacy_unknown",
        "ai_output": outputs.get(claim.ai_output_id)} for claim in claims]
