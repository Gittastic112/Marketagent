"""Reversible private-source organization, never evidence deletion or approval."""
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.api.dependencies import get_current_user
from app.main import app
from app.models import AiOutput, BriefSource, User, ValuationSetupDraft
from test_brief_sources import company, generated, mock_generation, paste, scan


def change(client, source_id, archived, version=1):
    return client.post(f"/brief-sources/{source_id}/lifecycle", json={
        "archived": archived, "expected_version": version,
    })


def test_archive_restore_preserves_evidence_and_review(client, db, company, monkeypatch):
    source_id = paste(client, company).json()["data"]["id"]
    mock_generation(monkeypatch, generated(source_id))
    original = scan(client, source_id).json()["data"]
    archived = change(client, source_id, True)
    assert archived.status_code == 200, archived.text
    assert archived.headers["cache-control"] == "private, no-store"
    saved = archived.json()["data"]
    assert saved["archived_at"] and saved["lifecycle_version"] == 2
    for key in ("source_sha256", "analysis", "ai_output_id", "generated_at", "review_status", "extraction"):
        assert saved[key] == original[key]
    assert client.get("/brief-sources").json()["data"] == []
    assert client.get("/brief-sources/search").json()["data"]["items"] == []
    for state in ("archived", "all"):
        rows = client.get("/brief-sources/search", params={"lifecycle": state}).json()["data"]["items"]
        assert [row["id"] for row in rows] == [source_id]
    assert client.get(f"/brief-sources/{source_id}").json()["data"]["text"]
    restored = change(client, source_id, False, 2).json()["data"]
    assert restored["archived_at"] is None and restored["lifecycle_version"] == 3
    assert restored["analysis"] == original["analysis"] and restored["review_status"] == "pending"
    assert client.get("/brief-sources").json()["data"][0]["id"] == source_id
    assert db.scalar(select(func.count()).select_from(ValuationSetupDraft)) == 0


def test_same_state_noop_and_stale_actions_cannot_undo_newer_decisions(client, company):
    source_id = paste(client, company).json()["data"]["id"]
    assert change(client, source_id, False).json()["data"]["lifecycle_version"] == 1
    assert change(client, source_id, True).status_code == 200
    assert change(client, source_id, True, 2).json()["data"]["lifecycle_version"] == 2
    assert change(client, source_id, False, 1).status_code == 409
    assert change(client, source_id, False, 2).status_code == 200
    assert change(client, source_id, True, 1).status_code == 409


def test_duplicates_never_unarchive_or_overwrite_original(client, company):
    original = paste(client, company).json()["data"]
    change(client, original["id"], True)
    duplicate = paste(client, company, title="Different title").json()["data"]
    assert duplicate["id"] == original["id"] and duplicate["archived_at"]
    assert duplicate["title"] == original["title"] and duplicate["lifecycle_version"] == 2
    assert client.get("/brief-sources").json()["data"] == []


def test_archived_pdf_remains_byte_identical_and_private(client, db, company):
    original = (Path(__file__).parent / "fixtures/financial_statement_table.pdf").read_bytes()
    response = client.post("/brief-sources/pdf", data={"company_id": company.id, "title": "Mock Data PDF"},
        files={"file": ("source.pdf", original, "application/pdf")})
    source_id = response.json()["data"]["id"]
    assert change(client, source_id, True).status_code == 200
    download = client.get(f"/brief-sources/{source_id}/pdf")
    assert download.content == original and download.headers["cache-control"] == "private, no-store"
    db.add(User(id="other-archive", email="other-archive@example.test", name="Other"))
    db.commit()
    app.dependency_overrides[get_current_user] = lambda: {"id": "other-archive"}
    assert change(client, source_id, False, 2).status_code == 404
    assert client.get(f"/brief-sources/{source_id}/pdf").status_code == 404
    assert client.get("/brief-sources/search?lifecycle=all").json()["data"]["items"] == []


def test_archive_blocks_new_scans_without_provider_calls(client, company, monkeypatch):
    source_id = paste(client, company).json()["data"]["id"]
    calls = []
    mock_generation(monkeypatch, generated(source_id), calls)
    change(client, source_id, True)
    assert scan(client, source_id).status_code == 409
    assert calls == []
    change(client, source_id, False, 2)
    assert scan(client, source_id).status_code == 200 and len(calls) == 1


def test_running_scan_blocks_archive_but_abandoned_scan_can_be_archived(client, db, company):
    source_id = paste(client, company).json()["data"]["id"]
    source = db.get(BriefSource, source_id)
    source.analysis_status, source.analysis_started_at = "scanning", datetime.now(UTC)
    db.commit()
    assert change(client, source_id, True).status_code == 409
    source.analysis_started_at = datetime.now(UTC) - timedelta(minutes=3)
    db.commit()
    result = change(client, source_id, True).json()["data"]
    assert result["archived_at"] and result["analysis_status"] == "failed"


