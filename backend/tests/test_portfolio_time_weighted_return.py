from datetime import date

import pytest

from app.models import Portfolio, PortfolioSnapshot, PortfolioTransaction
from app.services.portfolio_performance import calculate_time_weighted_return


def _snapshot(portfolio_id: int, day: date, value: float) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        portfolio_id=portfolio_id,
        snapshot_date=day,
        total_portfolio_value=value,
        base_currency="USD",
        calculation_status="complete",
    )


def test_time_weighted_return_compounds_complete_snapshot_subperiods(db):
    portfolio = Portfolio(name="TWR", base_currency="USD")
    db.add(portfolio)
    db.flush()
    db.add_all(
        [
            _snapshot(portfolio.id, date(2026, 8, 1), 100),
            _snapshot(portfolio.id, date(2026, 8, 2), 110),
            _snapshot(portfolio.id, date(2026, 8, 3), 121),
        ]
    )
    db.commit()

    result = calculate_time_weighted_return(db, portfolio.id, date(2026, 8, 1), date(2026, 8, 3))

    assert result.calculation_status == "complete"
    assert result.return_decimal == pytest.approx(0.21)


def test_time_weighted_return_adjusts_external_flow_and_discloses_timing_limit(db):
    portfolio = Portfolio(name="Flow TWR", base_currency="USD")
    db.add(portfolio)
    db.flush()
    flow = PortfolioTransaction(
        portfolio_id=portfolio.id,
        ticker="CASH",
        transaction_type="deposit",
        quantity=20,
        price=0,
        fees=0,
        currency="USD",
        transaction_date=date(2026, 8, 2),
    )
    db.add_all(
        [
            flow,
            _snapshot(portfolio.id, date(2026, 8, 1), 100),
            _snapshot(portfolio.id, date(2026, 8, 2), 132),
        ]
    )
    db.commit()

    result = calculate_time_weighted_return(db, portfolio.id, date(2026, 8, 1), date(2026, 8, 2))

    assert result.calculation_status == "partial"
    assert result.return_decimal == pytest.approx(0.12)
    assert result.source_transaction_ids == [flow.id]
    assert any("end-of-subperiod" in warning for warning in result.warnings)
