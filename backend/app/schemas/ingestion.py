"""Ingestion API contracts, independent of HTTP and persistence."""

from datetime import (
    date,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from typing import (
    Literal,
)


class RssIngestionCreate(BaseModel):
    source_id: int
    company_id: int | None = None
    rss_xml: str | None = None
    feed_url: str | None = None


class RssIngestionRead(BaseModel):
    fetched_count: int
    created_count: int
    skipped_duplicate_count: int
    error_count: int = 0
    errors: list[str] = Field(default_factory=list)
    created: int
    skipped_duplicates: int
    events_created: int = 0
    events_skipped_existing: int = 0
    alerts_created: int = 0
    alerts_skipped_existing: int = 0
    alerts_skipped_below_threshold: int = 0


class RssBatchIngestionRead(RssIngestionRead):
    source_count: int = 0


class SecFilingMetadataCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    accession_number: str
    form_type: str
    filing_date: date
    report_date: date | None = None
    primary_document: str | None = None
    filing_url: str | None = None


class FilingDiscoveryRead(BaseModel):
    company_id: int
    market: str
    provider_name: str
    mode: Literal["automated", "manual"]
    manual_required: bool
    filings: list[SecFilingMetadataCreate] = Field(default_factory=list)
    next_action: str


class SecFilingIngestionCreate(BaseModel):
    source_id: int | None = None
    company_id: int
    filings: list[SecFilingMetadataCreate] = Field(default_factory=list)
    form_types: list[str] = Field(default_factory=lambda: ["10-K", "10-Q", "8-K"])
    filing_year: int | None = None
    limit: int = 40
    download_text: bool = False


class SecFilingIngestionRead(BaseModel):
    fetched_count: int
    created_count: int
    skipped_duplicate_count: int
    error_count: int = 0
    errors: list[str] = Field(default_factory=list)
    created: int
    skipped_duplicates: int
    events_created: int = 0
    events_skipped_existing: int = 0
    alerts_created: int = 0
    alerts_skipped_existing: int = 0
    alerts_skipped_below_threshold: int = 0


class EventExtractionRead(BaseModel):
    created: int
    skipped_existing: int


class AlertGenerationRead(BaseModel):
    created: int
    skipped_existing: int
    skipped_below_threshold: int
