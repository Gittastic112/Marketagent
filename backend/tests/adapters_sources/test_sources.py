"""Mock Data provider fixtures; actual optional parsers tested separately below."""
from datetime import UTC, date, datetime
from pathlib import Path
import hashlib
import json
import subprocess
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.dependencies import get_current_user
from app.api.routers.source_adapters import router
from app.db.session import get_db
from app.models import Company, DocumentAsset, FinancialExtractionCandidate, FinancialMetric, ProcessingRun, RawDocument, Source
from app.providers.extraction.edgar import parse_company_facts
from app.providers.extraction.jobs import dependency_version, run_extraction
from app.providers.filings.india_metadata import normalize_india_filing, assert_filing_identity
from app.providers.fred_provider import FredProvider
from app.providers.research_sources.errors import SourceAdapterError
from app.providers.research_sources.transcripts import normalize_earningscall, normalize_fmp
from app.schemas.source_adapters import SourceAdapterResult, TranscriptRequest
from app.services.source_adapters import workflows

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def facts():
    return {"cik": 320193, "entityName": "Mock Data issuer", "facts": {"us-gaap": {
        "Revenues": {"label": "Revenue", "description": "Revenue", "units": {"USD": [
            {"start": "2023-01-01", "end": "2023-12-31", "val": 100, "form": "10-K", "fy": 2023, "fp": "FY", "filed": "2024-02-01", "accn": "original"},
            {"start": "2023-01-01", "end": "2023-12-31", "val": 110, "form": "10-K/A", "fy": 2023, "fp": "FY", "filed": "2024-06-01", "accn": "amendment"},
            {"start": "2023-10-01", "end": "2023-12-31", "val": 25, "form": "10-Q", "fy": 2023, "fp": "Q4", "filed": "2024-02-01", "accn": "quarter"}],
            "EUR": [{"start": "2023-01-01", "end": "2023-12-31", "val": 999, "form": "10-K", "fp": "FY", "filed": "2024-02-01", "accn": "wrong-unit"}]}},
        "CashAndCashEquivalentsAtCarryingValue": {"label": "Cash", "units": {"USD": [
            {"end": "2023-12-31", "val": 0, "form": "10-K", "fy": 2023, "fp": "FY", "filed": "2024-02-01", "accn": "original"}]}}
    }}}


def transcript_payload(text="Mock Data guidance text"):
    return {"exchange": "NASDAQ", "symbol": "MOCK", "level": 1,
        "event": {"year": 2024, "quarter": 1, "conference_date": "2024-02-02T17:00:00-05:00"}, "text": text}


def test_transcript_times_and_identity_are_distinct():
    request = TranscriptRequest(provider="earningscall", fiscal_year=2024, fiscal_quarter=1)
    evidence = normalize_earningscall(transcript_payload(), symbol="MOCK", exchange="NASDAQ", request=request, observed_at=NOW)
    assert evidence.call_at == datetime(2024, 2, 2, 22, tzinfo=UTC)
    assert evidence.published_at is None and evidence.observed_at == NOW
    assert evidence.segments[0].segment_id.startswith("segment-0-")
    with pytest.raises(SourceAdapterError):
        normalize_earningscall(transcript_payload(), symbol="OTHER", exchange="NASDAQ", request=request, observed_at=NOW)


def test_word_timing_payload_and_bad_alignment():
    request = TranscriptRequest(provider="earningscall", fiscal_year=2024, fiscal_quarter=1, level=3)
    payload = transcript_payload()
    payload.update(level=3, speakers=[{"speaker": {"id": "one", "name": "Mock speaker"},
        "words": ["Mock", "Data"], "start_times": [0.1, 0.5]}])
    evidence = normalize_earningscall(payload, symbol="MOCK", exchange="NASDAQ", request=request, observed_at=NOW)
    assert evidence.segments[0].text == "Mock Data" and evidence.segments[0].start_seconds == 0.1
    payload["speakers"][0]["start_times"] = [0.5]
    with pytest.raises(SourceAdapterError):
        normalize_earningscall(payload, symbol="MOCK", exchange="NASDAQ", request=request, observed_at=NOW)


def test_fmp_date_is_not_invented_publication_timestamp():
    request = TranscriptRequest(provider="fmp", fiscal_year=2024, fiscal_quarter=1)
    payload = [{"symbol": "MOCK", "period": "Q1", "year": 2024, "date": "2024-02-02", "content": "Mock Data"}]
    evidence = normalize_fmp(payload, symbol="MOCK", request=request, observed_at=NOW)
    assert evidence.call_at is None and evidence.published_at is None
    assert evidence.raw_payload[0]["date"] == "2024-02-02"


