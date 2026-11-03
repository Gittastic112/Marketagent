"""Private-source retrieval uses isolated Mock Data, never external providers."""
from hashlib import sha256

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select

from app.api.dependencies import get_current_user
from app.main import app
from app.models import AiOutput, BriefSource, Company, ProcessingRun, User, ValuationSetupDraft
from conftest import TEST_USER_ID


@pytest.fixture
def library(db):
    companies = [Company(ticker=ticker, name=f"Mock Data {ticker}", currency="USD") for ticker in ("FIRST", "SECOND")]
    db.add_all([*companies, User(id="another-owner", email="other@example.test", name="Other")])
    db.flush()
    company_ids = [company.id for company in companies]

    def add(title="Mock Data source", text="Original source text for a deterministic retrieval test.",
            company_id=None, user_id=TEST_USER_ID, kind="text", status="not_scanned"):
        digest = sha256(f"{title}:{text}:{kind}".encode()).hexdigest()
        source = BriefSource(user_id=user_id, company_id=company_id or company_ids[0], title=title,
            source_kind=kind, content_text=text, pdf_bytes=b"Mock Data PDF bytes" if kind == "pdf" else None,
            identity_hash=digest, source_sha256=digest, analysis_status=status,
            extraction_json={"character_count": len(text), "warnings": ["Mock Data"]})
        db.add(source)
        db.flush()
        return source.id

    return company_ids, add


def search(client, **params):
    response = client.get("/brief-sources/search", params=params)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "private, no-store"
    body = response.json()
    assert body["errors"] == [] and body["meta"]["source"] == "owned_user_supplied_sources"
    return body["data"]


def ids(page):
    return [row["id"] for row in page["items"]]


def test_pages_reach_every_source_without_repeats_when_new_sources_arrive(client, db, library):
    _, add = library
    original = [add(title=f"Mock Data source {index}") for index in range(45)]
    db.commit()
    first = search(client)
    assert ids(first) == original[-20:][::-1]
    newest = add(title="Mock Data inserted while paging")
    db.commit()
    second = search(client, before_id=first["next_before_id"])
    last = search(client, before_id=second["next_before_id"])
    assert ids(first) + ids(second) + ids(last) == original[::-1]
    assert last["next_before_id"] is None
    assert search(client)["items"][0]["id"] == newest
    # Existing callers retain the list-shaped latest-source contract.
    assert isinstance(client.get("/brief-sources").json()["data"], list)
    assert len(client.get("/brief-sources").json()["data"]) == 20


def test_search_matches_titles_and_original_text_before_applying_page_limit(client, db, library):
    _, add = library
    title_match = add(title="Mock Data Currency Outlook")
    text_match = add(title="Mock Data annual note", text="Original report discusses CURRENCY outlook and uncertainty.")
    for index in range(22):
        add(title=f"Mock Data unrelated {index}")
    db.commit()
    assert ids(search(client, q="  currency outlook  ")) == [text_match, title_match]
    assert search(client, q="does not exist") == {"items": [], "next_before_id": None}
    assert len(search(client, q="   ")["items"]) == 20


@pytest.mark.parametrize("term", ["50%", "under_score", "back\\slash", "<script>", "x' OR 1=1 --"])
def test_search_treats_wildcards_markup_and_sql_as_literal_text(client, db, library, term):
    _, add = library
    match = add(title=f"Mock Data {term}")
    add(title="Mock Data unrelated 500 underXscore backslash")
    db.commit()
    assert ids(search(client, q=term)) == [match]


def test_filters_intersect_and_cannot_disclose_other_owners(client, db, library):
    company_ids, add = library
    match = add(title="Mock Data margin note", company_id=company_ids[1], kind="pdf", status="failed")
    add(title="Mock Data margin text", company_id=company_ids[1], status="failed")
    add(title="Mock Data margin wrong company", kind="pdf", status="failed")
    add(title="Mock Data margin unscanned", company_id=company_ids[1], kind="pdf")
    other = add(title="Mock Data private margin", user_id="another-owner", company_id=company_ids[1], kind="pdf", status="failed")
    db.commit()
    filters = {"q": "margin", "company_id": company_ids[1], "source_kind": "pdf", "analysis_status": "failed"}
    assert ids(search(client, **filters)) == [match]
    assert ids(search(client, before_id=other, **filters)) == [match]
    assert search(client, q="private margin")["items"] == []
    assert search(client, company_id=99999)["items"] == []
    app.dependency_overrides[get_current_user] = lambda: {"id": "another-owner"}
    assert ids(search(client, **filters)) == [other]


def test_reads_are_bounded_and_never_fetch_original_bodies_or_write(client, db, library):
    _, add = library
    for index in range(8):
        add(title=f"Mock Data page {index}", kind="pdf")
    db.commit()
    db.expunge_all()
    statements, loaded = [], []

    def record(_connection, _cursor, statement, *_args):
        statements.append(statement)

    def source_loaded(source, _context):
        loaded.append(source.id)

    engine = db.get_bind()
    event.listen(engine, "before_cursor_execute", record)
    event.listen(BriefSource, "load", source_loaded)
    try:
        result = search(client, q="original", limit=3)
    finally:
        event.remove(engine, "before_cursor_execute", record)
        event.remove(BriefSource, "load", source_loaded)
    assert len(statements) <= 3 and len(loaded) == 4
    assert all(statement.lstrip().upper().startswith("SELECT") for statement in statements)
    for statement in statements:
        projection = statement.lower().split("from")[0]
        assert "content_text" not in projection and "pdf_bytes" not in projection
    for row in result["items"]:
        assert not {"text", "content_text", "pdf_bytes", "user_id"}.intersection(row)
        assert row["source_sha256"] and row["warnings"]
    for model in (AiOutput, ProcessingRun, ValuationSetupDraft):
        assert db.scalar(select(func.count()).select_from(model)) == 0


def test_cursor_is_absent_at_exact_page_boundary(client, db, library):
    _, add = library
    for index in range(3):
        add(title=f"Mock Data boundary {index}")
    db.commit()
    assert search(client, limit=3)["next_before_id"] is None
    assert search(client, before_id=1) == {"items": [], "next_before_id": None}


@pytest.mark.parametrize("params", [{"q": "x" * 201}, {"q": "has\x00null"}, {"company_id": 0},
    {"source_kind": "html"}, {"analysis_status": "approved"}, {"before_id": 0}, {"limit": 0}, {"limit": 51}])
def test_search_rejects_invalid_queries(client, params):
    assert client.get("/brief-sources/search", params=params).status_code == 422


def test_search_requires_authentication():
    override = app.dependency_overrides.pop(get_current_user)
    try:
        with TestClient(app) as client:
            assert client.get("/brief-sources/search").status_code == 401
    finally:
        app.dependency_overrides[get_current_user] = override
