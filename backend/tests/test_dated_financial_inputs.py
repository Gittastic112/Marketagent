from datetime import UTC, date, datetime

import pytest

from app.models import Company, FinancialExtractionCandidate, RawDocument, Source
from app.services.financial_period_basis import financial_period_basis
from app.services.source_fact_history import record_financial_fact_revision


def fact(db, company, source, value, published, suffix, **locator):
    document = RawDocument(company_id=company.id, source_id=source.id, title="Mock Data dated source",
        document_type="annual_report", content_hash=f"mock-dated-{suffix}", published_at=published,
        raw_text="Mock Data revenue")
    db.add(document); db.flush()
    candidate = FinancialExtractionCandidate(company_id=company.id, raw_document_id=document.id,
        metric_code="revenue", reported_label="Revenue", value=value, unit="USD million", fiscal_year=2025,
        period_type="annual", source_text="Mock Data revenue", extraction_method="mock",
        review_status="promoted", source_locator_json={"start": "2025-01-01", "end": "2025-12-31", **locator})
    db.add(candidate); db.flush()
    result = record_financial_fact_revision(db, candidate, effective_at=date(2025, 12, 31))
    db.flush()
    return result


def setup(db):
    company = Company(ticker="DATED", name="Mock Data dated company", currency="USD")
    source = Source(name="Mock Data source", source_type="filing")
    db.add_all([company, source]); db.flush()
    return company, source


def test_period_basis_preserves_unknowns_and_source_fields():
    candidate = FinancialExtractionCandidate(period_type="annual", fiscal_year=2025,
        source_locator_json={"end": "2025-09-30", "taxonomy": "us-gaap"})
    basis = financial_period_basis(candidate)
    assert basis["start"] is None and basis["instant"] is None
    assert basis["scope"] == "annual" and basis["accounting_basis"] == "us-gaap"
    assert candidate.source_locator_json == {"end": "2025-09-30", "taxonomy": "us-gaap"}


def test_dated_read_uses_publication_not_retrieval_and_keeps_unknowns(client, db):
    company, source = setup(db)
    original = fact(db, company, source, 100, datetime(2026, 2, 1, tzinfo=UTC), "original")
    fact(db, company, source, 110, datetime(2026, 11, 13, 5, tzinfo=UTC), "later")
    fact(db, company, source, 120, None, "unknown")
    db.commit()
    response = client.get(f"/companies/{company.id}/dated-inputs?valuation_date=2026-11-12")
    assert response.status_code == 200
    data = response.json()["data"]
    row = next(item for item in data["rows"] if item["metric"] == "revenue")
    assert row["status"] == "available" and row["selected_revision_id"] == original.id
    assert row["original_value"] == 100 and row["normalized_value"] == 100_000_000
    assert {item["availability"] for item in row["sources"]} == {"available_by_date", "published_later", "publication_unknown"}
    assert data["valuation_date"] == "2026-11-12"
    assert next(item for item in data["rows"] if item["metric"] == "debt")["status"] == "missing"
    assert db.query(FinancialExtractionCandidate).count() == 3


def test_same_date_conflicts_are_visible_and_never_silently_selected(client, db):
    company, source = setup(db)
    for i, value in enumerate([100, 101]):
        fact(db, company, source, value, datetime(2026, 2, 1, tzinfo=UTC), str(i))
    db.commit()
    row = client.get(f"/companies/{company.id}/dated-inputs?valuation_date=2026-11-12").json()["data"]["rows"][0]
    assert row["status"] == "conflict" and row["selected_revision_id"] is None
    assert row["original_value"] is None and len(row["sources"]) == 2


def test_later_knowledge_is_explicit_and_date_validation_is_strict(client, db):
    company, source = setup(db)
    fact(db, company, source, 110, datetime(2026, 11, 13, 5, tzinfo=UTC), "later")
    db.commit()
    route = f"/companies/{company.id}/dated-inputs?valuation_date=2026-11-12"
    assert client.get(route).json()["data"]["rows"][0]["status"] == "unavailable_by_date"
    assert client.get(route + "&knowledge=latest_recorded").json()["data"]["rows"][0]["original_value"] == 110
    assert client.get(route + "&knowledge=guess").status_code == 422


def test_sec_fact_filing_dates_are_independent_of_snapshot_publication(client, db):
    company, source = setup(db)
    revisions = []
    for suffix, filed, value in [("original", "2026-02-01", 100), ("cutoff", "2026-11-12", 105),
                                  ("later", "2026-11-13", 110), ("unknown", "invalid", 120)]:
        revisions.append(fact(db, company, source, value, None, suffix,
            type="xbrl_fact", filed=filed, accession=f"mock-{suffix}", payload_sha256="a" * 64))
    document = db.get(RawDocument, revisions[0].raw_document_id)
    document.document_type = "xbrl_facts"
    document.raw_payload_json = {"provider": "SEC EDGAR", "payload_sha256": "a" * 64}
    document.published_at = datetime(2026, 11, 15, tzinfo=UTC)  # Snapshot metadata is not the fact filing date.
    for revision in revisions:
        revision.raw_document_id = document.id
        candidate = db.get(FinancialExtractionCandidate, revision.financial_candidate_id)
        candidate.raw_document_id = document.id
        candidate.extraction_method = "sec_xbrl_v3"
    db.commit()
    before = [(r.id, r.observed_at, r.value) for r in revisions]
    response = client.get(f"/companies/{company.id}/dated-inputs?valuation_date=2026-11-12")
    assert response.status_code == 200
    row = response.json()["data"]["rows"][0]
    assert row["selected_revision_id"] == revisions[1].id and row["original_value"] == 105
    sources = {s["revision_id"]: s for s in row["sources"]}
    assert [sources[r.id]["availability"] for r in revisions] == [
        "available_by_date", "available_by_date", "published_later", "publication_unknown"]
    assert sources[revisions[1].id]["publication_date"] == "2026-11-12"
    assert sources[revisions[1].id]["publication_precision"] == "date"
    assert sources[revisions[1].id]["published_at"] is None
    assert sources[revisions[1].id]["locator"]["accession"] == "mock-cutoff"
    db.expire_all()
    assert [(r.id, r.observed_at, r.value) for r in revisions] == before
    assert document.published_at.date() == date(2026, 11, 15)


