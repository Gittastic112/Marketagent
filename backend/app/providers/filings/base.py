from datetime import UTC, datetime
import ipaddress
import json
from urllib.parse import urlsplit
from typing import Protocol

from pydantic import BaseModel, Field, field_validator

from app.models import Company
from app.services.sec_ingestion import SecFilingMetadata


class ManualFilingCreate(BaseModel):
    document_type: str = Field(max_length=80)
    title: str = Field(min_length=1, max_length=500)
    url: str | None = Field(default=None, max_length=1000)
    published_at: datetime | None = None
    raw_text: str | None = Field(default=None, max_length=1_000_000)
    raw_payload_json: dict | None = None

    @field_validator("title")
    @classmethod
    def nonblank_title(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("A filing title is required")
        return value.strip()

    @field_validator("published_at")
    @classmethod
    def utc_date(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return (value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC))

    @field_validator("raw_payload_json")
    @classmethod
    def bounded_metadata(cls, value: dict | None) -> dict | None:
        if value is not None and len(json.dumps(value, allow_nan=False).encode("utf-8")) > 65_536:
            raise ValueError("Filing metadata exceeds 64 KiB")
        return value

    @field_validator("url")
    @classmethod
    def reference_url(cls, value: str | None) -> str | None:
        # Stored citation only. Fetching this URL later still requires the
        # DNS-pinned safe HTTP client; this validation performs no network call.
        if value is None:
            return None
        if "\\" in value or any(ord(char) <= 32 or ord(char) == 127 for char in value):
            raise ValueError("Unsupported filing reference URL")
        parsed = urlsplit(value)
        host = (parsed.hostname or "").rstrip(".").lower()
        if (parsed.scheme not in {"https", "http"} or not host or parsed.username is not None
                or parsed.password is not None or parsed.port not in {None, 80, 443}
                or host in {"localhost", "docker.internal", "host.docker.internal", "gateway.docker.internal"}
                or host.endswith((".localhost", ".local", ".internal"))):
            raise ValueError("A public HTTP(S) reference without credentials is required")
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            address = None
        if address is not None and (not address.is_global or address.is_multicast):
            raise ValueError("A public HTTP(S) reference is required")
        return value


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
