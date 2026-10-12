from datetime import date

import pytest

from app.models import Portfolio, PortfolioSnapshot, PortfolioTransaction
from app.services.portfolio_performance import calculate_money_weighted_return


def test_money_weighted_return_uses_external_flows_and_complete_snapshot(db):
    portfolio = Portfolio(name="MWR", base_currency="USD")
    db.add(portfolio)
    db.flush()
    deposit = PortfolioTransaction(
        portfolio_id=portfolio.id,
        ticker="CASH",
        transaction_type="deposit",
        quantity=100,
        price=0,
        fees=0,
        currency="USD",
        transaction_date=date(2025, 8, 9),
    )
    snapshot = PortfolioSnapshot(
        portfolio_id=portfolio.id,
        snapshot_date=date(2026, 8, 9),
        total_portfolio_value=110,
        base_currency="USD",
        calculation_status="complete",
    )
    db.add_all([deposit, snapshot])
    db.commit()

    result = calculate_money_weighted_return(db, portfolio.id, date(2026, 8, 9))

    assert result.calculation_status == "partial"
    assert any("Legacy snapshot" in warning for warning in result.warnings)
    assert result.return_decimal is not None
    assert result.return_decimal == pytest.approx(0.1, abs=0.001)
    assert result.source_snapshot_ids == [snapshot.id]
    assert result.source_transaction_ids == [deposit.id]


def test_money_weighted_return_requires_complete_end_snapshot(db):
    portfolio = Portfolio(name="No Snapshot", base_currency="USD")
    db.add(portfolio)
    db.commit()

    result = calculate_money_weighted_return(db, portfolio.id, date(2026, 8, 9))

    assert result.calculation_status == "not_available"
    assert result.return_decimal is None
    assert "complete point-in-time snapshot" in result.warnings[0]
