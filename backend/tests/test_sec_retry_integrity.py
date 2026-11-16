"""Mock Data SEC retries retain source identity, bytes and audit counts."""
from datetime import date

import pytest
from sqlalchemy import select

from app.models import Company, ProcessingRun, RawDocument, Source
from app.services import sec_ingestion as sec


def setup(db):
    company = Company(ticker="MOCKSEC", name="Mock Data SEC retry", cik="0000000001")
    source = Source(name="Mock Data SEC", source_type="sec")
    db.add_all([company, source]); db.commit()
    filing = sec.SecFilingMetadata("0000000001-26-000001", "10-K", date(2026, 1, 1),
        filing_url="https://www.sec.gov/Archives/edgar/data/1/000000000126000001/mock.htm")
    return company, source, filing


@pytest.mark.parametrize("first_fails", [False, True])
def test_missing_text_retry_completes_the_same_document_and_preserves_identity(db, monkeypatch, first_fails):
    company, source, filing = setup(db)
    def unavailable(*args, **kwargs):
        raise TimeoutError("Mock Data fetch failure")
    monkeypatch.setattr(sec, "fetch_sec_filing_text", unavailable)
    first = sec.ingest_sec_filing_metadata(db, source.id, company.id, [filing], download_text=first_fails)
    document = db.scalar(select(RawDocument))
    identity = (document.id, document.content_hash, document.created_at, document.url, document.published_at)
    assert first.created_count == 1 and first.error_count == int(first_fails)
    monkeypatch.setattr(sec, "fetch_sec_filing_text", lambda *args, **kwargs: "Mock Data recovered filing")
    second = sec.ingest_sec_filing_metadata(db, source.id, company.id, [filing], download_text=True)
    db.refresh(document)
    assert document.raw_text == "Mock Data recovered filing"
    assert second.completed_text_count == 1 and second.created_count == 0
    assert second.skipped_duplicate_count == second.error_count == 0
    assert (document.id, document.content_hash, document.created_at, document.url, document.published_at) == identity
    assert document.raw_payload_json["text_downloaded"] is True
    third = sec.ingest_sec_filing_metadata(db, source.id, company.id, [filing], download_text=True)
    assert third.completed_text_count == 0 and third.skipped_duplicate_count == 1


def test_repeated_batch_is_idempotent_with_production_autoflush_false(db):
    company, source, filing = setup(db)
    assert db.autoflush is False
    result = sec.ingest_sec_filing_metadata(db, source.id, company.id, [filing, filing])
    assert result.created_count == 1 and result.skipped_duplicate_count == 1
    assert len(list(db.scalars(select(RawDocument)))) == 1


def test_failed_retry_does_not_claim_completion_or_modify_populated_source(db, monkeypatch):
    company, source, filing = setup(db)
    sec.ingest_sec_filing_metadata(db, source.id, company.id, [filing])
    document = db.scalar(select(RawDocument))
    monkeypatch.setattr(sec, "fetch_sec_filing_text", lambda *args, **kwargs: "   ")
    result = sec.ingest_sec_filing_metadata(db, source.id, company.id, [filing], download_text=True)
    assert result.error_count == 1 and result.completed_text_count == 0
    assert document.raw_text is None
    document.raw_text = "Mock Data original content"
    db.commit()
    result = sec.ingest_sec_filing_metadata(db, source.id, company.id, [filing], download_text=True)
    assert document.raw_text == "Mock Data original content" and result.skipped_duplicate_count == 1


def test_retry_response_and_processing_run_report_completion_without_new_sources(db, client, monkeypatch):
    company, source, filing = setup(db)
    sec.ingest_sec_filing_metadata(db, source.id, company.id, [filing])
    monkeypatch.setattr(sec, "fetch_sec_filing_text", lambda *args, **kwargs: "Mock Data recovered filing")
    response = client.post("/ingest/sec-filings", json={"company_id": company.id, "source_id": source.id,
        "download_text": True, "filings": [{"accession_number": filing.accession_number,
            "form_type": filing.form_type, "filing_date": filing.filing_date.isoformat(), "filing_url": filing.filing_url}]})
    assert response.status_code == 201
    assert response.json()["data"]["completed_text_count"] == 1
    assert response.json()["data"]["created_count"] == 0
    run = db.scalar(select(ProcessingRun))
    assert run.status == "success" and run.metadata_json["completed_text_count"] == 1
    assert len(list(db.scalars(select(RawDocument)))) == 1


def test_retry_keeps_stored_url_and_rejects_cross_company_completion(db, monkeypatch):
    from dataclasses import replace
    company, source, filing = setup(db)
    sec.ingest_sec_filing_metadata(db, source.id, company.id, [filing])
    fetched = []
    def fetch(url, **kwargs):
        fetched.append(url)
        return "Mock Data preserved identity"
    monkeypatch.setattr(sec, "fetch_sec_filing_text", fetch)
    other = Company(ticker="OTHER", name="Mock Data other company")
    db.add(other); db.commit()
    rejected = sec.ingest_sec_filing_metadata(db, source.id, other.id, [filing], download_text=True)
    assert rejected.error_count == 1 and fetched == []
    updated = sec.ingest_sec_filing_metadata(db, source.id, company.id,
        [replace(filing, filing_url="https://www.sec.gov/changed.htm")], download_text=True)
    assert updated.completed_text_count == 1 and fetched == [filing.filing_url]
