"""Dated official source selection, bound to the reviewed security identity."""
import json
import logging
from pathlib import Path

from app.models import Company
from app.schemas.ingestion import ManualFilingSourceRead

DATA_ROOT = Path(__file__).resolve().parents[3] / "data"
logger = logging.getLogger(__name__)


def official_manual_source(company: Company) -> ManualFilingSourceRead | None:
    if company.market != "IN" or company.primary_exchange != "NSE" or not company.isin:
        return None
    try:
        scope = json.loads((DATA_ROOT / "research-scope.json").read_text())
        checklist = json.loads((DATA_ROOT / "certification/scoped-source-checklist.json").read_text())
        security = next((row for row in scope["securities"] if row.get("isin") == company.isin
                         and row["ticker"] == (company.local_symbol or company.ticker)), None)
        if security is None:
            return None
        source = next((row for row in checklist["securities"] if row["ticker"] == security["ticker"]), None)
        if source is None:
            return None
        return ManualFilingSourceRead(
            url=source["source"], checked_on=checklist["manual_sources_checked_date"], security_isin=company.isin,
            target_years=source["target_years"], required_documents=source["required_documents"],
        )
    except (OSError, ValueError, KeyError, TypeError):
        logger.warning("Official manual source checklist unavailable")
        return None
