from fastapi.testclient import TestClient
from sqlalchemy import event as sqlalchemy_event
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.routers.dashboard import DASHBOARD_QUERY_BUDGET, DASHBOARD_RESPONSE_BUDGET_MS
from app.main import app
from helpers import response_data


def _use_user(user_id: str) -> None:
    app.dependency_overrides[get_current_user] = lambda: {
        "id": user_id,
        "email": f"{user_id}@example.com",
        "name": user_id,
    }


def test_dashboard_overview_consolidates_data_and_enforces_ownership(
    client: TestClient,
    db_session: Session,
) -> None:
    company = response_data(client.post("/companies", json={"ticker": "DASH", "name": "Dashboard Co"}))
    response_data(
        client.post(
            "/alerts",
            json={"company_id": company["id"], "alert_type": "manual", "title": "Owner alert"},
        )
    )
    response_data(
        client.post(
            "/thesis-notes",
            json={"company_id": company["id"], "title": "Owner thesis", "thesis_text": "Evidence-backed thesis."},
        )
    )
    response_data(client.post("/portfolios", json={"name": "Owner portfolio", "base_currency": "USD"}))

    _use_user("other-dashboard-user")
    other_alert = response_data(
        client.post(
            "/alerts",
            json={"company_id": company["id"], "alert_type": "manual", "title": "Other alert"},
        )
    )
    response_data(
        client.post(
            "/thesis-notes",
            json={"company_id": company["id"], "title": "Other thesis", "thesis_text": "Other thesis."},
        )
    )

    statements: list[str] = []

    def record_statement(*args) -> None:
        statements.append(args[2])

    engine = db_session.get_bind()
    sqlalchemy_event.listen(engine, "before_cursor_execute", record_statement)
    try:
        response = client.get("/dashboard/overview")
    finally:
        sqlalchemy_event.remove(engine, "before_cursor_execute", record_statement)
    overview = response_data(response)

    assert [item["id"] for item in overview["alerts"]] == [other_alert["id"]]
    assert [item["title"] for item in overview["thesis_notes"]] == ["Other thesis"]
    assert overview["default_portfolio"] is None
    assert overview["companies"][0]["ticker"] == "DASH"
    assert overview["daily_brief"]["summary"].endswith("1 active thesis notes reviewed.")
    assert len(statements) <= DASHBOARD_QUERY_BUDGET
    assert response.json()["meta"]["processing_time_ms"] <= DASHBOARD_RESPONSE_BUDGET_MS


def test_dashboard_overview_labels_portfolio_analytics_with_missing_prices_as_partial(
    client: TestClient,
) -> None:
    company = response_data(client.post("/companies", json={"ticker": "NOPRICE", "name": "No Price Co"}))
    portfolio = response_data(client.post("/portfolios", json={"name": "Partial portfolio", "base_currency": "USD"}))
    response_data(client.post("/portfolio-holdings", json={
        "portfolio_id": portfolio["id"],
        "company_id": company["id"],
        "ticker": "NOPRICE",
        "quantity": 2,
        "average_cost": 10,
        "currency": "USD",
        "as_of_date": "2026-07-31",
    }))

    response = client.get("/dashboard/overview")
    overview = response_data(response)

    assert overview["portfolio_analytics"]["total_invested_value"] is None
    assert (
        "Default portfolio analytics are partial until every holding has a dated market price."
        in response.json()["meta"]["warnings"]
    )
