"""Filing publication values retain the precision supplied by their source."""
from datetime import UTC, date, datetime, time
from typing import Annotated

from pydantic import BeforeValidator


def _preserve_calendar_date(value):
    if isinstance(value, str) and len(value) == 10 and value[4:5] == "-" and value[7:8] == "-":
        return date.fromisoformat(value)
    return value


PublicationValue = Annotated[datetime | date, BeforeValidator(_preserve_calendar_date)]


def publication_storage(value: datetime | date | None) -> tuple[datetime | None, str]:
    if isinstance(value, datetime):
        stamp = value if value.tzinfo else value.replace(tzinfo=UTC)
        return stamp.astimezone(UTC), "timestamp"
    if value is not None:
        return datetime.combine(value, time.min, tzinfo=UTC), "date"
    return None, "unknown"


def document_publication(stamp: datetime | None, document_type: str, source_kind: str | None,
                         precision: str | None) -> datetime | date | None:
    if stamp is None:
        return None
    utc = stamp.astimezone(UTC) if stamp.tzinfo else stamp.replace(tzinfo=UTC)
    # SEC filing metadata and legacy date pickers stored a calendar day at UTC
    # midnight. Only an explicitly timed upload can establish that exact instant.
    if (document_type == "sec_filing_metadata" or precision == "date" or
            (precision is None and source_kind in {"manual_filing", "pdf_filing_upload"}
             and utc.time() == time.min)):
        return utc.date()
    return utc
