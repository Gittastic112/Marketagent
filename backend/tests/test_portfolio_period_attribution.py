from datetime import date

from app.models import Company, ExposureTag, Portfolio, PortfolioSnapshot, PortfolioTransaction
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
    assert "legacy_unverified_replay" in result["blockers"]
    assert result["total_change"] == 20
    assert result["price_movement"] == 20
    assert result["fx_impact"] == 0
    assert result["holdings"][0]["price_movement"] == 20
    assert result["position_change"] == 0
    assert result["cash_change"] == 0
    assert result["unexplained_change"] == 0
    assert result["blockers"] == ["legacy_unverified_replay"]
    assert result["confidence"] == "low"
    assert "Total change" in result["formula"]
    assert result["source_snapshot_ids"] == [start.id, end.id]


def test_period_attribution_requires_complete_boundary_snapshots(db):
    portfolio = Portfolio(name="Incomplete", base_currency="USD")
    db.add(portfolio)
    db.commit()

    result = calculate_period_attribution(db, portfolio.id, date(2026, 8, 1), date(2026, 8, 2))

    assert result["calculation_status"] == "not_available"
    assert result["price_movement"] is None
    assert result["blockers"] == ["missing_complete_boundary_snapshot"]
    assert result["confidence"] == "invalid"


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


def test_period_attribution_reconciles_position_and_internal_cash_changes(db):
    portfolio = Portfolio(name="Position Attribution", base_currency="USD")
    db.add(portfolio)
    db.flush()
    start = _snapshot(portfolio.id, date(2026, 8, 1), 10, 100)
    start.total_cash = 100
    start.total_portfolio_value = 200
    end = _snapshot(portfolio.id, date(2026, 8, 2), 10, 200)
    end.total_cash = 0
    end.total_portfolio_value = 200
    end.payload_json["holdings"][0]["quantity"] = 20
    db.add_all([start, end])
    db.commit()

    result = calculate_period_attribution(db, portfolio.id, start.snapshot_date, end.snapshot_date)

    assert result["position_change"] == 100
    assert result["cash_change"] == -100
    assert result["external_cash_flow"] == 0
    assert result["internal_cash_change"] == -100
    assert result["unexplained_change"] == 0
    assert result["calculation_status"] == "partial"
    assert "legacy_unverified_replay" in result["blockers"]


def test_period_attribution_separates_external_cash_flow(db):
    portfolio = Portfolio(name="External Flow", base_currency="USD")
    db.add(portfolio)
    db.flush()
    start = _snapshot(portfolio.id, date(2026, 8, 1), 10, 100)
    start.payload_json = {"holdings": []}
    start.total_market_value = 0
    start.total_cash = 100
    end = _snapshot(portfolio.id, date(2026, 8, 2), 10, 150)
    end.payload_json = {"holdings": []}
    end.total_market_value = 0
    end.total_cash = 150
    flow = PortfolioTransaction(
        portfolio_id=portfolio.id,
        ticker="CASH",
        transaction_type="deposit",
        quantity=50,
        price=0,
        fees=0,
        currency="USD",
        transaction_date=date(2026, 8, 2),
    )
    db.add_all([start, end, flow])
    db.commit()

    result = calculate_period_attribution(db, portfolio.id, start.snapshot_date, end.snapshot_date)

    assert result["external_cash_flow"] == 50
    assert result["cash_change"] == 50
    assert result["internal_cash_change"] == 0
    assert result["source_transaction_ids"] == [flow.id]
    assert result["unexplained_change"] == 0


def test_period_attribution_rolls_contributions_into_company_dimensions(db):
    tag = ExposureTag(name="Cloud")
    company = Company(
        ticker="TEST",
        name="Dimension Test",
        sector="Technology",
        country="US",
        asset_type="Equity",
        exposure_tags=[tag],
    )
    portfolio = Portfolio(name="Dimensions", base_currency="USD")
    db.add_all([tag, company, portfolio])
    db.flush()
    start = _snapshot(portfolio.id, date(2026, 8, 1), 10, 100)
    end = _snapshot(portfolio.id, date(2026, 8, 2), 12, 120)
    start.payload_json["holdings"][0]["company_id"] = company.id
    end.payload_json["holdings"][0]["company_id"] = company.id
    db.add_all([start, end])
    db.commit()

    result = calculate_period_attribution(db, portfolio.id, start.snapshot_date, end.snapshot_date)

    assert result["attribution_by_sector"] == {"Technology": 20}
    assert result["attribution_by_geography"] == {"US": 20}
    assert result["attribution_by_asset_type"] == {"Equity": 20}
    assert result["attribution_by_tag"] == {"Cloud": 20}
