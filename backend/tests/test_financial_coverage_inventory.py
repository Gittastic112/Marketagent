from sqlalchemy import event

from app.models import Company, FinancialExtractionCandidate, RawDocument, Source
from app.services.financial_coverage_inventory import build_financial_coverage_inventory


def test_inventory_preserves_share_class_scope_and_has_no_writes(db):
    scope = {"version": 1, "selection_date": "2026-09-21", "securities": [
        {"ticker": "GOOG", "market": "US", "exchange": "NASDAQ", "currency": "USD", "security_type": "Class C", "research_universe": True},
        {"ticker": "GOOGL", "market": "US", "exchange": "NASDAQ", "currency": "USD", "security_type": "Class A", "research_universe": False},
        {"ticker": "BANK", "market": "IN", "exchange": "NSE", "currency": "INR", "security_type": "Equity", "research_universe": True}]}
    checklist = {"securities": [{"ticker": s["ticker"], "review_track": "bank_equity" if s["ticker"] == "BANK" else "operating_company"}
                                for s in scope["securities"]]}
    company = Company(ticker="GOOG", name="Mock Data C", market="US", primary_exchange="NASDAQ", currency="USD")
    bank = Company(ticker="BANK", name="Mock Data Bank", market="IN", primary_exchange="NSE", currency="INR")
    source = Source(name="Mock Data", source_type="manual")
    db.add_all([company, bank, source]); db.flush()
    doc = RawDocument(company_id=company.id, source_id=source.id, title="Mock Data", document_type="annual_report",
                      content_hash="mock-data-source", raw_payload_json={"payload_sha256": "mock-sha"})
    db.add(doc); db.flush()
    db.add(FinancialExtractionCandidate(company_id=company.id, raw_document_id=doc.id, metric_code="revenue",
        reported_label="Revenue", value=100, fiscal_year=2025, period_type="annual", source_text="Revenue 100", unit=None))
    db.commit()
    statements = []
    def record(_connection, _cursor, statement, *_args):
        statements.append(statement)
    event.listen(db.bind, "before_cursor_execute", record)
    try:
        report = build_financial_coverage_inventory(db, scope, checklist)
    finally:
        event.remove(db.bind, "before_cursor_execute", record)
    assert len(statements) == 6 and all(s.lstrip().upper().startswith("SELECT") for s in statements)
    goog, googl, bank_row = report["companies"]
    assert goog["candidate_count"] == 1 and goog["annual_candidates"]["2025"]["missing_unit_count"] == 1
    assert googl["identity_status"] == "missing" and googl["company_id"] is None
    assert "Bank equity" in " ".join(bank_row["blockers"])
    assert all(row["certification_status"] == "not_assessed" for row in report["companies"])
    assert not db.new and not db.dirty and not db.deleted


def test_inventory_records_missing_checklist_as_error(db):
    import pytest
    with pytest.raises(ValueError, match="review checklist"):
        build_financial_coverage_inventory(db, {"securities": [{"ticker": "UNKNOWN"}]}, {"securities": []})
