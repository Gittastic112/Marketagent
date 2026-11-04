"""Ai API contracts, independent of HTTP and persistence."""

from datetime import (
    datetime,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from typing import (
    Any,
    Literal,
)


class FilingSectionDiffRead(BaseModel):
    id: int
    current_section_id: int
    prior_section_id: int | None = None
    added_words: int
    removed_words: int
    diff_html: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FilingSectionRead(BaseModel):
    id: int
    raw_document_id: int
    item_name: str
    title: str | None = None
    text_content: str
    word_count: int
    created_at: datetime
    updated_at: datetime

    diffs_as_current: list[FilingSectionDiffRead] = []

    model_config = ConfigDict(from_attributes=True)


class AiOutputRead(BaseModel):
    id: int
    consent_decision_id: int | None = None
    raw_document_id: int | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    model_name: str
    provider_name: str
    is_mock: bool
    prompt_version: str
    input_hash: str
    source_ids_json: list[str] = Field(default_factory=list)
    source_scope: str
    citations_json: list[dict[str, Any]] = Field(default_factory=list)
    citation_validation_status: str
    evaluation_json: dict[str, Any] | None = None
    privacy_disclosure_version: str
    external_data_classes_json: list[str] = Field(default_factory=list)
    transmission_scope: str
    execution_status: str
    failure_code: str | None = None
    is_blocked: bool
    output_text: str
    limitations: str | None = None
    confidence_label: str
    human_review_status: str
    review_notes: str | None = None
    reviewer_id: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AiCitationCreate(BaseModel):
    source_id: str = Field(min_length=1, max_length=255)
    quote: str = Field(min_length=1, max_length=2_000)
    start_char: int | None = Field(default=None, ge=0)
    end_char: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_span(self):
        if (self.start_char is None) != (self.end_char is None):
            raise ValueError("start_char and end_char must be provided together")
        if self.start_char is not None and self.end_char <= self.start_char:
            raise ValueError("end_char must be greater than start_char")
        return self


class AiCitationValidationRequest(BaseModel):
    citations: list[AiCitationCreate] = Field(min_length=1, max_length=50)


class AiCitationSuggestionCandidate(BaseModel):
    quote: str = Field(min_length=1, max_length=2_000)
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)
    score: float = Field(ge=0, le=1)
    confidence: Literal["high", "medium", "low"]
    matched_terms: list[str] = Field(default_factory=list)
    claim_term_count: int = Field(ge=0)
    matched_term_count: int = Field(ge=0)
    internal_href: str


class AiCitationSuggestionRead(BaseModel):
    source_id: str
    claim_text: str | None = None
    source_title: str | None = None
    status: Literal[
        "ready",
        "no_candidate",
        "source_text_unavailable",
        "unsupported_source",
        "undeclared_source",
        "claim_text_unavailable",
    ]
    candidates: list[AiCitationSuggestionCandidate] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class AiOutputReviewRequest(BaseModel):
    status: Literal["approved", "rejected", "needs_revision"]
    notes: str | None = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def require_review_notes(self):
        if self.status != "approved" and not (self.notes or "").strip():
            raise ValueError("Review notes are required for rejection or revision")
        return self


class AIPrivacyAcknowledgement(BaseModel):
    privacy_disclosure_version: str
