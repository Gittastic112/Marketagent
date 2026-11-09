"""Research API contracts, independent of HTTP and persistence."""

from app.schemas.ai import (
    AiOutputRead,
)

from datetime import (
    datetime,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from typing import (
    Any,
    Literal,
)


class SummarizeRequest(BaseModel):
    document_id: int = Field(gt=0)
    user_task: str = Field(min_length=1, max_length=20000)
    privacy_disclosure_version: str | None = None


class QuestionRequest(BaseModel):
    document_id: int = Field(gt=0)
    user_question: str = Field(min_length=1, max_length=20000)
    privacy_disclosure_version: str | None = None


class MapEventRequest(BaseModel):
    event_text: str = Field(min_length=1, max_length=20000)
    event_id: int | None = Field(default=None, gt=0)
    privacy_disclosure_version: str | None = None


class ThesisNoteCreate(BaseModel):
    company_id: int
    title: str
    thesis_text: str
    assumptions_json: dict[str, Any] | None = None
    status: str = "active"


class ThesisNoteUpdate(BaseModel):
    company_id: int | None = None
    title: str | None = None
    thesis_text: str | None = None
    assumptions_json: dict[str, Any] | None = None
    status: str | None = None


class ThesisAssumptionCreate(BaseModel):
    thesis_note_id: int
    description: str
    category: str | None = Field(default=None, max_length=100)
    importance: str | None = Field(default="medium", max_length=40)
    falsification_trigger: str | None = Field(default=None, max_length=20_000)
    original_confidence: str = "medium"
    current_confidence: str = "medium"


class ThesisAssumptionUpdate(BaseModel):
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    importance: str | None = Field(default=None, max_length=40)
    falsification_trigger: str | None = Field(default=None, max_length=20_000)
    original_confidence: str | None = None
    current_confidence: str | None = None


class EventThesisImpactCreate(BaseModel):
    event_id: int
    thesis_assumption_id: int
    impact_classification: str
    rationale: str


class EventThesisImpactRead(EventThesisImpactCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class ThesisAssumptionRead(ThesisAssumptionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    impacts: list[EventThesisImpactRead] = Field(default_factory=list)


class ThesisChangeCreate(BaseModel):
    thesis_note_id: int
    change_summary: str
    drift_score: float = 0.0


class ThesisChangeRead(ThesisChangeCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ThesisNoteRead(ThesisNoteCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    thesis_drift_score: float
    created_at: datetime
    updated_at: datetime
    assumptions: list[ThesisAssumptionRead] = Field(default_factory=list)
    changes: list[ThesisChangeRead] = Field(default_factory=list)


class SocialPostCreate(BaseModel):
    platform: str
    source_url: str
    author: str | None = None
    raw_text: str
    published_at: datetime | None = None
    payload_json: dict[str, Any] | list[Any] | None = None


class SocialPostUpdate(BaseModel):
    platform: str | None = None
    source_url: str | None = None
    author: str | None = None
    raw_text: str | None = None
    published_at: datetime | None = None
    payload_json: dict[str, Any] | list[Any] | None = None


class SocialPostRead(SocialPostCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content_hash: str
    created_at: datetime
    updated_at: datetime


class SentimentScoreCreate(BaseModel):
    post_id: int | None = None
    company_id: int | None = None
    score: str
    rationale: str | None = None


class SentimentScoreUpdate(BaseModel):
    post_id: int | None = None
    company_id: int | None = None
    score: str | None = None
    rationale: str | None = None


class SentimentScoreRead(SentimentScoreCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class NarrativeClusterCreate(BaseModel):
    name: str
    description: str | None = None


class NarrativeClusterUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class NarrativeClusterRead(NarrativeClusterCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class NarrativeClaimCreate(BaseModel):
    cluster_id: int
    claim_text: str


class NarrativeClaimUpdate(BaseModel):
    cluster_id: int | None = None
    claim_text: str | None = None


class NarrativeClaimRead(NarrativeClaimCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class NarrativeMentionCreate(BaseModel):
    cluster_id: int
    event_id: int
    context_text: str | None = None


class NarrativeMentionUpdate(BaseModel):
    cluster_id: int | None = None
    event_id: int | None = None
    context_text: str | None = None


class NarrativeMentionRead(NarrativeMentionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ResearchMessageCreate(BaseModel):
    role: Literal["user"] = "user"
    content: str = Field(min_length=1, max_length=20_000)
    privacy_disclosure_version: str


class CitationSchema(BaseModel):
    source_id: str
    quote: str | None = None
    start_char: int | None = None
    end_char: int | None = None
    status: Literal["valid", "invalid", "partial", "not_evaluated"] = "not_evaluated"
    reason: str | None = None
    internal_href: str | None = None


class ResearchAiOutputRead(AiOutputRead):
    """Full review contract so research responses use the same approval gates as document AI."""


class ResearchMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime
    ai_output_id: int | None = None
    ai_output: ResearchAiOutputRead | None = None


class ResearchSessionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class ResearchSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class ResearchSessionDetail(ResearchSessionRead):
    messages: list[ResearchMessageRead] = Field(default_factory=list)


class VariantPerceptionCreate(BaseModel):
    company_id: int = Field(gt=0)
    market_belief: str
    my_belief: str
    evidence_for_my_belief: str | None = None
    evidence_against_my_belief: str | None = None
    how_price_reflects_market_belief: str | None = None
    what_would_close_the_gap: str | None = None
    confidence: str = "medium"


class VariantPerceptionUpdate(BaseModel):
    market_belief: str | None = None
    my_belief: str | None = None
    evidence_for_my_belief: str | None = None
    evidence_against_my_belief: str | None = None
    how_price_reflects_market_belief: str | None = None
    what_would_close_the_gap: str | None = None
    confidence: str | None = None


class VariantPerceptionRead(VariantPerceptionCreate):
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DecisionLogCreate(BaseModel):
    company_id: int
    decision_type: str
    rationale: str
    price_at_time: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    emotional_state: str | None = None
    alternatives_considered: str | None = None


class DecisionLogUpdate(BaseModel):
    decision_type: str | None = None
    rationale: str | None = None
    price_at_time: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    emotional_state: str | None = None
    alternatives_considered: str | None = None


class OutcomeReviewRead(BaseModel):
    id: int
    what_happened: str
    wrong_assumption: str | None = None
    information_unavailable_or_misinterpreted: bool
    valuation_wrong: bool
    thesis_wrong: bool
    timing_wrong: bool
    sizing_wrong: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DecisionLogRead(DecisionLogCreate):
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime
    outcome_review: OutcomeReviewRead | None = None

    model_config = ConfigDict(from_attributes=True)


class EvidenceLedgerItemCreate(BaseModel):
    company_id: int = Field(gt=0)
    evidence_text: str
    effect: str
    source_link: str | None = None
    confidence: str = "medium"
    date_discovered: datetime | None = None


class EvidenceLedgerItemUpdate(BaseModel):
    evidence_text: str | None = None
    effect: str | None = None
    source_link: str | None = None
    confidence: str | None = None


class EvidenceLedgerItemRead(EvidenceLedgerItemCreate):
    id: int
    company_id: int
    date_discovered: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
