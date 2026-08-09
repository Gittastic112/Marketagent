from datetime import date

from app.models import MarketPrice, Portfolio, PortfolioHolding, PortfolioSnapshot
from app.services.portfolio_analytics import record_daily_snapshot


def test_snapshot_capture_is_idempotent_and_records_completeness(db):
    portfolio = Portfolio(name="Capture", base_currency="USD")
    db.add_all(
        [
            portfolio,
            PortfolioHolding(
                portfolio=portfolio,
                ticker="READY",
                quantity=2,
                average_cost=10,
                currency="USD",
                as_of_date=date(2026, 8, 1),
            ),
            MarketPrice(
                ticker="READY",
                price=12,
                currency="USD",
                as_of_date=date(2026, 8, 9),
            ),
        ]
    )
    db.commit()

    first = record_daily_snapshot(db, portfolio.id, date(2026, 8, 9))
    second = record_daily_snapshot(db, portfolio.id, date(2026, 8, 9))

    assert first.id == second.id
    assert second.calculation_status == "complete"
    assert second.holdings_count == 1
    assert second.priced_holdings_count == 1
    assert second.total_portfolio_value == 24
    holding_payload = second.payload_json["holdings"][0]
    assert holding_payload["ticker"] == "READY"
    assert holding_payload["market_price_id"] is not None
    assert holding_payload["market_price_provider"] == "manual"
    assert holding_payload["market_price_as_of"] == "2026-08-09"
    assert db.query(PortfolioSnapshot).count() == 1


def test_snapshot_capture_records_missing_price_blocker(db):
    portfolio = Portfolio(name="Partial Capture", base_currency="USD")
    db.add(
        PortfolioHolding(
            portfolio=portfolio,
            ticker="MISSING",
            quantity=1,
            average_cost=10,
            currency="USD",
            as_of_date=date(2026, 8, 1),
        )
    )
    db.commit()

    snapshot = record_daily_snapshot(db, portfolio.id, date(2026, 8, 9))

    assert snapshot.calculation_status == "partial"
    assert snapshot.missing_price_tickers_json == ["MISSING"]
    assert snapshot.total_portfolio_value is None
