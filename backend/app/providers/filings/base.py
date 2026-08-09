from datetime import datetime
from typing import Protocol

from pydantic import BaseModel

from app.models import Company
from app.services.sec_ingestion import SecFilingMetadata


class ManualFilingCreate(BaseModel):
    document_type: str
    title: str
    url: str | None = None
    published_at: datetime | None = None
    raw_text: str | None = None
    raw_payload_json: dict | None = None


class FilingProvider(Protocol):
    provider_name: str
    market: str

    def preview_filings(
        self,
        company: Company,
        form_type: str | None = None,
        filing_year: int | None = None,
        limit: int = 20,
    ) -> list[SecFilingMetadata]:
        ...


ALLOWED_MANUAL_FILING_TYPES = {
    "annual_report",
    "quarterly_result",
    "investor_presentation",
    "exchange_announcement",
    "shareholding_pattern",
    "corporate_action",
}
