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


def create_portfolio(client: TestClient) -> dict:
    response = client.post(
        "/portfolios",
        json={"name": "Core Portfolio", "base_currency": "USD", "description": "Long-term holdings"},
    )
    assert response.status_code == 201
    return response.json()


def create_company(client: TestClient) -> dict:
    response = client.post("/companies", json={"ticker": "AAPL", "name": "Apple Inc.", "cik": "0000320193"})
    assert response.status_code == 201
    return response.json()


def test_create_list_get_update_and_delete_portfolio(client: TestClient) -> None:
    created = create_portfolio(client)

    assert created["name"] == "Core Portfolio"
    assert created["base_currency"] == "USD"
    assert created["description"] == "Long-term holdings"

    list_response = client.get("/portfolios")
    get_response = client.get(f"/portfolios/{created['id']}")
    update_response = client.patch(f"/portfolios/{created['id']}", json={"description": "Updated notes"})
    delete_response = client.delete(f"/portfolios/{created['id']}")
    missing_response = client.get(f"/portfolios/{created['id']}")

    assert list_response.status_code == 200
    assert list_response.json()[0]["name"] == "Core Portfolio"
    assert get_response.status_code == 200
    assert get_response.json()["base_currency"] == "USD"
    assert update_response.status_code == 200
    assert update_response.json()["description"] == "Updated notes"
    assert delete_response.status_code == 204
    assert missing_response.status_code == 404


