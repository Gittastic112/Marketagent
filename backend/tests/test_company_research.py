from datetime import UTC, datetime

from sqlalchemy import event

from app.models import Company, FilingSection, RawDocument, Source


def test_profiles_only_read_requested_companies_and_annual_business(client, db):
    company = Company(ticker="ABOUT", name="About company", sector="Technology")
    other = Company(ticker="OTHER", name="Other company")
    provider = Source(name="SEC", source_type="sec")
    db.add_all([company, other, provider])
    db.flush()
    annual = RawDocument(company_id=company.id, source_id=provider.id, document_type="sec_filing_metadata", raw_payload_json={"form_type": "10-K"},
        title="Annual filing", content_hash="annual-test", raw_text="Do not load the full filing",
        published_at=datetime(2025, 10, 30, tzinfo=UTC))
    quarterly = RawDocument(company_id=company.id, source_id=provider.id, document_type="10-Q",
        title="Quarterly financial statements, not a business description", content_hash="quarterly-test",
        published_at=datetime(2026, 2, 1, tzinfo=UTC))
    db.add_all([annual, quarterly])
    db.flush()
    db.add_all([FilingSection(raw_document_id=annual.id, item_name="Item 1", text_content="Stored business context " * 100, word_count=300),
                FilingSection(raw_document_id=quarterly.id, item_name="Item 1", text_content="Do not select quarterly statements " * 100, word_count=500)])
    db.commit()
    query_id = company.id
    queries = []
    def record(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(statement)
    event.listen(db.get_bind(), "before_cursor_execute", record)
    try:
        response = client.get(f"/company-research/profiles?company_id={query_id}")
    finally:
        event.remove(db.get_bind(), "before_cursor_execute", record)
    assert response.status_code == 200
    profile, = response.json()["data"]
    assert profile["name"] == "About company" and profile["business_status"] == "stored_excerpt"
    assert profile["document_title"] == "Annual filing" and len(profile["excerpt"]) <= 1400
    assert profile["source_href"] == f"/documents/{annual.id}/sections"
    assert len(queries) == 1
    assert "raw_documents.raw_text" not in queries[0]
    empty, = client.get(f"/company-research/profiles?company_id={other.id}").json()["data"]
    assert empty["business_status"] == "not_available" and empty["excerpt"] is None


def test_profile_selection_is_bounded(client):
    assert client.get("/company-research/profiles").status_code == 422
    assert client.get("/company-research/profiles?" + "&".join(f"company_id={i}" for i in range(51))).status_code == 422
