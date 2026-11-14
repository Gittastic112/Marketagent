from datetime import UTC, datetime

from app.models import Company, RawDocument, Source


def test_library_filters_counts_pages_and_keeps_unknown_publication_explicit(client, db):
    company = Company(ticker="LIB", name="Mock Data library")
    source = Source(name="Mock Data library source", source_type="filing")
    db.add_all([company, source]); db.flush()
    for i in range(5):
        db.add(RawDocument(company_id=company.id, source_id=source.id, title=f"Mock Data annual {i}",
            document_type="annual_report", content_hash=f"mock-library-{i}",
            published_at=datetime(2026, 2, 1, tzinfo=UTC) if i else None))
    db.commit()
    url = f"/raw-documents/library?company_id={company.id}&q=annual&limit=2"
    first = client.get(url).json()["data"]
    second = client.get(url + "&offset=2").json()["data"]
    assert first["total"] == second["total"] == 5
    assert len(first["items"]) == len(second["items"]) == 2
    assert not {r["id"] for r in first["items"]} & {r["id"] for r in second["items"]}
    assert client.get(url + "&published_to=2026-11-12").json()["data"]["total"] == 4
    assert client.get(url + "&review=needs_review").json()["data"]["total"] == 0
    assert client.get("/raw-documents/library?q=%25").json()["data"]["total"] == 0
    assert client.get(url + "&published_from=2027-01-01&published_to=2026-01-01").status_code == 422
    assert client.get("/raw-documents/library?limit=101").status_code == 422
