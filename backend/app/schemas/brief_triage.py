"""Source comparison and analyst review contracts, independent of persistence."""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.brief_sources import BriefFinding, ValuationField


class BriefTriageFinding(BriefFinding):
    start_char: int
    end_char: int
    page: int | None


class BriefTriageSource(BaseModel):
    id: int
    title: str
    source_kind: str
    as_of_date: date | None
    source_sha256: str
    created_at: datetime
    ai_output_id: int
    provider: str
    model: str
    prompt_version: str
    input_hash: str
    generated_at: datetime
    is_mock: bool
    review_status: str
    reviewed_at: datetime | None
    lifecycle_version: int
    warnings: list[str]
    findings: list[BriefTriageFinding]


class BriefFindingRef(BaseModel):
    source_id: int
    finding_index: int


class BriefSuggestionRef(BriefFindingRef):
    suggestion_index: int


class BriefTriageGroup(BaseModel):
    field: ValuationField
    label: str
    review_href: str
    status: Literal["opposing_directions", "mixed_within_content", "no_opposition_detected"]
    opposition_basis: list[Literal["stored_sources", "mock_data"]]
    source_count: int
    distinct_content_count: int
    highest_importance: Literal["high", "medium", "low"]
    items: list[BriefSuggestionRef]


class BriefTriageCoverage(BaseModel):
    active_sources: int
    archived_sources: int
    examined_sources: int
    included_sources: int
    not_examined: int
    source_limit: int
    excluded: dict[str, int]


ReviewDisposition = Literal["investigate", "keep_input", "revisit_input", "not_relevant"]


class BriefReviewWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    company_id: int = Field(gt=0, strict=True)
    field: ValuationField
    include_mock: bool = Field(default=False, strict=True)
    evidence_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_version: int = Field(ge=0, strict=True)
    disposition: ReviewDisposition
    notes: str = Field(min_length=10, max_length=2000)
    evidence_reviewed: Literal[True]

    @field_validator("evidence_reviewed", mode="before")
    @classmethod
    def explicit_confirmation(cls, value):
        if value is not True:
            raise ValueError("Explicit evidence review confirmation is required")
        return value

    @field_validator("notes")
    @classmethod
    def no_nulls(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("Review notes must not contain null characters")
        return value


class BriefReviewRead(BaseModel):
    id: int
    company_id: int
    field: ValuationField
    include_mock: bool
    version: int
    evidence_hash: str
    disposition: ReviewDisposition
    notes: str
    created_at: datetime
    is_current: bool
    claim_type: Literal["User Assumption"] = "User Assumption"


class BriefReviewEvidence(BaseModel):
    company_id: int
    company_name: str
    ticker: str
    include_mock: bool
    methodology: str
    compared_at: datetime
    coverage: BriefTriageCoverage
    group: BriefTriageGroup
    sources: list[BriefTriageSource]


class BriefReviewDetail(BriefReviewRead):
    evidence: BriefReviewEvidence


class BriefTriageRead(BaseModel):
    company_id: int
    company_name: str
    ticker: str
    claim_type: Literal["Calculation"] = "Calculation"
    methodology: str = "private-source-direction-comparison-v1"
    computed_at: datetime
    include_mock: bool
    evidence_hash: str = ""
    reviews: list[BriefReviewRead] = Field(default_factory=list)
    coverage: BriefTriageCoverage
    sources: list[BriefTriageSource]
    groups: list[BriefTriageGroup]
    unmapped_findings: list[BriefFindingRef]
    warnings: list[str]
