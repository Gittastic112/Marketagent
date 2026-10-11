from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from hashlib import sha256
import logging
from typing import Any, Callable

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Company, RawDocument, Source
from app.providers.safe_http import fetch_public_json

SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"
DEFAULT_SEC_FORMS = ("10-K", "10-Q", "8-K")
logger = logging.getLogger(__name__)
DEFAULT_SEC_SOURCE_NAME = "SEC EDGAR"
SEC_SOURCE_TYPES = {"sec", "filing"}

def get_valid_sec_user_agent(user_agent: str | None = None) -> str:
    ua = user_agent or get_settings().sec_user_agent
    if not ua or ua.lower() == "placeholder" or "contact@example.com" in ua or "your.email@example.com" in ua:
        raise ValueError("SEC_USER_AGENT is not configured. The SEC requires a real application name and contact email in the User-Agent header. Please configure this in your environment.")
    return ua



@dataclass(frozen=True)
class SecIngestionResult:
    fetched_count: int
    created_count: int
    skipped_duplicate_count: int
    error_count: int = 0
    errors: tuple[str, ...] = ()

    @property
    def created(self) -> int:
        return self.created_count

    @property
    def skipped_duplicates(self) -> int:
        return self.skipped_duplicate_count


@dataclass(frozen=True)
class SecFilingMetadata:
    accession_number: str
    form_type: str
    filing_date: date
    report_date: date | None = None
    primary_document: str | None = None
    filing_url: str | None = None


@dataclass(frozen=True)
class SecCompanyProfile:
    ticker: str
    title: str
    cik: str


def resolve_sec_source(db: Session, source_id: int | None = None) -> Source:
    if source_id is not None:
        source = db.get(Source, source_id)
        if source is None:
            raise ValueError("Source not found")
        if source.source_type not in SEC_SOURCE_TYPES:
            raise ValueError("Selected source is not an SEC filing source")
        if not source.active:
            raise ValueError("Selected SEC filing source is inactive")
        return source

    source = db.scalar(
        select(Source)
        .where(
            Source.active.is_(True),
            or_(
                Source.name == DEFAULT_SEC_SOURCE_NAME,
                Source.source_type.in_(SEC_SOURCE_TYPES),
            ),
        )
        .order_by(
            (Source.name == DEFAULT_SEC_SOURCE_NAME).desc(),
            Source.id,
        )
    )
    if source is not None:
        return source

    source = Source(
        name=DEFAULT_SEC_SOURCE_NAME,
        source_type="sec",
        base_url="https://www.sec.gov",
        reliability_score=95,
        active=True,
    )
    db.add(source)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        source = db.scalar(
            select(Source).where(Source.name == DEFAULT_SEC_SOURCE_NAME)
        )
        if source is None:
            raise
    else:
        db.refresh(source)
    return source


def ingest_sec_filing_metadata(
    db: Session,
    source_id: int,
    company_id: int,
    filings: list[SecFilingMetadata],
    download_text: bool = False,
    http_get: Callable[..., Any] | None = None,
    user_agent: str | None = None,
) -> SecIngestionResult:
    company = db.get(Company, company_id)
    ticker = company.ticker if company is not None else f"company-{company_id}"
    created = 0
    skipped_duplicates = 0
    error_count = 0
    errors: list[str] = []
    for filing in filings:
        content_hash = build_sec_content_hash(filing)
        existing = _find_existing_raw_document(db, content_hash, filing.filing_url)
        if existing is not None:
            skipped_duplicates += 1
            continue
        raw_text = None
        text_downloaded = False
        if download_text:
            if filing.filing_url:
                try:
                    raw_text = fetch_sec_filing_text(filing.filing_url, http_get=http_get, user_agent=user_agent)
                    text_downloaded = True
                except Exception as exc:
                    logger.error(
                        "SEC filing text download failed",
                        extra={"provider": "SEC EDGAR", "exception_type": type(exc).__name__},
                    )
                    error_count += 1
                    errors.append(f"{filing.accession_number}: filing text download failed")
            else:
                error_count += 1
                errors.append(f"{filing.accession_number}: filing_url is required to download filing text")

        db.add(
            RawDocument(
                company_id=company_id,
                source_id=source_id,
                document_type="sec_filing_metadata",
                title=f"{ticker} {filing.form_type} filed {filing.filing_date.isoformat()}",
                url=filing.filing_url,
                published_at=datetime.combine(filing.filing_date, time.min, tzinfo=timezone.utc),
                raw_text=raw_text,
                raw_payload_json={
                    "source_kind": "sec_edgar",
                    "accession_number": filing.accession_number,
                    "form_type": filing.form_type,
                    "filing_date": filing.filing_date.isoformat(),
                    "report_date": filing.report_date.isoformat() if filing.report_date is not None else None,
                    "primary_document": filing.primary_document,
                    "filing_url": filing.filing_url,
                    "text_downloaded": text_downloaded,
                },
                content_hash=content_hash,
            )
        )
        created += 1

    db.commit()
    return SecIngestionResult(
        fetched_count=len(filings),
        created_count=created,
        skipped_duplicate_count=skipped_duplicates,
        error_count=error_count,
        errors=tuple(errors),
    )


