from datetime import date

import pytest

from app.models import MarketPrice, Portfolio, PortfolioBenchmarkConfig, PortfolioSnapshot, PortfolioTransaction
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

    assert result["calculation_status"] == "partial"
    assert any("Legacy snapshot" in warning for warning in result["warnings"])
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


@pytest.mark.parametrize("flows,ending", [
    ([(2, "deposit", 100)], 229.090909),
    ([(2, "withdrawal", 20)], 98.181818),
    ([(2, "deposit", 100), (3, "withdrawal", 100)], 124.743083),
])
def test_equal_investment_wealth_does_not_claim_a_mismatched_return_spread(db, flows, ending):
    portfolio = Portfolio(name="Mock Data matching benchmark investment", base_currency="USD")
    db.add(portfolio); db.flush()
    start = PortfolioSnapshot(portfolio_id=portfolio.id, snapshot_date=date(2026, 8, 1),
        total_portfolio_value=100, base_currency="USD", calculation_status="complete")
    end = PortfolioSnapshot(portfolio_id=portfolio.id, snapshot_date=date(2026, 8, 4),
        total_portfolio_value=ending, base_currency="USD", calculation_status="complete")
    db.add_all([start, end, PortfolioBenchmarkConfig(portfolio_id=portfolio.id,
        ticker="MOCK", currency="USD", effective_from=date(2026, 1, 1))])
    for day, price in [(1, 100), (2, 110), (3, 115), (4, 120)]:
        db.add(MarketPrice(ticker="MOCK", price=price, currency="USD", as_of_date=date(2026, 8, day)))
    for day, kind, amount in flows:
        db.add(PortfolioTransaction(portfolio_id=portfolio.id, ticker="CASH", transaction_type=kind,
            quantity=amount, currency="USD", price=0, fees=0, transaction_date=date(2026, 8, day)))
    db.commit()

    result = calculate_benchmark_opportunity_cost(db, portfolio.id, start.snapshot_date, end.snapshot_date)

    assert result["benchmark_ending_value"] == pytest.approx(ending, abs=0.00001)
    assert result["opportunity_cost"] == pytest.approx(0, abs=0.00001)
    assert result["benchmark_return"] is None
    assert result["portfolio_return"] is None
    assert result["return_spread"] is None
    assert any("external cash flows" in warning for warning in result["warnings"])
