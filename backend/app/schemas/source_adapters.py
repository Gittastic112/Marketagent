"""Source adapter requests/results, independent of HTTP and persistence."""
from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SourceAdapterModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class SourceAdapterCapability(SourceAdapterModel):
    adapter: str
    available: bool
    status: str
    dependency_version: str | None = None
    warnings: list[str] = Field(default_factory=list)


class SecFactsAdapterRequest(SourceAdapterModel):
    as_of: date | None = None
    max_years: int = Field(default=5, ge=1, le=10)


class IndiaFilingsRequest(SourceAdapterModel):
    exchange: Literal["NSE", "BSE"]
    records: list[dict[str, Any]] = Field(min_length=1, max_length=100)

    @field_validator("records")
    @classmethod
    def bounded_records(cls, value: list[dict]) -> list[dict]:
        if len(json.dumps(value, allow_nan=False).encode()) > 1_000_000:
            raise ValueError("Filing metadata exceeds 1 MB")
        return value


class TranscriptRequest(SourceAdapterModel):
    provider: Literal["earningscall", "fmp"]
    fiscal_year: int = Field(ge=1990, le=2100)
    fiscal_quarter: int = Field(ge=1, le=4)
    exchange: str | None = Field(default=None, pattern=r"^[A-Z0-9_.-]{1,20}$")
    level: int = Field(default=1, ge=1, le=4)


class FredVintageRequest(SourceAdapterModel):
    series_id: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,80}$")
    as_of: date
    observation_start: date
    observation_end: date
    mode: Literal["as_of", "initial_release"] = "as_of"
    max_pages: int = Field(default=5, ge=1, le=10)

    @model_validator(mode="after")
    def ordered_dates(self):
        if self.observation_start > self.observation_end or self.as_of > date.today():
            raise ValueError("Observation dates must be ordered and the cutoff cannot be future dated")
        return self


class DocumentExtractionRequest(SourceAdapterModel):
    adapter: Literal["camelot", "docling", "marker"]
    pages: list[int] = Field(min_length=1, max_length=20)

    @field_validator("pages")
    @classmethod
    def valid_pages(cls, value: list[int]) -> list[int]:
        if any(page < 1 or page > 1000 for page in value):
            raise ValueError("Pages must be between 1 and 1000")
        return sorted(set(value))


class SourceAdapterResult(SourceAdapterModel):
    adapter: str
    processing_run_id: int | None = None
    raw_document_ids: list[int] = Field(default_factory=list)
    candidate_ids: list[int] = Field(default_factory=list)
    fetched_count: int = 0
    created_count: int = 0
    duplicate_count: int = 0
    status: Literal["success", "partial", "unavailable"] = "success"
    observed_at: datetime
    warnings: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class TranscriptSegment(SourceAdapterModel):
    segment_id: str
    text: str = Field(max_length=1_000_000)
    speaker: str | None = None
    section: str | None = None
    start_seconds: float | None = Field(default=None, ge=0)
    end_seconds: float | None = Field(default=None, ge=0)


class TranscriptEvidence(SourceAdapterModel):
    provider: str
    provider_record_id: str
    symbol: str
    exchange: str | None
    fiscal_year: int
    fiscal_quarter: int
    call_at: datetime | None
    published_at: datetime | None = None
    observed_at: datetime
    text: str = Field(min_length=1, max_length=2_000_000)
    segments: list[TranscriptSegment] = Field(default_factory=list)
    api_version: str
    raw_payload: dict | list
    warnings: list[str] = Field(default_factory=list)


class FilingMetadataEvidence(SourceAdapterModel):
    exchange: str
    provider_record_id: str
    symbol: str | None = None
    isin: str | None = None
    scrip_code: str | None = None
    title: str = Field(min_length=1, max_length=500)
    document_type: str = "exchange_announcement"
    attachment_url: str | None = None
    submitted_at: datetime | None = None
    published_at: datetime | None = None
    period_start: date | None = None
    period_end: date | None = None
    consolidated: str | None = None
    audited: str | None = None
    raw_payload: dict
    warnings: list[str] = Field(default_factory=list)