def ingest_recent_sec_filings_for_company(
    db: Session,
    source_id: int,
    company_id: int,
    form_types: tuple[str, ...] = DEFAULT_SEC_FORMS,
    filing_year: int | None = None,
    limit: int = 40,
    http_get: Callable[..., Any] | None = None,
    download_text: bool = False,
) -> SecIngestionResult:
    company = db.get(Company, company_id)
    if company is None:
        return SecIngestionResult(fetched_count=0, created_count=0, skipped_duplicate_count=0, error_count=1, errors=("Company not found",))
    if not company.cik:
        try:
            company.cik = lookup_cik_for_ticker(company.ticker, http_get=http_get)
            if company.cik is None:
                return SecIngestionResult(
                    fetched_count=0,
                    created_count=0,
                    skipped_duplicate_count=0,
                    error_count=1,
                    errors=(f"Company {company.ticker} has no CIK and lookup did not find one",),
                )
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error(
                "SEC CIK lookup failed during ingestion",
                extra={"provider": "SEC EDGAR", "exception_type": type(exc).__name__},
            )
            return SecIngestionResult(
                fetched_count=0,
                created_count=0,
                skipped_duplicate_count=0,
                error_count=1,
                errors=("SEC CIK lookup failed.",),
            )

    try:
        filings = fetch_recent_sec_filing_metadata(
            company.cik,
            form_types=form_types,
            filing_year=filing_year,
            limit=limit,
            http_get=http_get,
        )
    except ValueError:
        raise
    except Exception as exc:
        logger.error(
            "SEC filing metadata fetch failed",
            extra={"provider": "SEC EDGAR", "exception_type": type(exc).__name__},
        )
        return SecIngestionResult(
            fetched_count=0,
            created_count=0,
            skipped_duplicate_count=0,
            error_count=1,
            errors=("SEC filing metadata fetch failed.",),
        )

    return ingest_sec_filing_metadata(
        db,
        source_id=source_id,
        company_id=company_id,
        filings=filings,
        download_text=download_text,
        http_get=http_get,
    )