def test_create_list_update_and_delete_holding(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    company = create_company(client)

    response = client.post(
        "/portfolio-holdings",
        json={
            "portfolio_id": portfolio["id"],
            "company_id": company["id"],
            "ticker": "AAPL",
            "quantity": 12.5,
            "average_cost": 145.25,
            "currency": "USD",
            "as_of_date": "2026-05-26",
        },
    )
    assert response.status_code == 201
    created = response.json()

    list_response = client.get("/portfolio-holdings")
    update_response = client.patch(f"/portfolio-holdings/{created['id']}", json={"quantity": 15})
    delete_response = client.delete(f"/portfolio-holdings/{created['id']}")

    assert created["ticker"] == "AAPL"
    assert created["company_id"] == company["id"]
    assert list_response.status_code == 200
    assert list_response.json()[0]["portfolio_id"] == portfolio["id"]
    assert update_response.status_code == 200
    assert update_response.json()["quantity"] == 15
    assert delete_response.status_code == 204


def test_create_list_update_and_delete_transaction(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    company = create_company(client)

    response = client.post(
        "/portfolio-transactions",
        json={
            "portfolio_id": portfolio["id"],
            "company_id": company["id"],
            "ticker": "AAPL",
            "transaction_type": "buy",
            "quantity": 10,
            "price": 180.5,
            "fees": 1.25,
            "currency": "USD",
            "transaction_date": "2026-05-26",
            "notes": "Initial entry",
        },
    )
    assert response.status_code == 201
    created = response.json()

    list_response = client.get("/portfolio-transactions")
    update_response = client.patch(f"/portfolio-transactions/{created['id']}", json={"notes": "Updated entry"})
    delete_response = client.delete(f"/portfolio-transactions/{created['id']}")

    assert created["transaction_type"] == "buy"
    assert created["price"] == 180.5
    assert list_response.status_code == 200
    assert list_response.json()[0]["ticker"] == "AAPL"
    assert update_response.status_code == 200
    assert update_response.json()["notes"] == "Updated entry"
    assert delete_response.status_code == 204


def test_buy_transaction_creates_and_updates_matching_holding(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    company = create_company(client)

    first_buy = client.post(
        "/portfolio-transactions",
        json={
            "portfolio_id": portfolio["id"],
            "company_id": company["id"],
            "ticker": "AAPL",
            "transaction_type": "buy",
            "quantity": 10,
            "price": 100,
            "fees": 0,
            "currency": "USD",
            "transaction_date": "2026-05-26",
        },
    )
    second_buy = client.post(
        "/portfolio-transactions",
        json={
            "portfolio_id": portfolio["id"],
            "company_id": company["id"],
            "ticker": "AAPL",
            "transaction_type": "buy",
            "quantity": 5,
            "price": 160,
            "fees": 0,
            "currency": "USD",
            "transaction_date": "2026-05-27",
        },
    )
    holdings = client.get("/portfolio-holdings").json()

    assert first_buy.status_code == 201
    assert second_buy.status_code == 201
    assert len(holdings) == 1
    assert holdings[0]["quantity"] == 15
    assert holdings[0]["average_cost"] == 120
    assert holdings[0]["as_of_date"] == "2026-05-27"


def test_sell_transaction_reduces_holding_and_rejects_oversell(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    company = create_company(client)
    client.post(
        "/portfolio-transactions",
        json={
            "portfolio_id": portfolio["id"],
            "company_id": company["id"],
            "ticker": "AAPL",
            "transaction_type": "buy",
            "quantity": 10,
            "price": 100,
            "fees": 0,
            "currency": "USD",
            "transaction_date": "2026-05-26",
        },
    )

    sell = client.post(
        "/portfolio-transactions",
        json={
            "portfolio_id": portfolio["id"],
            "company_id": company["id"],
            "ticker": "AAPL",
            "transaction_type": "sell",
            "quantity": 4,
            "price": 125,
            "fees": 0,
            "currency": "USD",
            "transaction_date": "2026-05-27",
        },
    )
    oversell = client.post(
        "/portfolio-transactions",
        json={
            "portfolio_id": portfolio["id"],
            "company_id": company["id"],
            "ticker": "AAPL",
            "transaction_type": "sell",
            "quantity": 7,
            "price": 125,
            "fees": 0,
            "currency": "USD",
            "transaction_date": "2026-05-28",
        },
    )
    holdings = client.get("/portfolio-holdings").json()

    assert sell.status_code == 201
    assert oversell.status_code == 409
    assert holdings[0]["quantity"] == 6


def test_transaction_update_and_delete_resync_holding(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    company = create_company(client)
    created = client.post(
        "/portfolio-transactions",
        json={
            "portfolio_id": portfolio["id"],
            "company_id": company["id"],
            "ticker": "AAPL",
            "transaction_type": "buy",
            "quantity": 10,
            "price": 100,
            "fees": 0,
            "currency": "USD",
            "transaction_date": "2026-05-26",
        },
    ).json()

    update_response = client.patch(f"/portfolio-transactions/{created['id']}", json={"quantity": 12})
    updated_holding = client.get("/portfolio-holdings").json()[0]
    delete_response = client.delete(f"/portfolio-transactions/{created['id']}")
    deleted_holding = client.get("/portfolio-holdings").json()[0]

    assert update_response.status_code == 200
    assert updated_holding["quantity"] == 12
    assert delete_response.status_code == 204
    assert deleted_holding["quantity"] == 0


def test_deleting_later_buy_restores_weighted_average_cost(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    company = create_company(client)
    client.post(
        "/portfolio-transactions",
        json={
            "portfolio_id": portfolio["id"],
            "company_id": company["id"],
            "ticker": "AAPL",
            "transaction_type": "buy",
            "quantity": 10,
            "price": 100,
            "fees": 0,
            "currency": "USD",
            "transaction_date": "2026-05-26",
        },
    )
    second_buy = client.post(
        "/portfolio-transactions",
        json={
            "portfolio_id": portfolio["id"],
            "company_id": company["id"],
            "ticker": "AAPL",
            "transaction_type": "buy",
            "quantity": 10,
            "price": 200,
            "fees": 0,
            "currency": "USD",
            "transaction_date": "2026-05-27",
        },
    ).json()

    weighted_holding = client.get("/portfolio-holdings").json()[0]
    delete_response = client.delete(f"/portfolio-transactions/{second_buy['id']}")
    restored_holding = client.get("/portfolio-holdings").json()[0]

    assert weighted_holding["quantity"] == 20
    assert weighted_holding["average_cost"] == 150
    assert delete_response.status_code == 204
    assert restored_holding["quantity"] == 10
    assert restored_holding["average_cost"] == 100


def test_create_list_update_and_delete_cash_balance(client: TestClient) -> None:
    portfolio = create_portfolio(client)

    response = client.post(
        "/portfolio-cash-balances",
        json={"portfolio_id": portfolio["id"], "currency": "USD", "amount": 2500, "as_of_date": "2026-05-26"},
    )
    assert response.status_code == 201
    created = response.json()

    list_response = client.get("/portfolio-cash-balances")
    update_response = client.patch(f"/portfolio-cash-balances/{created['id']}", json={"amount": 3000})
    delete_response = client.delete(f"/portfolio-cash-balances/{created['id']}")

    assert created["amount"] == 2500
    assert list_response.status_code == 200
    assert list_response.json()[0]["portfolio_id"] == portfolio["id"]
    assert update_response.status_code == 200
    assert update_response.json()["amount"] == 3000
    assert delete_response.status_code == 204


def test_create_list_update_and_delete_snapshot(client: TestClient) -> None:
    portfolio = create_portfolio(client)

    response = client.post(
        "/portfolio-snapshots",
        json={
            "portfolio_id": portfolio["id"],
            "snapshot_date": "2026-05-26",
            "total_market_value": 10000,
            "total_cost_basis": 8500,
            "total_cash": 1500,
            "payload_json": {"source": "manual"},
        },
    )
    assert response.status_code == 201
    created = response.json()

    list_response = client.get("/portfolio-snapshots")
    update_response = client.patch(f"/portfolio-snapshots/{created['id']}", json={"total_cash": 2000})
    delete_response = client.delete(f"/portfolio-snapshots/{created['id']}")

    assert created["payload_json"] == {"source": "manual"}
    assert list_response.status_code == 200
    assert list_response.json()[0]["portfolio_id"] == portfolio["id"]
    assert update_response.status_code == 200
    assert update_response.json()["total_cash"] == 2000
    assert delete_response.status_code == 204


def test_portfolio_delete_is_blocked_when_linked_records_exist(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    company = create_company(client)
    holding = client.post(
        "/portfolio-holdings",
        json={
            "portfolio_id": portfolio["id"],
            "company_id": company["id"],
            "ticker": "AAPL",
            "quantity": 1,
            "average_cost": 100,
            "currency": "USD",
            "as_of_date": "2026-05-26",
        },
    )
    assert holding.status_code == 201

    response = client.delete(f"/portfolios/{portfolio['id']}")

    assert response.status_code == 409
    assert "linked records" in response.json()["detail"]


def test_holding_rejects_missing_references(client: TestClient) -> None:
    response = client.post(
        "/portfolio-holdings",
        json={
            "portfolio_id": 999,
            "company_id": 888,
            "ticker": "AAPL",
            "quantity": 1,
            "average_cost": 100,
            "currency": "USD",
            "as_of_date": "2026-05-26",
        },
    )

    assert response.status_code == 404


def test_transaction_rejects_invalid_type_and_negative_values(client: TestClient) -> None:
    portfolio = create_portfolio(client)

    invalid_type = client.post(
        "/portfolio-transactions",
        json={
            "portfolio_id": portfolio["id"],
            "ticker": "AAPL",
            "transaction_type": "invalid",
            "quantity": 10,
            "price": 180.5,
            "fees": 0,
            "currency": "USD",
            "transaction_date": "2026-05-26",
        },
    )
    negative_value = client.post(
        "/portfolio-transactions",
        json={
            "portfolio_id": portfolio["id"],
            "ticker": "AAPL",
            "transaction_type": "buy",
            "quantity": -10,
            "price": 180.5,
            "fees": 0,
            "currency": "USD",
            "transaction_date": "2026-05-26",
        },
    )

    assert invalid_type.status_code == 422
    assert negative_value.status_code == 422