def india_row():
    return {"symbol": "MOCK", "sm_isin": "INE000000000", "seq_id": "one", "desc": "Mock Data filing",
        "an_dt": "18-Oct-2023 22:11:42", "exchdisstime": "18-Oct-2023 22:11:48",
        "attchmntFile": "https://nsearchives.nseindia.com/corporate/mock.pdf"}


def test_india_submission_publication_identity_and_bse_unknown_attachment():
    item = normalize_india_filing("NSE", india_row())
    assert (item.published_at - item.submitted_at).total_seconds() == 6
    assert item.published_at.hour == 16
    with pytest.raises(SourceAdapterError):
        assert_filing_identity(item, symbol="WRONG", isin=None, scrip_code=None)
    bse = normalize_india_filing("BSE", {"NEWSID": "one", "SCRIP_CD": 123456, "ATTACHMENTNAME": "mock.pdf"})
    assert bse.attachment_url is None
    assert "ATTACHMENT_LOCATION_REQUIRES_OFFICIAL_REFERENCE" in bse.warnings


@pytest.mark.parametrize("value", ["2025-01-01", "01-Jan-2025", "01-01-2025", "20250101"])
@pytest.mark.parametrize("exchange", ["NSE", "BSE"])
def test_india_date_only_metadata_does_not_invent_publication_time(exchange, value):
    row = {"symbol": "MOCK", "seq_id": "date-only", "an_dt": value, "exchdisstime": value} if exchange == "NSE" else {
        "NEWSID": "date-only", "SCRIP_CD": "123456", "News_submission_dt": value, "DissemDT": value}
    item = normalize_india_filing(exchange, row)
    assert item.submitted_at is None and item.published_at is None
    assert item.raw_payload == row
    assert "PUBLICATION_DATE_ONLY_PRECISE_TIME_UNKNOWN" in item.warnings
    assert "SUBMISSION_DATE_ONLY_PRECISE_TIME_UNKNOWN" in item.warnings


def test_explicit_india_midnight_is_still_a_real_timestamp():
    item = normalize_india_filing("NSE", {"symbol": "MOCK", "seq_id": "midnight", "exchdisstime": "2025-01-01T00:00:00+05:30"})
    assert item.published_at == datetime(2024, 12, 31, 18, 30, tzinfo=UTC)
    assert "PUBLICATION_DATE_ONLY_PRECISE_TIME_UNKNOWN" not in item.warnings


@pytest.mark.parametrize("url", ["http://127.0.0.1/a.pdf", "https://evil.example/a.pdf", "https://www.nseindia.com@evil.example/a.pdf"])
def test_india_attachment_references_are_bounded_to_exchange(url):
    row = india_row()
    row["attchmntFile"] = url
    with pytest.raises(SourceAdapterError):
        normalize_india_filing("NSE", row)


def test_alfred_revisions_and_missingness(monkeypatch):
    provider = FredProvider("not-a-real-key")
    rows = [
        {"date": "2024-01-01", "value": "1", "realtime_start": "2024-02-01", "realtime_end": "2024-03-01"},
        {"date": "2024-01-01", "value": "2", "realtime_start": "2024-03-02", "realtime_end": "9999-12-31"},
        {"date": "2024-02-01", "value": ".", "realtime_start": "2024-03-02", "realtime_end": "9999-12-31"},
    ]
    calls = []
    def get(endpoint, params):
        calls.append(params)
        if endpoint == "series":
            return {"seriess": [{"id": "MOCK", "units": "Billions of Dollars", "frequency": "Quarterly",
                "seasonal_adjustment": "Seasonally Adjusted Annual Rate", "realtime_start": params["realtime_start"],
                "realtime_end": params["realtime_end"]}]}
        return {"count": len(rows), "observations": rows}
    monkeypatch.setattr(provider, "_request", get)
    kwargs = dict(as_of=date(2024, 4, 1), observation_start=date(2024, 1, 1), observation_end=date(2024, 2, 1))
    result = provider.fetch_vintage_observations("mock", **kwargs)
    assert [row["value"] for row in result["observations"]] == [2, None]
    assert calls[0]["realtime_end"] == "2024-04-01" and calls[0]["output_type"] == 1
    result = provider.fetch_vintage_observations("mock", mode="initial_release", **kwargs)
    assert result["observations"][0]["value"] == 1
    assert set(result["series_basis"]) == {"2024-02-01", "2024-03-02"}
    assert result["observations"][0]["series_basis"]["seasonal_adjustment"] == "Seasonally Adjusted Annual Rate"
    assert result["transformation"] == "lin" and result["complete"]


