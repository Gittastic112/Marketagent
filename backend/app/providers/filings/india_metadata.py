"""Offline normalization of user-supplied original NSE/BSE metadata.

No exchange website scraping or undocumented feed authentication is performed.
"""
from datetime import UTC, date, datetime
import re
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from app.providers.research_sources.errors import SourceAdapterError
from app.schemas.source_adapters import FilingMetadataEvidence


def _time(value) -> datetime | None:
    if not value:
        return None
    if not isinstance(value, str):
        raise SourceAdapterError("FILING_DATE_INVALID", "Filing metadata contains an invalid date.")
    value = value.strip()
    # A calendar date does not establish an intraday dissemination instant.
    # Keep its original spelling in raw_payload and expose the precision warning.
    for fmt in (None, "%d-%b-%Y", "%d-%m-%Y"):
        try:
            date.fromisoformat(value) if fmt is None else datetime.strptime(value, fmt).date()
            return None
        except ValueError:
            continue
    for fmt in (None, "%d-%b-%Y %H:%M:%S", "%d%m%Y%H%M%S"):
        try:
            parsed = datetime.fromisoformat(value) if fmt is None else datetime.strptime(value, fmt)
            return (parsed.replace(tzinfo=ZoneInfo("Asia/Kolkata")) if parsed.tzinfo is None else parsed).astimezone(UTC)
        except ValueError:
            continue
    raise SourceAdapterError("FILING_DATE_INVALID", "Filing metadata contains an unsupported date format.")


def _period_date(value) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(value), fmt).date()
        except ValueError:
            continue
    raise SourceAdapterError("FILING_PERIOD_INVALID", "Filing metadata contains an unsupported period date.")


def _attachment(url: str | None, exchange: str) -> str | None:
    if not url:
        return None
    if not isinstance(url, str) or any(ord(c) <= 32 for c in url) or "\\" in url:
        raise SourceAdapterError("FILING_URL_INVALID", "Filing attachment must reference the selected official exchange.")
    parsed = urlsplit(url)
    hosts = {"www.nseindia.com", "www.nseindia.in", "nsearchives.nseindia.com", "nsearchives.nseindia.in", "archives.nseindia.com"} if exchange == "NSE" else {"www.bseindia.com", "bseindia.com"}
    if parsed.scheme != "https" or parsed.hostname not in hosts or parsed.username or parsed.password or parsed.port not in {None, 443}:
        raise SourceAdapterError("FILING_URL_INVALID", "Filing attachment must reference the selected official exchange.")
    return url


def normalize_india_filing(exchange: str, row: dict) -> FilingMetadataEvidence:
    if exchange == "NSE":
        symbol = row.get("symbol")
        identifier = row.get("seq_id") or row.get("seqNumber") or row.get("id")
        url = row.get("attchmntFile") or row.get("xbrl")
        if not identifier:
            identifier = url
        if not identifier or not isinstance(symbol, str) or not symbol:
            raise SourceAdapterError("FILING_IDENTITY_MISSING", "NSE metadata needs a symbol and stable filing ID or attachment.")
        submitted_value, published_value = row.get("an_dt") or row.get("broadCastDate"), row.get("exchdisstime")
        submitted_at, published_at = _time(submitted_value), _time(published_value)
        return FilingMetadataEvidence(exchange=exchange, provider_record_id=str(identifier), symbol=symbol.upper(),
            isin=row.get("sm_isin") or row.get("isin"), title=str(row.get("desc") or row.get("relatingTo") or "NSE financial filing")[:500],
            document_type={"Annual": "annual_report", "Quarterly": "quarterly_result"}.get(row.get("period"), "exchange_announcement"),
            attachment_url=_attachment(url, exchange), submitted_at=submitted_at,
            published_at=published_at, period_start=_period_date(row.get("from_date") or row.get("fromDate")),
            period_end=_period_date(row.get("to_date") or row.get("toDate")), consolidated=str(row["consolidated"]) if "consolidated" in row else None,
            audited=str(row["audited"]) if "audited" in row else None, raw_payload=row,
            warnings=["METADATA_ONLY_NOT_VERIFIED_FINANCIALS", "OFFSET_FREE_TIMES_INTERPRETED_AS_ASIA_KOLKATA",
                *(["SUBMISSION_DATE_ONLY_PRECISE_TIME_UNKNOWN"] if submitted_value and submitted_at is None else []),
                *(["PUBLICATION_DATE_ONLY_PRECISE_TIME_UNKNOWN"] if published_value and published_at is None else [])])
    if exchange != "BSE" or not row.get("NEWSID") or not row.get("SCRIP_CD"):
        raise SourceAdapterError("FILING_IDENTITY_MISSING", "BSE metadata needs NEWSID and SCRIP_CD.")
    attachment = row.get("ATTACHMENTNAME")
    if attachment and (not isinstance(attachment, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,200}\.pdf", attachment)):
        raise SourceAdapterError("FILING_URL_INVALID", "BSE attachment filename is invalid.")
    # Original filenames are retained; the live/archive directory is not guessed.
    url = row.get("attachment_url")
    submitted_value, published_value = row.get("News_submission_dt"), row.get("DissemDT")
    submitted_at, published_at = _time(submitted_value), _time(published_value)
    return FilingMetadataEvidence(exchange=exchange, provider_record_id=str(row["NEWSID"]), scrip_code=str(row["SCRIP_CD"]),
        isin=row.get("ISIN"), title=str(row.get("NEWSSUB") or row.get("HEADLINE") or "BSE announcement")[:500],
        attachment_url=_attachment(url, exchange), submitted_at=submitted_at,
        published_at=published_at, raw_payload=row,
        warnings=["METADATA_ONLY_NOT_VERIFIED_FINANCIALS", "OFFSET_FREE_TIMES_INTERPRETED_AS_ASIA_KOLKATA",
                  *(["SUBMISSION_DATE_ONLY_PRECISE_TIME_UNKNOWN"] if submitted_value and submitted_at is None else []),
                  *(["PUBLICATION_DATE_ONLY_PRECISE_TIME_UNKNOWN"] if published_value and published_at is None else []),
                  *(["ATTACHMENT_LOCATION_REQUIRES_OFFICIAL_REFERENCE"] if attachment and not url else [])])


def assert_filing_identity(item: FilingMetadataEvidence, *, symbol: str, isin: str | None,
                           scrip_code: str | None) -> None:
    if item.isin and isin and item.isin != isin:
        raise SourceAdapterError("FILING_IDENTITY_MISMATCH", "The filing belongs to a different security.")
    if item.exchange == "NSE":
        if item.symbol != symbol.upper():
            raise SourceAdapterError("FILING_IDENTITY_MISMATCH", "The NSE symbol does not match the selected company.")
    elif not scrip_code or item.scrip_code != scrip_code:
        raise SourceAdapterError("FILING_IDENTITY_UNRESOLVED", "Resolve this company's BSE scrip code before intake.")
