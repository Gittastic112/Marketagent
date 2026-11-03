"""Optional as-generated research context; old brief payloads remain valid."""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.brief_triage import BriefReviewRead, BriefTriageSource


class BriefResearchSource(BaseModel):
    source: BriefTriageSource
    content_hash: str
    freshness: Literal["historical", "dated_today", "unknown"]
    claim_type: Literal["AI Interpretation"] = "AI Interpretation"
    href: str


class BriefResearchDecision(BaseModel):
    company_id: int
    ticker: str
    field: str
    comparison_hash: str
    comparability_status: Literal["same", "unknown", "incompatible"]
    source_ids: list[int]
    receipt: BriefReviewRead | None = None
    state: Literal["reviewed", "pending_ai_review", "missing_receipt", "stale_receipt", "incompatible_basis", "incomplete_source_snapshot"]
    href: str


class BriefResearchContext(BaseModel):
    version: Literal["private-research-snapshot-v1"] = "private-research-snapshot-v1"
    captured_at: datetime
    as_of_date: date
    status: Literal["empty", "partial", "complete"]
    basis: Literal["as_generated"] = "as_generated"
    input_sha256: str
    company_count: int
    company_limit: int
    source_limit: int
    decision_limit: int
    excluded: dict[str, int] = Field(default_factory=dict)
    sources: list[BriefResearchSource] = Field(default_factory=list)
    reviewed: list[BriefResearchDecision] = Field(default_factory=list)
    review_queue: list[BriefResearchDecision] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