def test_alfred_partial_and_changed_page_count(monkeypatch):
    provider = FredProvider("not-a-real-key")
    row = {"date": "2024-01-01", "value": "0", "realtime_start": "2024-02-01", "realtime_end": "9999-12-31"}
    monkeypatch.setattr(provider, "_request", lambda *args: {"count": 1001, "observations": [row] * 1000})
    kwargs = dict(as_of=date(2024, 4, 1), observation_start=date(2024, 1, 1), observation_end=date(2024, 1, 1))
    result = provider.fetch_vintage_observations("MOCK", max_pages=1, **kwargs)
    assert result["complete"] is False and "VINTAGE_PAGE_BUDGET_EXHAUSTED" in result["warnings"] and "VINTAGE_SERIES_BASIS_UNAVAILABLE" in result["warnings"]
    responses = iter([{"count": 1001, "observations": [row] * 1000}, {"count": 1000, "observations": [row]}])
    monkeypatch.setattr(provider, "_request", lambda *args: next(responses))
    with pytest.raises(RuntimeError, match="pagination"):
        provider.fetch_vintage_observations("MOCK", **kwargs)


@pytest.mark.parametrize("mode", ["as_of", "initial_release"])
@pytest.mark.parametrize("changed", ["value", "realtime_end"])
def test_alfred_rejects_conflicting_unselected_revisions_across_pages(monkeypatch, mode, changed):
    """Mock Data: even an expired or unselected revision must not contradict itself."""
    provider = FredProvider("not-a-real-key")
    older = {"date": "2024-01-01", "value": "1", "realtime_start": "2024-02-01", "realtime_end": "2024-03-01"}
    newer = {**older, "value": "2", "realtime_start": "2024-03-02", "realtime_end": "9999-12-31"}
    conflict = {**older, changed: "3" if changed == "value" else "2024-02-28"}
    rows = [newer, older, conflict] if mode == "as_of" else [older, newer, {**newer, changed: "3" if changed == "value" else "2024-04-01"}]
    pages = iter([{"count": 3, "offset": 0, "observations": rows[:2]}, {"count": 3, "offset": 2, "observations": rows[2:]}])
    monkeypatch.setattr(provider, "_request", lambda *args: next(pages))
    with pytest.raises(RuntimeError, match="conflicting vintage"):
        provider.fetch_vintage_observations("MOCK", as_of=date(2024, 4, 1), observation_start=date(2024, 1, 1), observation_end=date(2024, 1, 1), mode=mode)


@pytest.fixture
def source_client(db):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: {"id": "source-owner"}
    with TestClient(app) as client:
        yield client


@pytest.fixture
def company(db):
    company = Company(name="Mock Data", ticker="MOCK", local_symbol="MOCK", primary_exchange="NASDAQ", market="US", currency="USD", cik="320193")
    db.add(company)
    db.commit()
    return company


def test_router_authentication_and_capability_read_does_not_ingest(db):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        assert client.get("/api/source-adapters").status_code == 401
    assert list(db.scalars(select(ProcessingRun))) == []


def test_india_intake_idempotence_and_atomic_identity_failure(source_client, company, db):
    company.market, company.primary_exchange, company.isin = "IN", "NSE", "INE000000000"
    db.commit()
    url = f"/api/companies/{company.id}/source-adapters/india-filings"
    response = source_client.post(url, json={"exchange": "NSE", "records": [india_row(), india_row()]})
    assert response.status_code == 200, response.text
    result = response.json()["data"]
    assert result["created_count"] == 1 and result["duplicate_count"] == 1
    assert db.get(ProcessingRun, result["processing_run_id"]).metadata_json["user_id"] == "source-owner"
    assert source_client.post(url, json={"exchange": "NSE", "records": [india_row()]}).json()["data"]["created_count"] == 0
    wrong = {**india_row(), "symbol": "WRONG", "seq_id": "two"}
    response = source_client.post(url, json={"exchange": "NSE", "records": [{**india_row(), "seq_id": "new"}, wrong]})
    assert response.status_code == 422
    assert len(list(db.scalars(select(RawDocument)))) == 1