def fetch_recent_sec_filing_metadata(
    cik: str,
    form_types: tuple[str, ...] = DEFAULT_SEC_FORMS,
    filing_year: int | None = None,
    limit: int = 40,
    http_get: Callable[..., Any] | None = None,
    user_agent: str | None = None,
) -> list[SecFilingMetadata]:
    normalized_cik = _normalize_cik(cik)
    url, headers = SEC_SUBMISSIONS_URL.format(cik=normalized_cik), _sec_headers(user_agent)
    if http_get is not None:
        response = http_get(url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
    else:
        data = fetch_public_json(url, headers=headers, max_bytes=16 * 1024 * 1024)
    recent = data.get("filings", {}).get("recent", {})

    filings: list[SecFilingMetadata] = []
    accepted_forms = set(form_types)
    accession_numbers = recent.get("accessionNumber", [])
    forms = recent.get("form", [])
    filing_dates = recent.get("filingDate", [])
    report_dates = recent.get("reportDate", [])
    primary_documents = recent.get("primaryDocument", [])

    for index, accession_number in enumerate(accession_numbers):
        form_type = _list_value(forms, index)
        if form_type not in accepted_forms:
            continue
        filing_date_value = _parse_date(_list_value(filing_dates, index))
        if filing_date_value is None:
            continue
        if filing_year is not None and filing_date_value.year != filing_year:
            continue
        primary_document = _list_value(primary_documents, index)
        report_date = _parse_date(_list_value(report_dates, index))
        filings.append(
            SecFilingMetadata(
                accession_number=accession_number,
                form_type=form_type,
                filing_date=filing_date_value,
                report_date=report_date,
                primary_document=primary_document,
                filing_url=_build_filing_url(cik, accession_number, primary_document),
            )
        )
        if len(filings) >= limit:
            break

    return filings


def lookup_company_profile_for_ticker(ticker: str, http_get: Callable[..., Any] | None = None, user_agent: str | None = None) -> SecCompanyProfile | None:
    headers = _sec_headers(user_agent)
    if http_get is not None:
        response = http_get(SEC_COMPANY_TICKERS_URL, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
    else:
        data = fetch_public_json(SEC_COMPANY_TICKERS_URL, headers=headers, max_bytes=8 * 1024 * 1024)
    wanted = ticker.upper()
    for company in data.values():
        if str(company.get("ticker", "")).upper() == wanted:
            return SecCompanyProfile(
                ticker=wanted,
                title=str(company.get("title", "")).strip(),
                cik=_normalize_cik(str(company.get("cik_str", ""))),
            )
    return None


def lookup_cik_for_ticker(ticker: str, http_get: Callable[..., Any] | None = None, user_agent: str | None = None) -> str | None:
    profile = lookup_company_profile_for_ticker(ticker, http_get=http_get, user_agent=user_agent)
    return profile.cik if profile is not None else None


def fetch_sec_filing_text(filing_url: str, http_get: Callable[..., Any] | None = None, user_agent: str | None = None) -> str:
    ua = get_valid_sec_user_agent(user_agent)
    if http_get is not None:
        response = http_get(
            filing_url,
            headers=_sec_filing_text_headers(ua),
            timeout=20,
        )
        response.raise_for_status()
        return response.text

    from app.providers.sec_provider import SECProvider

    provider = SECProvider(user_agent=ua)
    return provider.fetch_filing_text(filing_url)


def build_sec_content_hash(filing: SecFilingMetadata) -> str:
    stable_parts = [filing.accession_number, filing.form_type, filing.filing_date.isoformat()]
    return sha256("|".join(stable_parts).encode("utf-8")).hexdigest()


def _find_existing_raw_document(db: Session, content_hash: str, url: str | None) -> RawDocument | None:
    filters = [RawDocument.content_hash == content_hash]
    if url:
        filters.append(RawDocument.url == url)
    return db.scalar(select(RawDocument).where(or_(*filters)))


def _normalize_cik(cik: str) -> str:
    return "".join(character for character in cik if character.isdigit()).zfill(10)


def _build_filing_url(cik: str, accession_number: str, primary_document: str | None) -> str | None:
    if not primary_document:
        return None
    archive_cik = str(int(_normalize_cik(cik)))
    archive_accession = accession_number.replace("-", "")
    return SEC_ARCHIVES_URL.format(cik=archive_cik, accession=archive_accession, document=primary_document)


def _list_value(values: list[Any], index: int) -> Any:
    if index >= len(values):
        return None
    return values[index] or None


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _sec_headers(user_agent: str | None = None) -> dict[str, str]:
    return {"User-Agent": get_valid_sec_user_agent(user_agent), "Accept": "application/json"}


def _sec_filing_text_headers(user_agent: str | None = None) -> dict[str, str]:
    return {"User-Agent": get_valid_sec_user_agent(user_agent), "Accept": "text/html, text/plain, application/xhtml+xml, */*"}
