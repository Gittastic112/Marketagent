from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Alert, Company, Event
from helpers import response_data


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
        company = Company(ticker="MSFT", name="Microsoft")
        event = Event(
            company=company,
            event_type="sec_filing",
            information_speed="slow",
            title="Microsoft 10-Q filed",
            priority_score=82,
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


def test_post_generate_alerts_creates_alerts_from_high_priority_events(client: TestClient) -> None:
    response = client.post("/generate/alerts")

    assert response.status_code == 201
    body = response_data(response)
    assert body["created"] == 1
    assert body["skipped_existing"] == 0
    assert body["skipped_below_threshold"] == 0

    alerts_response = client.get("/alerts")
    assert response_data(alerts_response)[0]["title"] == "Review: Microsoft 10-Q filed"
    with next(app.dependency_overrides[get_db]()) as db:
        alert = db.query(Alert).one()
    assert alert.user_id == "admin_user_id_fallback"
