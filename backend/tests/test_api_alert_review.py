from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

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


def create_alert(client: TestClient) -> dict:
    response = client.post("/alerts", json={"alert_type": "manual_alert", "title": "Review margin change"})
    assert response.status_code == 201
    return response.json()


def test_update_alert_review_status_sets_reviewed_at(client: TestClient) -> None:
    alert = create_alert(client)

    response = client.patch(f"/alerts/{alert['id']}", json={"review_status": "useful"})

    assert response.status_code == 200
    body = response.json()
    assert body["review_status"] == "useful"
    assert body["reviewed_at"] is not None


def test_update_alert_review_notes_sets_reviewed_at(client: TestClient) -> None:
    alert = create_alert(client)

    response = client.patch(f"/alerts/{alert['id']}", json={"review_notes": "Check next filing."})

    assert response.status_code == 200
    body = response.json()
    assert body["review_status"] == "unreviewed"
    assert body["review_notes"] == "Check next filing."
    assert body["reviewed_at"] is not None


def test_alert_rejects_invalid_review_status(client: TestClient) -> None:
    alert = create_alert(client)

    response = client.patch(f"/alerts/{alert['id']}", json={"review_status": "dismissed"})

    assert response.status_code == 422


def test_create_alert_rejects_invalid_review_status(client: TestClient) -> None:
    response = client.post(
        "/alerts",
        json={"alert_type": "manual_alert", "title": "Bad review status", "review_status": "reviewed"},
    )

    assert response.status_code == 422
