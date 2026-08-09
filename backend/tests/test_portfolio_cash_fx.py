from datetime import date
from decimal import Decimal

from app.models import FxRateObservation, Portfolio, PortfolioCashBalance
from app.services.portfolio_analytics import calculate_portfolio_analytics
from app.services.portfolio_valuation import calculate_portfolio_valuation


def test_latest_cash_balance_per_currency_is_converted_to_base(db):
    portfolio = Portfolio(name="Cash FX", base_currency="USD")
    db.add_all(
        [
            portfolio,
            PortfolioCashBalance(
                portfolio=portfolio,
                currency="USD",
                amount=50,
                as_of_date=date(2026, 8, 1),
            ),
            PortfolioCashBalance(
                portfolio=portfolio,
                currency="INR",
                amount=1000,
                as_of_date=date(2026, 8, 1),
            ),
            PortfolioCashBalance(
                portfolio=portfolio,
                currency="INR",
                amount=1200,
                as_of_date=date(2026, 8, 5),
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

    valuation = calculate_portfolio_valuation(db, portfolio.id, date(2026, 8, 8))

    assert valuation["total_cash_value"] == 64.4
    assert valuation["total_portfolio_value"] == 64.4
    assert {row["currency"] for row in valuation["cash_balances"]} == {"INR", "USD"}
    assert next(row for row in valuation["cash_balances"] if row["currency"] == "INR")["amount"] == 1200
    assert calculate_portfolio_analytics(db, portfolio.id, date(2026, 8, 8))["total_cash_value"] == 64.4


def test_missing_cash_fx_blocks_total_portfolio_value(db):
    portfolio = Portfolio(name="Missing Cash FX", base_currency="USD")
    db.add_all(
        [
            portfolio,
            PortfolioCashBalance(
                portfolio=portfolio,
                currency="EUR",
                amount=100,
                as_of_date=date(2026, 8, 1),
            ),
        ]
    )
    db.commit()

    result = calculate_portfolio_valuation(db, portfolio.id, date(2026, 8, 8))

    assert result["total_cash_value"] is None
    assert result["total_portfolio_value"] is None
    assert result["missing_fx_pairs"] == ["EUR/USD"]
