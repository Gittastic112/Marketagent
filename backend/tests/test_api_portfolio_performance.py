from datetime import date

from app.models import Company, MarketPrice, Portfolio, PortfolioBenchmarkConfig, PortfolioHolding, PortfolioSnapshot, PortfolioTransaction, User


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
    assert data["time_weighted_return"]["calculation_status"] == "partial"
    assert data["money_weighted_return"]["calculation_status"] == "partial"
    assert any("Legacy snapshot" in warning for warning in data["time_weighted_return"]["warnings"])

    attribution = client.get(f"/portfolios/{portfolio.id}/period-attribution?{query}")
    assert attribution.status_code == 200, attribution.text
    attribution_data = attribution.json()["data"]
    assert attribution_data["calculation_status"] == "partial"
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
    assert second.json()["data"]["calculation_status"] == "partial"
    assert second.json()["data"]["payload_json"]["replay_basis"]["status"] == "not_available"
    assert second.json()["meta"]["source"] == "point_in_time_portfolio_capture"


def test_opportunity_cost_endpoint_uses_configured_benchmark(client, db):
    portfolio = Portfolio(name="Benchmark API", base_currency="USD")
    db.add(portfolio)
    db.flush()
    start = _snapshot(portfolio.id, date(2026, 8, 1), 100)
    end = _snapshot(portfolio.id, date(2026, 8, 2), 110)
    db.add_all(
        [
            PortfolioBenchmarkConfig(
                portfolio_id=portfolio.id,
                ticker="SPY",
                currency="USD",
                provider_name="manual",
                effective_from=date(2026, 1, 1),
            ),
            start,
            end,
            MarketPrice(ticker="SPY", price=100, currency="USD", as_of_date=start.snapshot_date),
            MarketPrice(ticker="SPY", price=120, currency="USD", as_of_date=end.snapshot_date),
        ]
    )
    db.commit()

    response = client.get(
        f"/portfolios/{portfolio.id}/opportunity-cost?start_date=2026-08-01&end_date=2026-08-02"
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"]["opportunity_cost"] == 10
    assert response.json()["meta"]["source"] == "configured_portfolio_benchmark"


def test_risk_return_endpoint_is_owner_scoped_and_source_labeled(client, db):
    company = Company(
        ticker="RISK",
        name="Risk Company",
        market="US",
        primary_exchange="NASDAQ",
        local_symbol="RISK",
        currency="USD",
    )
    portfolio = Portfolio(name="Risk API", base_currency="USD")
    other_user = User(id="other_user", email="other@example.com", name="Other")
    other_portfolio = Portfolio(user_id=other_user.id, name="Private", base_currency="USD")
    db.add_all([company, portfolio, other_user, other_portfolio])
    db.flush()
    db.add(PortfolioHolding(
        portfolio_id=portfolio.id,
        company_id=company.id,
        ticker="RISK",
        quantity=1,
        average_cost=100,
        currency="USD",
        as_of_date=date(2026, 8, 9),
    ))
    for offset, price in enumerate([100, 102, 101, 104, 106]):
        db.add(MarketPrice(
            company_id=company.id,
            ticker="RISK",
            price=price,
            currency="USD",
            as_of_date=date(2026, 8, 5 + offset),
            provider_name="test",
        ))
    db.commit()

    response = client.get(
        f"/portfolios/{portfolio.id}/risk-return-comparison?as_of_date=2026-08-09&lookback_days=30&min_observations=3"
    )
    forbidden = client.get(
        f"/portfolios/{other_portfolio.id}/risk-return-comparison?as_of_date=2026-08-09"
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"]["risk_calculation_status"] == "partial"
    assert "NO_RECORDED_ACTIVITY" in response.json()["data"]["blockers"]
    assert response.json()["data"]["contains_mock_data"] is False
    assert response.json()["meta"]["source"] == "historical_market_prices_fx_and_trust_gated_dcf"
    assert response.json()["meta"]["is_mock"] is False
    assert forbidden.status_code == 404
