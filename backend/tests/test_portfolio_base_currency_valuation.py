from datetime import date
from decimal import Decimal

from app.models import FxRateObservation, MarketPrice, Portfolio, PortfolioHolding
from app.services.portfolio_valuation import calculate_portfolio_valuation


def test_portfolio_uses_historical_and_current_fx_for_base_currency_totals(db):
    portfolio = Portfolio(name="Cross Currency", base_currency="USD")
    holding = PortfolioHolding(
        portfolio=portfolio,
        ticker="INRCO",
        quantity=10,
        average_cost=100,
        currency="INR",
        as_of_date=date(2026, 8, 1),
    )
    db.add_all(
        [
            portfolio,
            holding,
            MarketPrice(
                ticker="INRCO",
                price=120,
                currency="INR",
                as_of_date=date(2026, 8, 8),
            ),
            FxRateObservation(
                base_currency="INR",
                quote_currency="USD",
                rate=Decimal("0.011"),
                as_of_date=date(2026, 8, 1),
                provider_name="manual",
            ),
            FxRateObservation(
                base_currency="INR",
                quote_currency="USD",
                rate=Decimal("0.012"),
                as_of_date=date(2026, 8, 8),
                provider_name="manual",
            ),
        ]
    )
    db.commit()

    result = calculate_portfolio_valuation(db, portfolio.id, date(2026, 8, 8))
    valued = result["holdings"][0]

    assert valued["market_value"] == 1200
    assert valued["total_cost"] == 1000
    assert valued["market_value_base"] == 14.4
    assert valued["total_cost_base"] == 11
    assert round(valued["unrealized_pnl_base"], 6) == 3.4
    assert result["total_market_value"] == 14.4
    assert result["total_cost_basis"] == 11
    assert result["missing_fx_pairs"] == []


def test_missing_fx_blocks_cross_currency_portfolio_total(db):
    portfolio = Portfolio(name="Missing FX", base_currency="USD")
    db.add_all(
        [
            portfolio,
            PortfolioHolding(
                portfolio=portfolio,
                ticker="INRCO",
                quantity=1,
                average_cost=100,
                currency="INR",
                as_of_date=date(2026, 8, 1),
            ),
            MarketPrice(
                ticker="INRCO",
                price=120,
                currency="INR",
                as_of_date=date(2026, 8, 8),
            ),
        ]
    )
    db.commit()

    result = calculate_portfolio_valuation(db, portfolio.id, date(2026, 8, 8))

    assert result["total_market_value"] is None
    assert result["total_unrealized_pnl"] is None
    assert result["missing_fx_pairs"] == ["INR/USD"]
