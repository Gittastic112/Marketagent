from datetime import date

import pytest

from app.models import MarketPrice, Portfolio, PortfolioBenchmarkConfig, PortfolioSnapshot
from app.services.portfolio_benchmark import calculate_benchmark_opportunity_cost


def test_benchmark_opportunity_cost_uses_dated_prices_and_snapshots(db):
    portfolio = Portfolio(name="Opportunity", base_currency="USD")
    db.add(portfolio)
    db.flush()
    config = PortfolioBenchmarkConfig(
        portfolio_id=portfolio.id,
        ticker="SPY",
        currency="USD",
        provider_name="manual",
        effective_from=date(2026, 1, 1),
    )
    start = PortfolioSnapshot(
        portfolio_id=portfolio.id,
        snapshot_date=date(2026, 8, 1),
        total_portfolio_value=100,
        base_currency="USD",
        calculation_status="complete",
    )
    end = PortfolioSnapshot(
        portfolio_id=portfolio.id,
        snapshot_date=date(2026, 8, 2),
        total_portfolio_value=110,
        base_currency="USD",
        calculation_status="complete",
    )
    db.add_all(
        [
            config,
            start,
            end,
            MarketPrice(ticker="SPY", price=100, currency="USD", as_of_date=start.snapshot_date),
            MarketPrice(ticker="SPY", price=120, currency="USD", as_of_date=end.snapshot_date),
        ]
    )
    db.commit()

    result = calculate_benchmark_opportunity_cost(db, portfolio.id, start.snapshot_date, end.snapshot_date)

    assert result["calculation_status"] == "complete"
    assert result["benchmark_return"] == pytest.approx(0.2)
    assert result["portfolio_return"] == pytest.approx(0.1)
    assert result["return_spread"] == pytest.approx(-0.1)
    assert result["benchmark_ending_value"] == pytest.approx(120)
    assert result["opportunity_cost"] == pytest.approx(10)


def test_benchmark_opportunity_cost_requires_configuration(db):
    portfolio = Portfolio(name="No Benchmark", base_currency="USD")
    db.add(portfolio)
    db.commit()

    result = calculate_benchmark_opportunity_cost(db, portfolio.id, date(2026, 8, 1), date(2026, 8, 2))

    assert result["calculation_status"] == "not_configured"
    assert result["opportunity_cost"] is None
