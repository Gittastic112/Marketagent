from fastapi import HTTPException

from app.models import Company
from app.providers.filings.base import ALLOWED_MANUAL_FILING_TYPES, FilingProvider, ManualFilingCreate
from app.providers.filings.india_manual import IndiaManualFilingProvider
from app.providers.filings.sec_edgar import SecEdgarFilingProvider


def get_filing_provider(company: Company, source: str = "auto") -> FilingProvider:
    if source != "auto":
        raise HTTPException(status_code=400, detail=f"Unsupported filing source {source}")

    market = (company.market or "US").upper()
    if market == "US":
        return SecEdgarFilingProvider()
    if market == "IN":
        return IndiaManualFilingProvider()
    raise HTTPException(status_code=400, detail=f"Unsupported market {market}")


__all__ = [
    "ALLOWED_MANUAL_FILING_TYPES",
    "FilingProvider",
    "IndiaManualFilingProvider",
    "ManualFilingCreate",
    "SecEdgarFilingProvider",
    "get_filing_provider",
]