def test_india_date_precision_is_preserved_in_document_and_run(source_client, company, db):
    company.market, company.primary_exchange = "IN", "NSE"
    db.commit()
    row = {"symbol": "MOCK", "seq_id": "date-only", "exchdisstime": "2025-01-01"}
    response = source_client.post(f"/api/companies/{company.id}/source-adapters/india-filings", json={"exchange": "NSE", "records": [row]})
    assert response.status_code == 200, response.text
    result = response.json()["data"]
    document = db.get(RawDocument, result["raw_document_ids"][0])
    assert document.published_at is None and document.raw_payload_json["publication_time_known"] is False
    assert document.raw_payload_json["raw_response"] == row
    context = db.get(ProcessingRun, result["processing_run_id"]).metadata_json["request_context"]
    assert context["parameters"] == {"exchange": "NSE", "record_count": 1}
    assert "records" not in context["parameters"]


@pytest.mark.parametrize("market,exchange", [("IN", "NSE"), ("US", None), ("US", "NSE")])
def test_fmp_transcripts_reject_unresolved_or_non_us_listings_before_fetch(source_client, company, db, monkeypatch, market, exchange):
    company.market, company.primary_exchange = market, exchange
    db.commit()
    calls = []
    monkeypatch.setattr(workflows, "fetch_transcript", lambda **kwargs: calls.append(kwargs))
    response = source_client.post(f"/api/companies/{company.id}/source-adapters/transcript",
        json={"provider": "fmp", "fiscal_year": 2024, "fiscal_quarter": 1})
    assert response.status_code == 422, response.text
    error = response.json()["errors"][0]
    assert error["code"] == "FMP_TRANSCRIPT_LISTING_UNSUPPORTED" and not calls
    assert list(db.scalars(select(RawDocument))) == []
    run = db.get(ProcessingRun, error["processing_run_id"])
    assert run.status == "failed"
    assert run.metadata_json["request_context"]["company_listing"]["market"] == market


def test_fmp_transcript_supported_us_listing_retains_request_scope(source_client, company, db, monkeypatch):
    calls = []
    def fetch(**kwargs):
        calls.append(kwargs)
        return normalize_fmp([{"symbol": "MOCK", "period": "Q1", "year": 2024, "date": "2024-02-02", "content": "Mock Data"}],
            symbol=kwargs["symbol"], request=kwargs["request"], observed_at=NOW)
    monkeypatch.setattr(workflows, "fetch_transcript", fetch)
    response = source_client.post(f"/api/companies/{company.id}/source-adapters/transcript",
        json={"provider": "fmp", "fiscal_year": 2024, "fiscal_quarter": 1})
    assert response.status_code == 200, response.text
    assert calls[0]["symbol"] == "MOCK" and calls[0]["exchange"] == "NASDAQ"
    context = db.get(ProcessingRun, response.json()["data"]["processing_run_id"]).metadata_json["request_context"]
    assert context["parameters"]["fiscal_year"] == 2024 and context["parameters"]["level"] == 1
    assert context["company_listing"]["provider_symbol"] == "MOCK"
    assert context["company_listing"]["primary_exchange"] == "NASDAQ"


def test_transcript_versions_and_provider_failure_are_audited(source_client, company, db, monkeypatch):
    request = TranscriptRequest(provider="earningscall", fiscal_year=2024, fiscal_quarter=1)
    def fake_fetch(**kwargs):
        return normalize_earningscall(transcript_payload(), symbol="MOCK", exchange="NASDAQ", request=request, observed_at=NOW)
    monkeypatch.setattr(workflows, "fetch_transcript", fake_fetch)
    url = f"/api/companies/{company.id}/source-adapters/transcript"
    first = source_client.post(url, json=request.model_dump()).json()["data"]
    repeat = source_client.post(url, json=request.model_dump()).json()["data"]
    assert first["created_count"] == 1 and repeat["duplicate_count"] == 1
    monkeypatch.setattr(workflows, "fetch_transcript", lambda **kwargs: normalize_earningscall(transcript_payload("Mock Data corrected"),
        symbol="MOCK", exchange="NASDAQ", request=request, observed_at=NOW))
    changed = source_client.post(url, json=request.model_dump()).json()["data"]
    previous = db.get(RawDocument, first["raw_document_ids"][0])
    new = db.get(RawDocument, changed["raw_document_ids"][0])
    assert new.raw_payload_json["supersedes_raw_document_id"] == previous.id
    assert previous.raw_text == "Mock Data guidance text" and previous.published_at is None
    monkeypatch.setattr(workflows, "fetch_transcript", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("secret=private")))
    failed = source_client.post(url, json=request.model_dump())
    assert failed.status_code == 502 and "secret" not in failed.text
    assert db.get(ProcessingRun, failed.json()["errors"][0]["processing_run_id"]).status == "failed"


