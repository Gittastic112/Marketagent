from datetime import date
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Company, RawDocument, Source
from app.services.sec_ingestion import (
    SecFilingMetadata,
    fetch_recent_sec_filing_metadata,
    ingest_recent_sec_filings_for_company,
    ingest_sec_filing_metadata,
    lookup_cik_for_ticker,
    lookup_company_profile_for_ticker,
)

TEST_SEC_USER_AGENT = "Market Intelligence Test Suite sec-tests@marketintelligence.test"


def test_ingest_sec_filing_metadata_stores_raw_documents_and_skips_duplicates() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    filing = SecFilingMetadata(
        accession_number="0000320193-26-000001",
        form_type="10-K",
        filing_date=date(2026, 5, 24),
        report_date=date(2026, 3, 31),
        primary_document="aapl-20260331.htm",
        filing_url="https://www.sec.gov/Archives/edgar/data/320193/000032019326000001/aapl-20260331.htm",
    )

    with Session(engine) as session:
        company = Company(ticker="AAPL", name="Apple Inc.", cik="0000320193")
        source = Source(name="SEC EDGAR", source_type="sec")
        session.add_all([company, source])
        session.commit()

        first_result = ingest_sec_filing_metadata(session, source_id=source.id, company_id=company.id, filings=[filing])
        second_result = ingest_sec_filing_metadata(session, source_id=source.id, company_id=company.id, filings=[filing])
        documents = list(session.scalars(select(RawDocument).order_by(RawDocument.id)))

    assert first_result.created == 1
    assert first_result.created_count == 1
    assert first_result.fetched_count == 1
    assert first_result.error_count == 0
    assert first_result.skipped_duplicates == 0
    assert second_result.created == 0
    assert second_result.skipped_duplicate_count == 1
    assert second_result.skipped_duplicates == 1
    assert len(documents) == 1
    assert documents[0].document_type == "sec_filing_metadata"
    assert documents[0].title == "AAPL 10-K filed 2026-05-24"
    assert documents[0].url == filing.filing_url
    assert documents[0].published_at is not None
    assert documents[0].published_at.date() == date(2026, 5, 24)
    assert documents[0].raw_payload_json is not None
    assert documents[0].raw_payload_json["accession_number"] == "0000320193-26-000001"
    assert documents[0].raw_payload_json["form_type"] == "10-K"
    assert documents[0].raw_payload_json["filing_date"] == "2026-05-24"
    assert documents[0].content_hash


def test_ingest_sec_filing_metadata_downloads_filing_text_when_requested() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    filing = SecFilingMetadata(
        accession_number="0000320193-26-000001",
        form_type="10-K",
        filing_date=date(2026, 5, 24),
        primary_document="aapl-20260331.htm",
        filing_url="https://www.sec.gov/Archives/edgar/data/320193/000032019326000001/aapl-20260331.htm",
    )

    class FakeResponse:
        text = "<html><body>Full 10-K filing text</body></html>"

        def raise_for_status(self) -> None:
            return None

    calls: list[tuple[str, dict]] = []

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        calls.append((url, kwargs.get("headers", {})))
        return FakeResponse()

    with Session(engine) as session:
        company = Company(ticker="AAPL", name="Apple Inc.", cik="0000320193")
        source = Source(name="SEC EDGAR", source_type="sec")
        session.add_all([company, source])
        session.commit()

        result = ingest_sec_filing_metadata(
            session,
            source_id=source.id,
            company_id=company.id,
            filings=[filing],
            download_text=True,
            http_get=fake_get,
            user_agent=TEST_SEC_USER_AGENT,
        )
        document = session.scalar(select(RawDocument))

    assert result.created_count == 1
    assert result.error_count == 0
    assert document is not None
    assert document.raw_text == "<html><body>Full 10-K filing text</body></html>"
    assert document.raw_payload_json is not None
    assert document.raw_payload_json["text_downloaded"] is True
    assert calls == [
        (
            filing.filing_url,
            {"User-Agent": TEST_SEC_USER_AGENT, "Accept": "text/html, text/plain, application/xhtml+xml, */*"},
        )
    ]


def test_ingest_sec_filing_metadata_treats_same_source_url_as_duplicate() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    filing_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019326000001/aapl.htm"
    filings = [
        SecFilingMetadata("0000320193-26-000001", "10-Q", date(2026, 5, 24), filing_url=filing_url),
        SecFilingMetadata("0000320193-26-000002", "10-Q", date(2026, 5, 25), filing_url=filing_url),
    ]

    with Session(engine) as session:
        company = Company(ticker="AAPL", name="Apple Inc.", cik="0000320193")
        source = Source(name="SEC EDGAR", source_type="sec")
        session.add_all([company, source])
        session.commit()

        result = ingest_sec_filing_metadata(session, source_id=source.id, company_id=company.id, filings=filings)
        documents = list(session.scalars(select(RawDocument).order_by(RawDocument.id)))

    assert result.fetched_count == 2
    assert result.created_count == 1
    assert result.skipped_duplicate_count == 1
    assert len(documents) == 1


def test_fetch_recent_sec_filing_metadata_filters_supported_forms_from_mocked_response() -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "filings": {
                    "recent": {
                        "accessionNumber": [
                            "0000320193-26-000001",
                            "0000320193-26-000002",
                            "0000320193-26-000003",
                            "0000320193-26-000004",
                        ],
                        "form": ["10-K", "10-Q", "8-K", "4"],
                        "filingDate": ["2026-05-24", "2026-04-24", "2026-03-24", "2026-02-24"],
                        "reportDate": ["2026-03-31", "2026-03-31", "", ""],
                        "primaryDocument": ["aapl-10k.htm", "aapl-10q.htm", "aapl-8k.htm", "aapl-4.htm"],
                    }
                }
            }

    calls: list[str] = []

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        calls.append(url)
        return FakeResponse()

    filings = fetch_recent_sec_filing_metadata("0000320193", http_get=fake_get)

    assert calls == ["https://data.sec.gov/submissions/CIK0000320193.json"]
    assert [filing.form_type for filing in filings] == ["10-K", "10-Q", "8-K"]
    assert filings[0].filing_url == "https://www.sec.gov/Archives/edgar/data/320193/000032019326000001/aapl-10k.htm"


