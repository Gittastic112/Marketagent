from fastapi import HTTPException

from app.models import Company
from app.services.sec_ingestion import SecFilingMetadata, fetch_recent_sec_filing_metadata


class SecEdgarFilingProvider:
    provider_name = "SEC EDGAR"
    market = "US"

    def preview_filings(
        self,
        company: Company,
        form_type: str | None = None,
        filing_year: int | None = None,
        limit: int = 20,
    ) -> list[SecFilingMetadata]:
        if not company.cik:
            raise HTTPException(status_code=409, detail="Company needs a CIK before SEC filing preview")

        return fetch_recent_sec_filing_metadata(
            company.cik,
            form_types=(form_type or "10-K",),
            filing_year=filing_year,
            limit=limit,
        )
