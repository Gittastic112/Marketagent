from datetime import date

from app.models import Portfolio, PortfolioSnapshot
from app.services.portfolio_period_attribution import calculate_period_attribution


def _snapshot(
    portfolio_id: int,
    day: date,
    price: float,
    value: float,
    *,
    currency: str = "USD",
    fx_rate: float = 1,
) -> PortfolioSnapshot:
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
                    "currency": currency,
                    "market_price": price,
                    "market_value_base": value,
                    "market_fx_rate_to_base": fx_rate,
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
    assert result["fx_impact"] == 0
    assert result["holdings"][0]["price_movement"] == 20
    assert result["source_snapshot_ids"] == [start.id, end.id]


def test_period_attribution_requires_complete_boundary_snapshots(db):
    portfolio = Portfolio(name="Incomplete", base_currency="USD")
    db.add(portfolio)
    db.commit()

    result = calculate_period_attribution(db, portfolio.id, date(2026, 8, 1), date(2026, 8, 2))

    assert result["calculation_status"] == "not_available"
    assert result["price_movement"] is None


def test_period_fx_attribution_separates_security_and_currency_effects(db):
    portfolio = Portfolio(name="FX Attribution", base_currency="USD")
    db.add(portfolio)
    db.flush()
    start = _snapshot(
        portfolio.id,
        date(2026, 8, 1),
        100,
        10,
        currency="INR",
        fx_rate=0.01,
    )
    end = _snapshot(
        portfolio.id,
        date(2026, 8, 2),
        110,
        13.2,
        currency="INR",
        fx_rate=0.012,
    )
    db.add_all([start, end])
    db.commit()

    result = calculate_period_attribution(db, portfolio.id, start.snapshot_date, end.snapshot_date)

    assert result["total_change"] == 3.2
    assert result["price_movement"] == 1
    assert round(result["fx_impact"], 6) == 2.2
    assert round(result["holdings"][0]["fx_impact"], 6) == 2.2
