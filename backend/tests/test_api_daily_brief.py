from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Company, Event


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
        company = Company(ticker="AAPL", name="Apple Inc.")
        event = Event(
            company=company,
            event_type="manual_event",
            information_speed="medium",
            title="Manual event for brief",
            priority_score=70,
        )
        db.add_all([company, event])
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


def test_get_daily_brief_returns_rule_based_brief(client: TestClient) -> None:
    response = client.get("/daily-brief")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Daily Intelligence Brief"
    assert body["summary"] == "1 events, 0 alerts, 0 active thesis notes reviewed."
    assert body["top_events"][0]["title"] == "Manual event for brief"
    assert body["top_events"][0]["company"] == "AAPL"


def test_post_daily_brief_persists_brief(client: TestClient) -> None:
    response = client.post("/daily-brief")

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Daily Intelligence Brief"
    assert body["summary"] == "1 events, 0 alerts, 0 active thesis notes reviewed."
    assert body["payload_json"]["top_events"][0]["title"] == "Manual event for brief"


def test_list_saved_daily_briefs_returns_recent_saved_briefs(client: TestClient) -> None:
    client.post("/daily-brief")

    response = client.get("/daily-brief-history")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Daily Intelligence Brief"
    assert body[0]["summary"] == "1 events, 0 alerts, 0 active thesis notes reviewed."