@pytest.mark.parametrize("provider_fails", [False, True])
def test_late_scan_cannot_publish_after_archive_restore(client, db, company, monkeypatch, provider_fails):
    from app.providers.mock_provider import MockAIProvider
    from app.providers.base import AIProviderResult
    import json
    source_id = paste(client, company).json()["data"]["id"]

    def generate(*args):
        # Simulate another request recovering an abandoned provider attempt.
        source = db.get(BriefSource, source_id)
        source.analysis_started_at = datetime.now(UTC) - timedelta(minutes=3)
        db.commit()
        assert change(client, source_id, True).status_code == 200
        assert change(client, source_id, False, 2).status_code == 200
        if provider_fails:
            raise RuntimeError("Mock Data late failure")
        return AIProviderResult("fixture-model", json.dumps(generated(source_id)), "Mock Data", "medium")

    monkeypatch.setattr(MockAIProvider, "generate_structured_response", generate)
    assert scan(client, source_id).status_code == 409
    data = client.get(f"/brief-sources/{source_id}").json()["data"]
    assert data["analysis"] is None and data["lifecycle_version"] == 3
    assert data["analysis_status"] == "failed" and data["ai_output_id"] is None
    assert all(output.is_blocked or output.execution_status == "failed" for output in db.scalars(select(AiOutput)))


@pytest.mark.parametrize("provider_fails", [False, True])
def test_superseded_scan_cannot_damage_a_newer_success(client, db, company, monkeypatch, provider_fails):
    from app.providers.mock_provider import MockAIProvider
    from app.providers.base import AIProviderResult
    import json
    source_id = paste(client, company).json()["data"]["id"]
    calls = 0
    newer = None

    def generate(*args):
        nonlocal calls, newer
        calls += 1
        if calls == 1:
            source = db.get(BriefSource, source_id)
            source.analysis_started_at = datetime.now(UTC) - timedelta(minutes=3)
            db.commit()
            response = scan(client, source_id)
            assert response.status_code == 200
            newer = response.json()["data"]
            if provider_fails:
                raise RuntimeError("Mock Data superseded failure")
        return AIProviderResult("fixture-model", json.dumps(generated(source_id)), "Mock Data", "medium")

    monkeypatch.setattr(MockAIProvider, "generate_structured_response", generate)
    assert scan(client, source_id).status_code == 409
    result = client.get(f"/brief-sources/{source_id}").json()["data"]
    assert result["ai_output_id"] == newer["ai_output_id"] and result["analysis"] == newer["analysis"]
    assert result["analysis_status"] == "complete"
    assert db.get(AiOutput, newer["ai_output_id"]).is_blocked is False


def test_archived_filter_paginates_only_matching_owned_sources(client, company):
    archived = []
    for index in range(6):
        source_id = paste(client, company, text=f"Mock Data source {index}: original content for archive pagination.").json()["data"]["id"]
        if index % 2:
            change(client, source_id, True)
            archived.append(source_id)
    params = {"lifecycle": "archived", "company_id": company.id, "source_kind": "text", "q": "original content", "limit": 2}
    first = client.get("/brief-sources/search", params=params).json()["data"]
    second = client.get("/brief-sources/search", params={**params, "before_id": first["next_before_id"]}).json()["data"]
    assert [row["id"] for row in first["items"] + second["items"]] == archived[::-1]
    assert second["next_before_id"] is None


def test_lifecycle_requires_authentication(client, company):
    source_id = paste(client, company).json()["data"]["id"]
    override = app.dependency_overrides.pop(get_current_user)
    try:
        assert change(client, source_id, True).status_code == 401
    finally:
        app.dependency_overrides[get_current_user] = override


@pytest.mark.parametrize("payload", [{}, {"archived": "false", "expected_version": 1},
    {"archived": True, "expected_version": 0}, {"archived": True, "expected_version": 1, "user_id": "other"}])
def test_lifecycle_contract_is_strict(client, company, payload):
    source_id = paste(client, company).json()["data"]["id"]
    assert client.post(f"/brief-sources/{source_id}/lifecycle", json=payload).status_code == 422


def test_invalid_lifecycle_filter_is_rejected(client):
    assert client.get("/brief-sources/search?lifecycle=deleted").status_code == 422


def test_additive_migration_preserves_legacy_source_values():
    import importlib.util
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine, inspect, text
    migration = Path(__file__).parents[1] / "alembic/versions/r9r9r9r9r9r9_add_brief_source_lifecycle.py"
    spec = importlib.util.spec_from_file_location("source_lifecycle_migration", migration)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE brief_sources (id INTEGER PRIMARY KEY, content_text TEXT, pdf_bytes BLOB, analysis_json TEXT)"))
        original = {"body": "Mock Data immutable original", "pdf": b"original PDF bytes", "analysis": '{"review": "pending"}'}
        connection.execute(text("INSERT INTO brief_sources VALUES (1, :body, :pdf, :analysis)"), original)
        with Operations.context(MigrationContext.configure(connection)):
            module.upgrade()
        assert connection.execute(text("SELECT * FROM brief_sources")).one() == (1, *original.values(), None, 1)
        assert {column["name"] for column in inspect(connection).get_columns("brief_sources")} >= {"archived_at", "lifecycle_version"}