def test_unverified_sec_locator_does_not_create_a_publication_date(client, db):
    company, source = setup(db)
    revision = fact(db, company, source, 100, None, "unverified", type="xbrl_fact", filed="2026-01-01")
    db.commit()
    row = client.get(f"/companies/{company.id}/dated-inputs?valuation_date=2026-11-12").json()["data"]["rows"][0]
    assert row["status"] == "unavailable_by_date"
    assert row["sources"][0]["published_at"] is None

def test_edgartools_adapter_filing_date_requires_matching_archived_source(client, db):
    company, source = setup(db)
    url = "https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json"
    revision = fact(db, company, source, 100, None, "adapter", type="xbrl_fact", filed="2026-02-01",
        accession="0000000001-26-000001", payload_sha256="a" * 64, source_url=url, adapter_candidate_hash="b" * 64)
    document = db.get(RawDocument, revision.raw_document_id)
    document.document_type, document.url = "xbrl_facts", url
    document.raw_payload_json = {"source_kind": "source_adapter", "adapter": "edgartools", "payload_sha256": "a" * 64}
    db.get(FinancialExtractionCandidate, revision.financial_candidate_id).extraction_method = "edgartools_companyfacts_v1"
    db.commit()
    def lookup(day):
        return client.get(f"/companies/{company.id}/dated-inputs?valuation_date={day}").json()["data"]["rows"][0]
    assert lookup("2026-01-31")["status"] == "unavailable_by_date"
    selected = lookup("2026-02-01")
    assert selected["original_value"] == 100 and selected["sources"][0]["locator"]["parser"] == "edgartools"
    document.raw_payload_json = {**document.raw_payload_json, "payload_sha256": "c" * 64}
    db.commit()
    assert lookup("2026-02-01")["status"] == "unavailable_by_date"


@pytest.mark.parametrize(("research_day", "instant", "calendar_day", "eligible"), [
    ("2026-11-12", "2026-11-13T00:00:00Z", "2026-11-12", True),
    ("2026-11-12", "2026-11-13T04:59:59.999999Z", "2026-11-12", True),
    ("2026-11-12", "2026-11-13T05:00:00Z", "2026-11-13", False),
    ("2026-07-01", "2026-07-02T03:59:59Z", "2026-07-01", True),
    ("2026-07-01", "2026-07-02T04:00:00Z", "2026-07-02", False),
])
def test_true_publication_uses_new_york_calendar_day(client, db, research_day, instant, calendar_day, eligible):
    company, source = setup(db)
    fact(db, company, source, 100, datetime.fromisoformat(instant), "instant")
    db.commit()
    report = client.get(f"/companies/{company.id}/dated-inputs?valuation_date={research_day}").json()["data"]
    row = report["rows"][0]
    observation, = row["sources"]
    assert row["status"] == ("available" if eligible else "unavailable_by_date")
    assert observation["availability"] == ("available_by_date" if eligible else "published_later")
    assert observation["publication_date"] == calendar_day
    assert observation["publication_precision"] == "timestamp"
    assert datetime.fromisoformat(observation["published_at"]) == datetime.fromisoformat(instant)


def test_sec_calendar_filing_cannot_outrank_an_intraday_revision_without_a_time(client, db):
    company, source = setup(db)
    filing = fact(db, company, source, 100, datetime(2026, 11, 12, tzinfo=UTC), "sec")
    doc = db.get(RawDocument, filing.raw_document_id)
    doc.document_type = "sec_filing_metadata"
    doc.raw_payload_json = {"source_kind": "sec_edgar", "filing_date": "2026-11-12"}
    timed = fact(db, company, source, 110, datetime(2026, 11, 13, 2, tzinfo=UTC), "evening")
    db.commit()
    route = f"/companies/{company.id}/dated-inputs?valuation_date="
    prior = client.get(route + "2026-11-11").json()["data"]["rows"][0]
    assert prior["status"] == "unavailable_by_date"
    row = client.get(route + "2026-11-12").json()["data"]["rows"][0]
    assert row["status"] == "conflict" and row["selected_revision_id"] is None
    observations = {s["revision_id"]: s for s in row["sources"]}
    assert observations[filing.id]["publication_date"] == "2026-11-12"
    assert observations[filing.id]["published_at"] is None
    assert observations[timed.id]["publication_precision"] == "timestamp"
