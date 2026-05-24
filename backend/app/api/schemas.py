from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CompanyCreate(BaseModel):
    ticker: str
    name: str
    sector: str | None = None
    industry: str | None = None
    exchange: str | None = None
    cik: str | None = None
    active: bool = True


class CompanyUpdate(BaseModel):
    ticker: str | None = None
    name: str | None = None
    sector: str | None = None
    industry: str | None = None
    exchange: str | None = None
    cik: str | None = None
    active: bool | None = None


class CompanyRead(CompanyCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class SourceCreate(BaseModel):
    name: str
    source_type: str
    base_url: str | None = None
    reliability_score: int | None = None


class SourceUpdate(BaseModel):
    name: str | None = None
    source_type: str | None = None
    base_url: str | None = None
    reliability_score: int | None = None


class SourceRead(SourceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class RawDocumentCreate(BaseModel):
    company_id: int | None = None
    source_id: int
    document_type: str
    title: str
    url: str | None = None
    published_at: datetime | None = None
    raw_text: str | None = None
    raw_payload_json: dict[str, Any] | None = None
    content_hash: str


class RawDocumentUpdate(BaseModel):
    company_id: int | None = None
    source_id: int | None = None
    document_type: str | None = None
    title: str | None = None
    url: str | None = None
    published_at: datetime | None = None
    raw_text: str | None = None
    raw_payload_json: dict[str, Any] | None = None
    content_hash: str | None = None


class RawDocumentRead(RawDocumentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingested_at: datetime
    created_at: datetime


class EventCreate(BaseModel):
    company_id: int | None = None
    raw_document_id: int | None = None
    event_type: str
    information_speed: str
    title: str
    description: str | None = None
    event_time: datetime | None = None
    credibility_score: int | None = None
    novelty_score: int | None = None
    impact_score: int | None = None
    priority_score: int | None = None


class EventUpdate(BaseModel):
    company_id: int | None = None
    raw_document_id: int | None = None
    event_type: str | None = None
    information_speed: str | None = None
    title: str | None = None
    description: str | None = None
    event_time: datetime | None = None
    credibility_score: int | None = None
    novelty_score: int | None = None
    impact_score: int | None = None
    priority_score: int | None = None


class EventRead(EventCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class AlertCreate(BaseModel):
    event_id: int | None = None
    company_id: int | None = None
    alert_type: str
    severity: str = "low"
    title: str
    summary: str | None = None
    why_it_matters: str | None = None
    what_changed: str | None = None
    evidence: str | None = None
    confidence_bucket: str = "low"
    review_status: str = "unreviewed"
    review_notes: str | None = None


class AlertUpdate(BaseModel):
    event_id: int | None = None
    company_id: int | None = None
    alert_type: str | None = None
    severity: str | None = None
    title: str | None = None
    summary: str | None = None
    why_it_matters: str | None = None
    what_changed: str | None = None
    evidence: str | None = None
    confidence_bucket: str | None = None
    review_status: str | None = None
    review_notes: str | None = None


class AlertRead(AlertCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


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


class ThesisNoteRead(ThesisNoteCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class DailyBriefRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brief_date: date
    title: str
    summary: str
    payload_json: dict[str, Any]
    created_at: datetime


class RssIngestionCreate(BaseModel):
    source_id: int
    company_id: int | None = None
    rss_xml: str


class RssIngestionRead(BaseModel):
    created: int
    skipped_duplicates: int


class SecFilingMetadataCreate(BaseModel):
    accession_number: str
    form_type: str
    filing_date: date
    report_date: date | None = None
    primary_document: str | None = None
    filing_url: str | None = None


class SecFilingIngestionCreate(BaseModel):
    source_id: int
    company_id: int
    filings: list[SecFilingMetadataCreate]


class SecFilingIngestionRead(BaseModel):
    created: int
    skipped_duplicates: int


class EventExtractionRead(BaseModel):
    created: int
    skipped_existing: int