def test_actual_edgartools_parser_and_bounded_worker():
    if not dependency_version("edgartools"):
        pytest.skip("optional edgartools not installed")
    original = parse_company_facts(facts(), as_of="2024-03-01", currency="USD")
    assert sorted(c["value"] for c in original["candidates"]) == [0, 100]
    revised = run_extraction("edgartools", json.dumps(facts()).encode(), options={"as_of": "2024-07-01", "currency": "USD"})
    assert sorted(c["value"] for c in revised["candidates"]) == [0, 110]


def test_actual_camelot_worker_preserves_original_page_and_period_guard():
    if not dependency_version("camelot"):
        pytest.skip("optional camelot not installed")
    content = (Path(__file__).parents[1] / "fixtures/financial_statement_table.pdf").read_bytes()
    result = run_extraction("camelot", content, pages=[1])
    assert result["page_count"] == 1 and result["table_count"] >= 1
    assert result["candidates"]
    assert all(c["source_page"] == 1 and "period_context" in c["source_locator_json"] for c in result["candidates"])


def test_kernel_network_denial_is_in_child_only():
    code = "from app.providers.extraction.worker import deny_network; import socket; deny_network();\ntry: socket.socket()\nexcept PermissionError: print('blocked')"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0 and result.stdout.strip() == "blocked", result.stderr


def test_optional_model_absence_is_explicit(monkeypatch):
    monkeypatch.setattr("app.providers.extraction.jobs.dependency_version", lambda adapter, *args: "test-version")
    with pytest.raises(SourceAdapterError) as exc:
        run_extraction("docling", b"%PDF-Mock Data", pages=[1], model_dir=None)
    assert exc.value.code == "EXTRACTION_MODELS_MISSING"


