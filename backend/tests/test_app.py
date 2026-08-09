from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "status": "ok",
        "app": get_settings().app_name,
    }
    assert response.json()["errors"] == []
