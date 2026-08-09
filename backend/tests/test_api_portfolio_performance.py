from datetime import date

from app.models import Portfolio, PortfolioSnapshot, PortfolioTransaction


def _snapshot(portfolio_id: int, day: date, value: float) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        portfolio_id=portfolio_id,
        snapshot_date=day,
        total_market_value=0,
        total_cash=value,
        total_portfolio_value=value,
        base_currency="USD",
        calculation_status="complete",
        payload_json={"holdings": []},
    )


def test_owned_performance_and_period_attribution_endpoints(client, db):
    portfolio = Portfolio(name="API Performance", base_currency="USD")
    db.add(portfolio)
    db.flush()
    start = _snapshot(portfolio.id, date(2025, 8, 9), 100)
    end = _snapshot(portfolio.id, date(2026, 8, 9), 110)
    deposit = PortfolioTransaction(
        portfolio_id=portfolio.id,
        ticker="CASH",
        transaction_type="deposit",
        quantity=100,
        price=0,
        fees=0,
        currency="USD",
        transaction_date=start.snapshot_date,
    )
    db.add_all([start, end, deposit])
    db.commit()

    query = "start_date=2025-08-09&end_date=2026-08-09"
    performance = client.get(f"/portfolios/{portfolio.id}/performance?{query}")
    assert performance.status_code == 200, performance.text
    data = performance.json()["data"]
    assert data["time_weighted_return"]["calculation_status"] == "complete"
    assert data["money_weighted_return"]["calculation_status"] == "complete"

    attribution = client.get(f"/portfolios/{portfolio.id}/period-attribution?{query}")
    assert attribution.status_code == 200, attribution.text
    attribution_data = attribution.json()["data"]
    assert attribution_data["calculation_status"] == "complete"
    assert attribution_data["external_cash_flow"] == 0
    assert attribution_data["formula"].startswith("Total change")


def test_performance_endpoint_validates_period(client):
    portfolio = client.post("/portfolios", json={"name": "Dates", "base_currency": "USD"}).json()["data"]
    response = client.get(
        f"/portfolios/{portfolio['id']}/performance?start_date=2026-08-09&end_date=2026-08-09"
    )
    assert response.status_code == 422
