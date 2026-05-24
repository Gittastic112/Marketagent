from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Company, RawDocument, Source


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
        company = Company(ticker="AAPL", name="Apple")
        source = Source(name="Example RSS", source_type="rss")
        document = RawDocument(
            company=company,
            source=source,
            document_type="rss_item",
            title="Apple services headline",
            raw_text="Services update.",
            content_hash="api-event-extract-1",
        )
        db.add_all([company, source, document])
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


def test_post_extract_events_creates_events_from_raw_documents(client: TestClient) -> None:
    response = client.post("/extract/events")

    assert response.status_code == 201
    body = response.json()
    assert body["created"] == 1
    assert body["skipped_existing"] == 0

    events_response = client.get("/events")
    assert events_response.json()[0]["title"] == "Apple services headline"
