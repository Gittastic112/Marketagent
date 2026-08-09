from datetime import date

from app.models import Portfolio, PortfolioSnapshot
from app.services.portfolio_period_attribution import calculate_period_attribution


def _snapshot(portfolio_id: int, day: date, price: float, value: float) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        portfolio_id=portfolio_id,
        snapshot_date=day,
        total_portfolio_value=value,
        total_market_value=value,
        total_cash=0,
        base_currency="USD",
        calculation_status="complete",
        payload_json={
            "holdings": [
                {
                    "holding_id": 1,
                    "company_id": 1,
                    "ticker": "TEST",
                    "quantity": 10,
                    "currency": "USD",
                    "market_price": price,
                    "market_value_base": value,
                    "market_fx_rate_to_base": 1,
                }
            ]
        },
    )


def test_period_price_attribution_uses_beginning_quantity_and_fx(db):
    portfolio = Portfolio(name="Attribution", base_currency="USD")
    db.add(portfolio)
    db.flush()
    start = _snapshot(portfolio.id, date(2026, 8, 1), 10, 100)
    end = _snapshot(portfolio.id, date(2026, 8, 2), 12, 120)
    db.add_all([start, end])
    db.commit()

    result = calculate_period_attribution(db, portfolio.id, start.snapshot_date, end.snapshot_date)

    assert result["calculation_status"] == "partial"
    assert result["total_change"] == 20
    assert result["price_movement"] == 20
    assert result["holdings"][0]["price_movement"] == 20
    assert result["source_snapshot_ids"] == [start.id, end.id]


def test_period_attribution_requires_complete_boundary_snapshots(db):
    portfolio = Portfolio(name="Incomplete", base_currency="USD")
    db.add(portfolio)
    db.commit()

    result = calculate_period_attribution(db, portfolio.id, date(2026, 8, 1), date(2026, 8, 2))

    assert result["calculation_status"] == "not_available"
    assert result["price_movement"] is None
