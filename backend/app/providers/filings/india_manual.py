from fastapi import HTTPException

from app.models import Company
from app.services.sec_ingestion import SecFilingMetadata


class IndiaManualFilingProvider:
    provider_name = "India Manual Filings"
    market = "IN"

    def preview_filings(
        self,
        company: Company,
        form_type: str | None = None,
        filing_year: int | None = None,
        limit: int = 20,
    ) -> list[SecFilingMetadata]:
        raise HTTPException(
            status_code=409,
            detail="India automated filing provider not configured; use manual filing upload/link",
        )
