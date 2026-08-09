from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.api.route_security import build_route_security_inventory
from app.main import app


def test_every_application_route_is_explicitly_public_or_authenticated() -> None:
    inventory = build_route_security_inventory(app)

    assert inventory
    assert all(item.classification in {"public", "authenticated"} for item in inventory)
    assert not [
        item
        for item in inventory
        if item.classification == "authenticated" and not item.has_auth_dependency
    ]
    assert {
        (item.method, item.path)
        for item in inventory
        if item.classification == "public"
    } == {
        ("GET", "/api/health"),
        ("GET", "/health"),
    }


def test_direct_backend_requests_cannot_bypass_authentication() -> None:
    authenticated_override = app.dependency_overrides.pop(get_current_user)
    try:
        with TestClient(app) as client:
            assert client.get("/api/health").status_code == 200
            assert client.get("/health").status_code == 200
            assert client.get("/companies").status_code == 401
            assert client.post("/companies", json={}).status_code == 401
            assert client.patch("/companies/1", json={}).status_code == 401
            assert client.delete("/companies/1").status_code == 401
    finally:
        app.dependency_overrides[get_current_user] = authenticated_override
