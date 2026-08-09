from datetime import date
from decimal import Decimal

from app.models import FxRateObservation, Portfolio, PortfolioTransaction
from app.services.portfolio_cash_flows import normalize_external_cash_flows


def test_external_cash_flows_are_signed_and_converted_at_transaction_date(db):
    portfolio = Portfolio(name="Flows", base_currency="USD")
    db.add(portfolio)
    db.flush()
    db.add_all(
        [
            PortfolioTransaction(
                portfolio_id=portfolio.id,
                ticker="CASH",
                transaction_type="deposit",
                quantity=1000,
                price=0,
                fees=0,
                currency="INR",
                transaction_date=date(2026, 8, 1),
            ),
            PortfolioTransaction(
                portfolio_id=portfolio.id,
                ticker="CASH",
                transaction_type="withdrawal",
                quantity=5,
                price=0,
                fees=0,
                currency="USD",
                transaction_date=date(2026, 8, 2),
            ),
            FxRateObservation(
                base_currency="INR",
                quote_currency="USD",
                rate=Decimal("0.012"),
                as_of_date=date(2026, 8, 1),
                provider_name="manual",
            ),
        ]
    )
    db.commit()

    report = normalize_external_cash_flows(db, portfolio.id, end_date=date(2026, 8, 3))

    assert report.complete is True
    assert [flow.amount_base for flow in report.flows] == [Decimal("12.0000000000"), Decimal("-5")]
    assert report.net_external_cash_flow == Decimal("7.0000000000")
    assert report.flows[0].fx_observation_id is not None


def test_external_cash_flow_report_blocks_when_fx_is_missing(db):
    portfolio = Portfolio(name="Missing Flow FX", base_currency="USD")
    transaction = PortfolioTransaction(
        portfolio=portfolio,
        ticker="CASH",
        transaction_type="deposit",
        quantity=100,
        price=0,
        fees=0,
        currency="EUR",
        transaction_date=date(2026, 8, 1),
    )
    db.add_all([portfolio, transaction])
    db.commit()

    report = normalize_external_cash_flows(db, portfolio.id)

    assert report.complete is False
    assert report.net_external_cash_flow is None
    assert report.missing_fx_pairs == ["EUR/USD"]
    assert report.missing_transaction_ids == [transaction.id]
