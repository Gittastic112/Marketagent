from datetime import UTC, date, datetime

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
    fact(db, company, source, 110, datetime(2026, 11, 13, tzinfo=UTC), "later")
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
    fact(db, company, source, 110, datetime(2026, 11, 13, tzinfo=UTC), "later")
    db.commit()
    route = f"/companies/{company.id}/dated-inputs?valuation_date=2026-11-12"
    assert client.get(route).json()["data"]["rows"][0]["status"] == "unavailable_by_date"
    assert client.get(route + "&knowledge=latest_recorded").json()["data"]["rows"][0]["original_value"] == 110
    assert client.get(route + "&knowledge=guess").status_code == 422
