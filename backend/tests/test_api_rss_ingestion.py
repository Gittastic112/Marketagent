from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import ProcessingRun, Source
from helpers import response_data


RSS_XML = """<rss version="2.0">
  <channel>
    <item>
      <title>Nvidia supply update</title>
      <link>https://example.com/nvda-supply</link>
      <description>Supply update.</description>
    </item>
  </channel>
</rss>
"""


@pytest.fixture
def client() -> Generator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    with TestingSessionLocal() as db:
        db.add(Source(name="Example RSS", source_type="rss"))
        db.commit()

    def override_get_db() -> Generator[Session]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_post_rss_ingestion_imports_supplied_xml(client: TestClient) -> None:
    response = client.post("/ingest/rss", json={"source_id": 1, "rss_xml": RSS_XML})

    assert response.status_code == 201
    body = response_data(response)
    assert body["fetched_count"] == 1
    assert body["created_count"] == 1
    assert body["skipped_duplicate_count"] == 0
    assert body["error_count"] == 0
    assert body["created"] == 1
    assert body["skipped_duplicates"] == 0
    assert body["events_created"] == 1
    assert body["events_skipped_existing"] == 0
    assert body["alerts_created"] == 0

    documents = response_data(client.get("/raw-documents"))
    events = response_data(client.get("/events"))

    assert documents[0]["title"] == "Nvidia supply update"
    assert documents[0]["document_type"] == "rss_item"
    assert events[0]["title"] == "Nvidia supply update"
    assert events[0]["event_type"] == "rss_news"
    assert events[0]["priority_score"] is not None


def test_post_rss_ingestion_persists_processing_run(client: TestClient) -> None:
    request_id = str(uuid4())
    response = client.post(
        "/ingest/rss",
        json={"source_id": 1, "rss_xml": RSS_XML},
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 201

    with next(app.dependency_overrides[get_db]()) as db:
        run = db.query(ProcessingRun).one()

    assert run.run_type == "rss_ingestion"
    assert run.request_id == request_id
    assert run.source_type == "rss"
    assert run.source_id == 1
    assert run.status == "success"
    assert run.fetched_count == 1
    assert run.created_count == 1
    assert run.skipped_duplicate_count == 0
    assert run.error_count == 0
    assert run.finished_at is not None

    runs_response = client.get("/processing-runs")
    assert runs_response.status_code == 200
    assert response_data(runs_response)[0]["run_type"] == "rss_ingestion"
    assert response_data(runs_response)[0]["request_id"] == request_id


def test_post_rss_ingestion_rejects_missing_source(client: TestClient) -> None:
    response = client.post("/ingest/rss", json={"source_id": 999, "rss_xml": RSS_XML})

    assert response.status_code == 404
    assert response.json()["detail"] == "Source not found"


def test_post_rss_ingestion_persists_failed_processing_run(client: TestClient) -> None:
    response = client.post("/ingest/rss", json={"source_id": 1, "rss_xml": "<rss><broken>"})

    assert response.status_code == 201
    assert response_data(response)["error_count"] == 1

    with next(app.dependency_overrides[get_db]()) as db:
        run = db.query(ProcessingRun).one()

    assert run.run_type == "rss_ingestion"
    assert run.status == "failed"
    assert run.fetched_count == 0
    assert run.created_count == 0
    assert run.error_count == 1
    assert run.error_details_json


def test_post_rss_feed_ingestion_fetches_source_base_url(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        text = RSS_XML

        def raise_for_status(self) -> None:
            return None

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        assert url == "https://example.com/feed.xml"
        return FakeResponse()

    monkeypatch.setattr("app.providers.rss_provider.fetch_public_text", lambda url, **kwargs: fake_get(url, **kwargs).text)
    client.patch("/sources/1", json={"base_url": "https://example.com/feed.xml"})

    response = client.post("/ingest/rss-feed", json={"source_id": 1})

    assert response.status_code == 201
    body = response_data(response)
    assert body["fetched_count"] == 1
    assert body["created_count"] == 1
    assert body["error_count"] == 0
    assert body["events_created"] == 1


def test_post_active_rss_feed_ingestion_runs_only_active_rss_sources(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def __init__(self, text: str) -> None:
            self.text = text

        def raise_for_status(self) -> None:
            return None

    calls: list[str] = []

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        calls.append(url)
        return FakeResponse(RSS_XML.replace("https://example.com/nvda-supply", f"{url}/nvda-supply"))

    monkeypatch.setattr("app.providers.rss_provider.fetch_public_text", lambda url, **kwargs: fake_get(url, **kwargs).text)

    client.patch("/sources/1", json={"base_url": "https://example.com/feed.xml", "active": True})
    client.post("/sources", json={"name": "Inactive RSS", "source_type": "rss", "base_url": "https://example.com/inactive.xml", "active": False})
    client.post("/sources", json={"name": "Manual", "source_type": "manual", "base_url": "https://example.com/manual.xml", "active": True})

    response = client.post("/ingest/rss-feeds/active")

    assert response.status_code == 201
    body = response_data(response)
    assert body["source_count"] == 1
    assert body["fetched_count"] == 1
    assert body["created_count"] == 1
    assert body["error_count"] == 0
    assert calls == ["https://example.com/feed.xml"]

    with next(app.dependency_overrides[get_db]()) as db:
        runs = db.query(ProcessingRun).order_by(ProcessingRun.id).all()

    assert len(runs) == 1
    assert runs[0].source_id == 1
