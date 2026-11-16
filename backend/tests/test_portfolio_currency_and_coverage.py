"""Mock Data historical denomination, freshness and missing-weight regressions."""
from datetime import date
from decimal import Decimal
import pytest
from app.models import Portfolio, PortfolioSnapshot, PortfolioTransaction, PortfolioBenchmarkConfig, MarketPrice, FxRateObservation
from app.services.portfolio_performance import calculate_time_weighted_return, calculate_money_weighted_return
from app.services.portfolio_benchmark import calculate_benchmark_opportunity_cost
from app.services.portfolio_analytics import calculate_portfolio_analytics


def history(db):
    portfolio = Portfolio(name="Mock Data historical currency", base_currency="USD")
    db.add(portfolio); db.flush()
    start = PortfolioSnapshot(portfolio_id=portfolio.id, snapshot_date=date(2026, 1, 1),
        total_portfolio_value=100, base_currency="USD", calculation_status="complete")
    end = PortfolioSnapshot(portfolio_id=portfolio.id, snapshot_date=date(2026, 1, 11),
        total_portfolio_value=220, base_currency="USD", calculation_status="complete")
    db.add_all([start, end,
        PortfolioTransaction(portfolio_id=portfolio.id, ticker="CASH", transaction_type="deposit", quantity=100,
            currency="USD", price=0, fees=0, transaction_date=date(2025, 12, 31)),
        PortfolioTransaction(portfolio_id=portfolio.id, ticker="CASH", transaction_type="deposit", quantity=100,
            currency="USD", price=0, fees=0, transaction_date=date(2026, 1, 6)),
        PortfolioBenchmarkConfig(portfolio_id=portfolio.id, ticker="MOCKBENCH", currency="USD", effective_from=date(2025, 1, 1)),
    ])
    for day, price in [(1, 100), (6, 105), (11, 110)]:
        db.add(MarketPrice(ticker="MOCKBENCH", price=price, currency="USD", as_of_date=date(2026, 1, day)))
    db.commit()
    return portfolio, start, end


def test_preference_change_does_not_redenominate_historical_returns(db):
    portfolio, start, end = history(db)
    def results():
        return (calculate_time_weighted_return(db, portfolio.id, start.snapshot_date, end.snapshot_date),
            calculate_money_weighted_return(db, portfolio.id, end.snapshot_date),
            calculate_benchmark_opportunity_cost(db, portfolio.id, start.snapshot_date, end.snapshot_date))
    original = results()
    portfolio.base_currency = "EUR"; db.commit()
    changed = results()
    assert changed[0].return_decimal == original[0].return_decimal == pytest.approx(.2)
    assert changed[1].return_decimal == original[1].return_decimal
    assert changed[2]["opportunity_cost"] == original[2]["opportunity_cost"]
    assert changed[0].base_currency == changed[1].base_currency == "USD"


def test_mixed_snapshot_currencies_withhold_time_weighted_return(db):
    portfolio, start, end = history(db)
    end.base_currency = "EUR"; db.commit()
    result = calculate_time_weighted_return(db, portfolio.id, start.snapshot_date, end.snapshot_date)
    assert result.return_decimal is None and result.calculation_status == "not_available"
    assert any("currenc" in warning.lower() for warning in result.warnings)


@pytest.mark.parametrize("source", ["quote", "fx", "flow_fx"])
def test_benchmark_withholds_comparison_when_any_required_observation_is_old(db, source):
    portfolio, start, end = history(db)
    if source == "quote":
        db.query(MarketPrice).filter(MarketPrice.as_of_date > start.snapshot_date).delete()
    else:
        if source == "fx":
            for price in db.query(MarketPrice):
                price.currency = "EUR"
        else:
            db.query(PortfolioTransaction).filter(PortfolioTransaction.transaction_date == date(2026, 1, 6)).one().currency = "EUR"
        db.add(FxRateObservation(base_currency="EUR", quote_currency="USD", rate=Decimal("1.2"),
            as_of_date=date(2025, 12, 30), provider_name="Mock Data"))
    db.commit()
    result = calculate_benchmark_opportunity_cost(db, portfolio.id, start.snapshot_date, end.snapshot_date)
    assert result["calculation_status"] == "not_available"
    assert result["opportunity_cost"] is None and result["return_spread"] is None
    assert any("five calendar days" in warning for warning in result["warnings"])


def test_unknown_holding_weight_is_not_zero_concentration(db, monkeypatch):
    from app.services import portfolio_analytics
    monkeypatch.setattr(portfolio_analytics, "calculate_portfolio_valuation", lambda *args, **kwargs: {
        "portfolio_id": 1, "as_of_date": date(2026, 1, 1), "base_currency": "USD",
        "total_cash_value": 0, "total_market_value": None, "total_unrealized_pnl": None,
        "total_unrealized_pnl_percent": None, "missing_fx_pairs": [],
        "holdings": [{"company_id": None, "ticker": "MISSING", "currency": "USD", "weight_percent": None, "unrealized_pnl": None}]})
    result = calculate_portfolio_analytics(db, 1)
    assert result["concentration_score"] is None
    assert result["sector_exposure"] == {} and result["currency_exposure"] == {}
    assert result["top_positions"] == []
    assert result["missing_weight_tickers"] == ["MISSING"]
    assert result["exposure_status"] == "not_available"


@pytest.mark.parametrize("age,available", [(5, True), (6, False)])
def test_benchmark_flow_price_freshness_boundary_and_evidence(db, age, available):
    portfolio, start, end = history(db)
    db.query(MarketPrice).filter(MarketPrice.as_of_date == date(2026, 1, 6)).delete()
    flow = db.query(PortfolioTransaction).filter(PortfolioTransaction.transaction_date == date(2026, 1, 6)).one()
    flow.transaction_date = date(2026, 1, 1 + age)
    db.commit()
    result = calculate_benchmark_opportunity_cost(db, portfolio.id, start.snapshot_date, end.snapshot_date)
    assert (result["opportunity_cost"] is not None) == available
    observation = result["price_evidence"][-1]
    assert observation["price_age_days"] == age
    assert observation["is_stale"] != available