def test_sec_api_creates_review_candidates_without_promoting_and_preserves_revision(source_client, company, db, monkeypatch):
    if not dependency_version("edgartools"):
        pytest.skip("optional edgartools not installed")
    monkeypatch.setattr(workflows, "fetch_company_facts", lambda *args, **kwargs: facts())
    url = f"/api/companies/{company.id}/source-adapters/sec-facts"
    first = source_client.post(url, json={"as_of": "2024-03-01"})
    assert first.status_code == 200, first.text
    assert first.json()["data"]["created_count"] == 2
    rows = list(db.scalars(select(FinancialExtractionCandidate)))
    assert all(row.review_status == "needs_review" and row.period_type == "annual" for row in rows)
    original = next(row for row in rows if row.metric_code == "revenue")
    original.review_status = "reviewed"
    db.commit()
    repeated = source_client.post(url, json={"as_of": "2024-03-02"})
    assert repeated.json()["data"]["created_count"] == 0
    first_context = db.get(ProcessingRun, first.json()["data"]["processing_run_id"]).metadata_json["request_context"]
    repeated_context = db.get(ProcessingRun, repeated.json()["data"]["processing_run_id"]).metadata_json["request_context"]
    assert first_context["parameters"] == {"as_of": "2024-03-01", "max_years": 5}
    assert repeated_context["parameters"] == {"as_of": "2024-03-02", "max_years": 5}
    revised = source_client.post(url, json={"as_of": "2024-07-01"})
    assert revised.json()["data"]["created_count"] == 1
    db.refresh(original)
    assert original.value == 100 and original.review_status == "reviewed"
    assert list(db.scalars(select(FinancialMetric))) == []
    document = db.get(RawDocument, original.raw_document_id)
    raw_bytes = json.dumps(document.raw_payload_json["raw_response"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    assert hashlib.sha256(raw_bytes).hexdigest() == document.raw_payload_json["payload_sha256"]
    from app.services.dated_financial_inputs import dated_financial_inputs
    from app.services.financial_extraction import promote_reviewed_candidates
    def revenue(day):
        report = dated_financial_inputs(db, company.id, valuation_date=day)
        return next(row for row in report["rows"] if row["metric"] == "revenue")
    assert revenue(date(2024, 3, 1))["status"] == "missing"
    assert promote_reviewed_candidates(db, company.id) == 1
    assert revenue(date(2024, 1, 31))["selected_revision_id"] is None
    selected = revenue(date(2024, 3, 1))
    assert selected["original_value"] == 100 and selected["original_unit"] == "USD"
    assert selected["sources"][0]["locator"]["source_provider"] == "SEC EDGAR"


def test_pdf_api_uses_original_bytes_and_never_rewrites_review(source_client, company, db, monkeypatch):
    if not dependency_version("camelot"):
        pytest.skip("optional camelot not installed")
    source = Source(name="Mock Data PDFs", source_type="manual")
    db.add(source)
    db.flush()
    document = RawDocument(company_id=company.id, source_id=source.id, document_type="annual_report", title="Mock Data PDF", content_hash="mock-data-pdf")
    db.add(document)
    db.flush()
    content = (Path(__file__).parents[1] / "fixtures/financial_statement_table.pdf").read_bytes()
    asset = DocumentAsset(raw_document_id=document.id, original_filename="mock.pdf", mime_type="application/pdf",
        size_bytes=len(content), sha256=hashlib.sha256(content).hexdigest(), content=content, page_count=1)
    db.add(asset)
    db.commit()
    url = f"/api/companies/{company.id}/source-adapters/documents/{document.id}/extract"
    result = source_client.post(url, json={"adapter": "camelot", "pages": [1]})
    assert result.status_code == 200, result.text
    assert result.json()["data"]["created_count"] > 0
    row = db.get(FinancialExtractionCandidate, result.json()["data"]["candidate_ids"][0])
    assert row.review_status == "needs_review" and row.period_type == "annual"
    again = source_client.post(url, json={"adapter": "camelot", "pages": [1]})
    assert again.json()["data"]["created_count"] == 0
    monkeypatch.setattr(workflows, "run_extraction", lambda *args, **kwargs: {"candidates": [], "table_count": 0,
        "scanned_pages": [1], "page_count": 1, "dependency_version": "Mock Data", "warnings": []})
    empty = source_client.post(url, json={"adapter": "camelot", "pages": [1]})
    assert empty.status_code == 200 and empty.json()["data"]["candidate_ids"] == []
    context = db.get(ProcessingRun, empty.json()["data"]["processing_run_id"]).metadata_json["request_context"]
    assert context["parameters"] == {"adapter": "camelot", "document_id": document.id, "pages": [1]}
    db.refresh(asset)
    assert asset.content == content
    asset.sha256 = "0" * 64
    db.commit()
    invalid = source_client.post(url, json={"adapter": "camelot", "pages": [1]})
    assert invalid.status_code == 409 and invalid.json()["errors"][0]["code"] == "SOURCE_INTEGRITY_FAILED"


def test_fixed_transport_sanitizes_provider_errors(monkeypatch):
    import urllib.error
    from app.providers.research_sources import http
    class Opener:
        def open(self, request, timeout):
            assert request.full_url.startswith("https://api.earningscall.dev/v4/transcript?")
            raise urllib.error.HTTPError(request.full_url, 403, "secret key", {}, None)
    monkeypatch.setattr(http.urllib.request, "build_opener", lambda *args: Opener())
    with pytest.raises(SourceAdapterError) as error:
        http.fetch_transcript_json("earningscall", {"apikey": "secret-key"})
    assert error.value.code == "PROVIDER_ENTITLEMENT" and "secret" not in str(error.value)


def test_alfred_api_persists_vintage_without_current_macro_rewrite(source_client, db, monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "mock-key")
    from app.core.config import get_settings
    from app.models.macro import MacroObservation
    get_settings.cache_clear()
    monkeypatch.setattr(FredProvider, "_request", lambda *args: {"count": 1, "observations": [
        {"date": "2024-01-01", "value": ".", "realtime_start": "2024-02-01", "realtime_end": "9999-12-31"}]})
    response = source_client.post("/api/source-adapters/fred-vintage", json={"series_id": "MOCK", "as_of": "2024-04-01",
        "observation_start": "2024-01-01", "observation_end": "2024-01-01"})
    assert response.status_code == 200, response.text
    result = response.json()["data"]
    assert result["details"]["observations"][0]["value"] is None
    assert db.get(RawDocument, result["raw_document_ids"][0]).document_type == "macro_vintage"
    assert list(db.scalars(select(MacroObservation))) == []


def test_alfred_partial_duplicate_keeps_partial_run_and_exact_counts(source_client, db, monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "mock-key")
    from app.core.config import get_settings
    get_settings.cache_clear()
    row = {"date": "2024-01-01", "value": "1", "realtime_start": "2024-02-01", "realtime_end": "9999-12-31"}
    monkeypatch.setattr(FredProvider, "_request", lambda *args: {"count": 1001, "observations": [row] * 1000})
    request = {"series_id": "MOCK", "as_of": "2024-04-01", "observation_start": "2024-01-01", "observation_end": "2024-01-01", "max_pages": 1}
    first = source_client.post("/api/source-adapters/fred-vintage", json=request)
    repeat = source_client.post("/api/source-adapters/fred-vintage", json=request)
    assert first.status_code == repeat.status_code == 200
    assert first.json()["data"]["status"] == repeat.json()["data"]["status"] == "partial"
    result = repeat.json()["data"]
    run = db.get(ProcessingRun, result["processing_run_id"])
    assert run.status == "partial_success"
    assert run.fetched_count == 1000 and run.created_count == 0 and run.skipped_duplicate_count == 1
    assert run.error_count == 1
    assert run.metadata_json["request_context"]["parameters"] == {**request, "mode": "as_of"}
    assert "mock-key" not in json.dumps(run.metadata_json)


def test_partial_action_without_usable_evidence_is_recorded_as_failed(db):
    result = workflows.audited_action(db, adapter="alfred", company_id=None, user_id="source-owner",
        action=lambda: SourceAdapterResult(adapter="alfred", status="partial", observed_at=NOW,
            warnings=["Mock Data: no usable vintage observations"]))
    run = db.get(ProcessingRun, result.processing_run_id)
    assert run.status == "failed" and run.error_count == 1
    assert result.status == "unavailable"


def test_audit_context_is_sanitized_and_frozen_before_execution(db):
    parameters = {"as_of": "2024-03-01", "max_years": 5,
        "apikey": "Mock Data secret", "records": [{"private": "Mock Data request body"}]}
    def action():
        parameters["max_years"] = 1
        return SourceAdapterResult(adapter="edgartools", observed_at=NOW)
    result = workflows.audited_action(db, adapter="edgartools", company_id=None, user_id="source-owner",
        action=action, request_context=parameters)
    context = db.get(ProcessingRun, result.processing_run_id).metadata_json["request_context"]
    assert context == {"parameters": {"as_of": "2024-03-01", "max_years": 5}}


def test_nse_original_financial_results_shape_preserves_period_scope():
    item = normalize_india_filing("NSE", {"symbol": "MOCK", "seqNumber": "123", "isin": "INE000000000",
        "broadCastDate": "16-Jan-2025 20:20:21", "exchdisstime": "16-Jan-2025 20:20:54",
        "period": "Quarterly", "fromDate": "01-Oct-2024", "toDate": "31-Dec-2024",
        "consolidated": "Non-Consolidated", "audited": "Un-Audited", "relatingTo": "Third Quarter",
        "xbrl": "https://nsearchives.nseindia.com/corporate/xbrl/mock.xml"})
    assert item.document_type == "quarterly_result" and item.period_start == date(2024, 10, 1)
    assert item.period_end == date(2024, 12, 31) and item.consolidated == "Non-Consolidated"
    assert item.isin == "INE000000000" and (item.published_at - item.submitted_at).total_seconds() == 33


def test_selected_interpreter_dependency_probe_is_real_and_bounded():
    if dependency_version("camelot"):
        assert dependency_version("camelot", sys.executable) == dependency_version("camelot")
    assert dependency_version("docling", "/not/a/configured/python") is None


@pytest.mark.parametrize("versions", [
    {"marker-pdf": "2.2.0", "surya-ocr": "0.23.0", "Pillow": "10.4.0", "filelock": "3.32.0"},
    {"marker-pdf": "2.2.0", "surya-ocr": "0.23.0", "Pillow": "13.0.0", "filelock": "4.2.12"},
    {"marker-pdf": "2.2.0", "surya-ocr": None, "Pillow": "13.0.0", "filelock": "4.2.12"},
])
def test_marker_dependency_conflict_blocks_before_worker(monkeypatch, versions):
    from app.providers.extraction import jobs
    monkeypatch.setattr(jobs, "dependency_version", lambda *args: "2.2.0")
    monkeypatch.setattr(jobs, "_marker_versions", lambda *args: versions)
    monkeypatch.setattr(jobs.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("Blocked dependencies must not launch a model worker"))
    with pytest.raises(SourceAdapterError) as error:
        run_extraction("marker", b"%PDF-Mock Data", pages=[1])
    assert error.value.code == "EXTRACTION_DEPENDENCY_CONFLICT" and error.value.status_code == 503


def test_marker_capability_exposes_dependency_conflict(source_client, monkeypatch):
    from app.api.routers import source_adapters
    monkeypatch.setattr(source_adapters, "dependency_version", lambda *args: "2.2.0")
    monkeypatch.setattr(source_adapters, "extraction_dependency_conflict", lambda adapter, *args: "Mock Data dependency conflict" if adapter == "marker" else None)
    result = source_client.get("/api/source-adapters")
    marker = next(item for item in result.json()["data"] if item["adapter"] == "marker")
    assert marker["available"] is False and marker["status"] == "dependency_conflict"
    assert "Mock Data dependency conflict" in marker["warnings"]


def test_marker_version_probe_uses_selected_interpreter_without_importing_models():
    from app.providers.extraction.jobs import _marker_versions
    assert _marker_versions(sys.executable) == _marker_versions()
    assert _marker_versions("/not/a/configured/python") == {}


@pytest.mark.parametrize("headers,body,code", [
    ({"Content-Length": str(9 * 1024 * 1024)}, b"{}", "RESPONSE_LIMIT"),
    ({"Content-Encoding": "gzip"}, b"{}", "RESPONSE_LIMIT"),
    ({}, b"not json private provider body", "PROVIDER_RESPONSE_INVALID"),
])
def test_transcript_transport_bounds_and_safe_parse_failure(monkeypatch, headers, body, code):
    from app.providers.research_sources import http
    class Response:
        def __init__(self):
            self.headers, self.sent = headers, False
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read1(self, size):
            if self.sent:
                return b""
            self.sent = True
            return body
    class Opener:
        def open(self, *args, **kwargs):
            return Response()
    monkeypatch.setattr(http.urllib.request, "build_opener", lambda *args: Opener())
    with pytest.raises(SourceAdapterError) as error:
        http.fetch_transcript_json("fmp", {"apikey": "secret-key"})
    assert error.value.code == code
    assert "private" not in str(error.value) and "secret" not in str(error.value)

def test_alfred_units_change_preserves_both_raw_receipts(source_client, db, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("FRED_API_KEY", "mock-key")
    get_settings.cache_clear()
    basis = {"units": "Index"}
    row = {"date": "2024-01-01", "value": "123.5", "realtime_start": "2024-02-01", "realtime_end": "9999-12-31"}

    def request(self, endpoint, params):
        if endpoint == "series":
            return {"seriess": [{"id": "MOCK", "realtime_start": params["realtime_start"],
                "realtime_end": params["realtime_end"], "frequency": "Monthly",
                "seasonal_adjustment": "Not Seasonally Adjusted", **basis}]}
        return {"count": 1, "observations": [row]}

    monkeypatch.setattr(FredProvider, "_request", request)
    payload = {"series_id": "MOCK", "as_of": "2024-04-01",
               "observation_start": "2024-01-01", "observation_end": "2024-01-01"}

    def ingest():
        response = source_client.post("/api/source-adapters/fred-vintage", json=payload)
        assert response.status_code == 200, response.text
        return response.json()["data"]

    first = ingest()
    basis["units"] = "Percent"
    revised = ingest()
    repeated = ingest()
    assert repeated["raw_document_ids"] == revised["raw_document_ids"]
    original_doc, revised_doc = (db.get(RawDocument, batch["raw_document_ids"][0]) for batch in (first, revised))
    assert revised_doc.raw_payload_json["supersedes_raw_document_id"] == original_doc.id
    assert original_doc.raw_payload_json["payload_sha256"] != revised_doc.raw_payload_json["payload_sha256"]
    for batch, unit in ((first, "Index"), (revised, "Percent")):
        observation = batch["details"]["observations"][0]
        assert batch["status"] == "success" and float(observation["value"]) == 123.5
        assert observation["basis_vintage"] == "2024-04-01" and observation["series_basis"]["units"] == unit
    basis.clear()
    unavailable = ingest()
    assert unavailable["status"] == "partial" and "VINTAGE_SERIES_BASIS_UNAVAILABLE" in unavailable["warnings"]
    assert unavailable["details"]["observations"][0]["series_basis"] is None