def test_fetch_recent_sec_filing_metadata_filters_by_form_and_year() -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "filings": {
                    "recent": {
                        "accessionNumber": [
                            "0000320193-26-000001",
                            "0000320193-25-000001",
                            "0000320193-26-000002",
                        ],
                        "form": ["10-K", "10-K", "10-Q"],
                        "filingDate": ["2026-05-24", "2025-05-24", "2026-04-24"],
                        "reportDate": ["2026-03-31", "2025-03-31", "2026-03-31"],
                        "primaryDocument": ["aapl-2026-10k.htm", "aapl-2025-10k.htm", "aapl-2026-10q.htm"],
                    }
                }
            }

    filings = fetch_recent_sec_filing_metadata(
        "0000320193",
        form_types=("10-K",),
        filing_year=2026,
        http_get=lambda *_args, **_kwargs: FakeResponse(),
    )

    assert [filing.accession_number for filing in filings] == ["0000320193-26-000001"]


def test_fetch_recent_sec_filing_metadata_uses_configured_user_agent() -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"filings": {"recent": {"accessionNumber": [], "form": [], "filingDate": [], "reportDate": [], "primaryDocument": []}}}

    seen_headers: list[dict] = []

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        seen_headers.append(kwargs.get("headers", {}))
        return FakeResponse()

    fetch_recent_sec_filing_metadata("0000320193", http_get=fake_get, user_agent=TEST_SEC_USER_AGENT)

    assert seen_headers[0]["User-Agent"] == TEST_SEC_USER_AGENT


def test_lookup_cik_for_ticker_uses_company_tickers_endpoint_and_user_agent() -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
                "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp."},
            }

    calls: list[tuple[str, dict]] = []

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        calls.append((url, kwargs.get("headers", {})))
        return FakeResponse()

    cik = lookup_cik_for_ticker("msft", http_get=fake_get, user_agent=TEST_SEC_USER_AGENT)

    assert cik == "0000789019"
    assert calls == [("https://www.sec.gov/files/company_tickers.json", {"User-Agent": TEST_SEC_USER_AGENT, "Accept": "application/json"})]


def test_lookup_company_profile_for_ticker_returns_sec_title_and_cik() -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
                "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp."},
            }

    profile = lookup_company_profile_for_ticker(
        "aapl",
        http_get=lambda *_args, **_kwargs: FakeResponse(),
        user_agent=TEST_SEC_USER_AGENT,
    )

    assert profile is not None
    assert profile.ticker == "AAPL"
    assert profile.cik == "0000320193"
    assert profile.title == "Apple Inc."


def test_ingest_recent_sec_filings_for_company_links_tracked_company_and_counts_errors() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "filings": {
                    "recent": {
                        "accessionNumber": ["0000789019-26-000123"],
                        "form": ["10-Q"],
                        "filingDate": ["2026-05-24"],
                        "reportDate": ["2026-03-31"],
                        "primaryDocument": ["msft-20260331.htm"],
                    }
                }
            }

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        return FakeResponse()

    with Session(engine) as session:
        company = Company(ticker="MSFT", name="Microsoft", cik="0000789019")
        no_cik_company = Company(ticker="META", name="Meta Platforms")
        source = Source(name="SEC EDGAR", source_type="sec")
        session.add_all([company, no_cik_company, source])
        session.commit()

        result = ingest_recent_sec_filings_for_company(session, source_id=source.id, company_id=company.id, http_get=fake_get)
        error_result = ingest_recent_sec_filings_for_company(session, source_id=source.id, company_id=no_cik_company.id, http_get=fake_get)
        documents = list(session.scalars(select(RawDocument).order_by(RawDocument.id)))

    assert result.fetched_count == 1
    assert result.created_count == 1
    assert result.error_count == 0
    assert documents[0].company_id == company.id
    assert documents[0].raw_payload_json is not None
    assert documents[0].raw_payload_json["accession_number"] == "0000789019-26-000123"
    assert error_result.created_count == 0
    assert error_result.error_count == 1


def test_ingest_recent_sec_filings_for_company_looks_up_missing_cik() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    class CompanyTickersResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"0": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp."}}

    class SubmissionsResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "filings": {
                    "recent": {
                        "accessionNumber": ["0000789019-26-000123"],
                        "form": ["10-Q"],
                        "filingDate": ["2026-05-24"],
                        "reportDate": ["2026-03-31"],
                        "primaryDocument": ["msft-20260331.htm"],
                    }
                }
            }

    def fake_get(url: str, **kwargs: object) -> CompanyTickersResponse | SubmissionsResponse:
        if url == "https://www.sec.gov/files/company_tickers.json":
            return CompanyTickersResponse()
        if url == "https://data.sec.gov/submissions/CIK0000789019.json":
            return SubmissionsResponse()
        raise AssertionError(f"unexpected URL {url}")

    with Session(engine) as session:
        company = Company(ticker="MSFT", name="Microsoft")
        source = Source(name="SEC EDGAR", source_type="sec")
        session.add_all([company, source])
        session.commit()

        result = ingest_recent_sec_filings_for_company(session, source_id=source.id, company_id=company.id, http_get=fake_get)
        session.refresh(company)

    assert result.created_count == 1
    assert result.error_count == 0
    assert company.cik == "0000789019"
