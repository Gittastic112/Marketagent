from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Source


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
    body = response.json()
    assert body["created"] == 1
    assert body["skipped_duplicates"] == 0


def test_post_rss_ingestion_rejects_missing_source(client: TestClient) -> None:
    response = client.post("/ingest/rss", json={"source_id": 999, "rss_xml": RSS_XML})

    assert response.status_code == 404
    assert response.json()["detail"] == "Source not found"
