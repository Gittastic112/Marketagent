from datetime import date

from app.models import MarketPrice, Portfolio, PortfolioHolding, PortfolioSnapshot, PortfolioTransaction


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


def test_snapshot_capture_endpoint_is_idempotent_and_source_labeled(client, db):
    portfolio = Portfolio(name="Capture API", base_currency="USD")
    holding = PortfolioHolding(
        portfolio=portfolio,
        ticker="CAP",
        quantity=2,
        average_cost=10,
        currency="USD",
        as_of_date=date(2026, 8, 1),
    )
    db.add_all(
        [
            portfolio,
            holding,
            MarketPrice(ticker="CAP", price=12, currency="USD", as_of_date=date(2026, 8, 9)),
        ]
    )
    db.commit()

    url = f"/portfolios/{portfolio.id}/snapshots/capture?as_of_date=2026-08-09"
    first = client.post(url)
    second = client.post(url)

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["data"]["id"] == second.json()["data"]["id"]
    assert second.json()["data"]["calculation_status"] == "complete"
    assert second.json()["meta"]["source"] == "point_in_time_portfolio_capture"
