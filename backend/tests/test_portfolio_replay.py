"""Mock Data: independently reconciled dated activity, never normal records."""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.models import Company, MarketPrice, Portfolio, PortfolioCashBalance, PortfolioHolding, PortfolioTransaction
from app.services.portfolio_valuation import calculate_portfolio_valuation
from app.services.portfolio_analytics import record_daily_snapshot
from app.services.portfolio_holdings import apply_transaction_to_cash, apply_transaction_to_holding
from app.services.portfolio_risk_return import calculate_portfolio_risk_return
from app.services.portfolio_replay import _book


@pytest.mark.parametrize("deposit, expected_cash, negative", [
    ("1", "0.999997", False),
    ("0", "-0.000006", True),
])
def test_fractional_trades_match_postgres_numeric_tie_rounding(deposit, expected_cash, negative):
    # PostgreSQL NUMERIC rounds ties away from zero at each persisted cash update.
    # Three $0.0000015 debits must not accumulate a false reconciliation gap.
    rows = [SimpleNamespace(id=1, company_id=None, ticker="CASH", currency="USD",
        transaction_type="deposit", quantity=Decimal(deposit), price=Decimal(0),
        fees=Decimal(0), transaction_date=date(2026, 1, 1))]
    rows.extend(SimpleNamespace(id=index, company_id=1, ticker="MOCK", currency="USD",
        transaction_type="buy", quantity=Decimal("0.000001"), price=Decimal("1.5"),
        fees=Decimal(0), transaction_date=date(2026, 1, 1)) for index in range(2, 5))
    _, cash, blockers, _ = _book(rows)
    assert cash["USD"] == Decimal(expected_cash)
    assert ("NEGATIVE_CASH_OR_MISSING_OPENING_FUNDING" in blockers) is negative


def test_fractional_split_matches_persisted_numeric_precision():
    rows = [SimpleNamespace(id=1, company_id=None, ticker="CASH", currency="USD",
        transaction_type="deposit", quantity=Decimal(1), price=Decimal(0),
        fees=Decimal(0), transaction_date=date(2026, 1, 1)),
        SimpleNamespace(id=2, company_id=1, ticker="MOCK", currency="USD",
        transaction_type="buy", quantity=Decimal("0.000001"), price=Decimal(1),
        fees=Decimal(0), transaction_date=date(2026, 1, 1)),
        SimpleNamespace(id=3, company_id=1, ticker="MOCK", currency="USD",
        transaction_type="split", quantity=Decimal("2.5"), price=Decimal(0),
        fees=Decimal(0), transaction_date=date(2026, 1, 2))]
    positions, _, blockers, _ = _book(rows)
    assert positions[(1, "MOCK", "USD")].quantity == Decimal("0.000003")
    assert not blockers


def record_activity(db, portfolio, company, day, kind, qty, price=0, fees=0):
    record = PortfolioTransaction(portfolio_id=portfolio.id, company_id=company.id if company else None,
        ticker=company.ticker if company else "CASH", transaction_type=kind, quantity=qty,
        price=price, fees=fees, currency=company.currency if company else portfolio.base_currency, transaction_date=day)
    db.add(record)
    db.flush()
    apply_transaction_to_holding(db, record)
    apply_transaction_to_cash(db, record)
    db.flush()
    return record


def seed_book(db):
    company = Company(ticker="REPLAY", name="Mock Data replay company", currency="USD")
    portfolio = Portfolio(user_id="local-user", name="Mock Data replay", base_currency="USD")
    db.add_all([company, portfolio])
    db.flush()
    records = []
    for day, kind, qty, price, fees in [(1, "deposit", 200, 0, 0), (2, "buy", 10, 10, 2),
        (5, "sell", 10, 12, 1), (10, "deposit", 80, 0, 0), (10, "buy", 4, 20, 2)]:
        record = PortfolioTransaction(portfolio_id=portfolio.id, company_id=company.id if kind in {"buy", "sell"} else None,
            ticker="REPLAY" if kind in {"buy", "sell"} else "CASH", transaction_type=kind,
            quantity=qty, price=price, fees=fees, currency="USD", transaction_date=date(2026, 1, day))
        db.add(record)
        records.append(record)
    db.add_all([
        PortfolioHolding(portfolio_id=portfolio.id, company_id=company.id, ticker="REPLAY", quantity=4,
            average_cost=Decimal("20.5"), currency="USD", as_of_date=date(2026, 1, 10)),
        PortfolioCashBalance(portfolio_id=portfolio.id, currency="USD", amount=215, as_of_date=date(2026, 1, 10)),
        MarketPrice(company_id=company.id, ticker="REPLAY", currency="USD", price=11, as_of_date=date(2026, 1, 3)),
        MarketPrice(company_id=company.id, ticker="REPLAY", currency="USD", price=999, as_of_date=date(2026, 1, 15)),
    ])
    db.commit()
    return portfolio, company, records


def test_historical_positions_and_cash_exclude_future_sales_buys_and_prices(db):
    portfolio, _, records = seed_book(db)
    result = calculate_portfolio_valuation(db, portfolio.id, date(2026, 1, 3), user_id="local-user")
    assert result["holdings"][0]["quantity"] == 10
    assert result["holdings"][0]["market_price"] == 11
    assert result["holdings"][0]["total_cost_base"] == 102
    assert result["total_cash_value"] == 98
    assert result["total_portfolio_value"] == 208
    assert result["replay_basis"]["status"] == "complete"
    assert result["replay_basis"]["source_transaction_ids"] == [r.id for r in records[:2]]
    assert not db.new and not db.dirty and not db.deleted


def test_closed_positions_still_exist_before_sale_and_cash_survives_after_sale(db):
    portfolio, _, _ = seed_book(db)
    result = calculate_portfolio_valuation(db, portfolio.id, date(2026, 1, 6))
    assert result["holdings"] == []
    assert result["total_market_value"] == 0
    assert result["total_portfolio_value"] == 217
    snapshot = record_daily_snapshot(db, portfolio.id, date(2026, 1, 6))
    assert snapshot.calculation_status == "complete"
    assert snapshot.payload_json["replay_basis"]["method"] == "recorded-portfolio-replay-v1"


def test_missing_opening_activity_does_not_create_an_invented_position(db):
    portfolio, _, records = seed_book(db)
    records[1].transaction_type = "manual_adjustment"
    db.commit()
    result = calculate_portfolio_valuation(db, portfolio.id, date(2026, 1, 6))
    assert result["total_portfolio_value"] is None
    assert result["replay_basis"]["status"] == "partial"
    assert any("UNSUPPORTED" in item for item in result["replay_basis"]["blockers"])


def test_unknown_opening_cash_is_a_gap_not_an_implicit_deposit(db):
    portfolio, _, _ = seed_book(db)
    db.query(PortfolioCashBalance).filter_by(portfolio_id=portfolio.id).one().amount += 50
    db.commit()
    result = calculate_portfolio_valuation(db, portfolio.id, date(2026, 1, 3))
    assert result["total_portfolio_value"] is None
    assert "CASH_BALANCE_MISMATCH" in result["replay_basis"]["blockers"]


def test_future_manual_holdings_cannot_appear_before_their_declared_date(db):
    portfolio = Portfolio(name="Mock Data unknown opening", user_id="local-user", base_currency="USD")
    db.add(portfolio)
    db.flush()
    db.add(PortfolioHolding(portfolio_id=portfolio.id, ticker="FUTURE", currency="USD", quantity=10,
        average_cost=10, as_of_date=date(2026, 3, 1)))
    db.commit()
    result = calculate_portfolio_valuation(db, portfolio.id, date(2026, 1, 3))
    assert result["holdings"] == []
    assert result["total_portfolio_value"] is None
    assert result["replay_basis"]["status"] == "not_available"


def test_replay_is_scoped_to_the_owned_portfolio(db):
    portfolio, _, _ = seed_book(db)
    with pytest.raises(ValueError, match="not found"):
        calculate_portfolio_valuation(db, portfolio.id, date(2026, 1, 3), user_id="another-owner")


def test_purchase_date_fx_and_partial_sale_cost_reconcile_independently(db):
    from app.models import FxRateObservation
    from app.services.portfolio_period_attribution import calculate_period_attribution
    portfolio = Portfolio(name="Mock Data FX replay", base_currency="USD")
    company = Company(ticker="EURTEST", name="Mock Data EUR", currency="EUR")
    db.add_all([portfolio, company])
    db.flush()
    record_activity(db, portfolio, company, date(2026, 1, 1), "deposit", 1000)
    record_activity(db, portfolio, company, date(2026, 1, 1), "buy", 2, 100, 2)
    record_activity(db, portfolio, company, date(2026, 1, 2), "buy", 1, 120)
    record_activity(db, portfolio, company, date(2026, 1, 3), "sell", 1, 130, 1)
    for day, rate in [(1, "1.1"), (2, "1.2"), (4, "1.4")]:
        db.add(FxRateObservation(base_currency="EUR", quote_currency="USD", rate=Decimal(rate),
            as_of_date=date(2026, 1, day), provider_name="Mock Data"))
    for day, price in [(2, 130), (4, 140)]:
        db.add(MarketPrice(company_id=company.id, ticker=company.ticker, currency="EUR", price=price, as_of_date=date(2026, 1, day)))
    db.commit()
    result = calculate_portfolio_valuation(db, portfolio.id, date(2026, 1, 4))
    holding = result["holdings"][0]
    assert holding["quantity"] == 2
    assert holding["total_cost_base"] == pytest.approx((202 * 1.1 + 120 * 1.2) * 2 / 3)
    assert len(holding["cost_fx_observation_ids"]) == 2
    assert result["total_cash_value"] == pytest.approx(807 * 1.4)
    assert result["total_portfolio_value"] == pytest.approx(1521.8)
    record_daily_snapshot(db, portfolio.id, date(2026, 1, 2))
    record_daily_snapshot(db, portfolio.id, date(2026, 1, 4))
    report = calculate_period_attribution(db, portfolio.id, date(2026, 1, 2), date(2026, 1, 4))
    assert report["calculation_status"] == "complete"
    assert report["total_change"] == pytest.approx(240.2)
    assert report["unexplained_change"] == pytest.approx(0, abs=1e-6)


def test_explicit_corporate_actions_preserve_cost_and_do_not_double_adjust_price(db):
    portfolio = Portfolio(name="Mock Data corporate actions", base_currency="USD")
    company = Company(ticker="ACTION", name="Mock Data actions", currency="USD")
    db.add_all([portfolio, company])
    db.flush()
    for day, kind, qty, price in [(1, "deposit", 200, 0), (2, "buy", 10, 10),
        (3, "split", 2, 0), (4, "bonus", 5, 0), (5, "dividend", 8, 999),
        (6, "fee", 1, 0), (7, "tax", 2, 0), (8, "withdrawal", 10, 0)]:
        record_activity(db, portfolio, company, date(2026, 1, day), kind, qty, price)
    price = MarketPrice(company_id=company.id, ticker=company.ticker, currency="USD", price=5,
        as_of_date=date(2026, 1, 8), adjustment_state="unadjusted")
    db.add(price)
    db.commit()
    result = calculate_portfolio_valuation(db, portfolio.id, date(2026, 1, 8))
    assert result["holdings"][0]["quantity"] == 25
    assert result["holdings"][0]["total_cost_base"] == 100
    assert result["total_cash_value"] == 95
    assert result["total_portfolio_value"] == 220
    risk = calculate_portfolio_risk_return(db, portfolio.id, date(2026, 1, 8), min_observations=2)
    assert risk["portfolio_volatility_annualized"] is None
    assert any("corporate action" in message for message in risk["holdings"][0]["warnings"])
    price.adjustment_state = "adjusted"
    db.commit()
    adjusted = calculate_portfolio_valuation(db, portfolio.id, date(2026, 1, 8))
    assert adjusted["total_portfolio_value"] is None
    assert "PRICE_ADJUSTMENT_BASIS_UNSUPPORTED" in adjusted["replay_basis"]["blockers"]


def test_replayed_risk_matches_an_independent_covariance_reference(db):
    portfolio = Portfolio(name="Mock Data independent risk", base_currency="USD")
    first = Company(ticker="RISKONE", name="Mock Data first risk", currency="USD")
    second = Company(ticker="RISKTWO", name="Mock Data second risk", currency="USD")
    db.add_all([portfolio, first, second])
    db.flush()
    record_activity(db, portfolio, None, date(2026, 1, 1), "deposit", 787500)
    record_activity(db, portfolio, first, date(2026, 1, 1), "buy", 4608, 100)
    record_activity(db, portfolio, second, date(2026, 1, 1), "buy", 3267, 100)
    for company, prices in [(first, [100, 110, 99, 108.9, 98.01]),
                            (second, [100, 120, 96, 115.2, 92.16])]:
        for day, price in enumerate(prices, 1):
            db.add(MarketPrice(company_id=company.id, ticker=company.ticker,
                currency="USD", price=price, as_of_date=date(2026, 1, day),
                provider_name="mock_independent_risk", adjustment_state="unadjusted"))
    db.commit()
    result = calculate_portfolio_risk_return(db, portfolio.id, date(2026, 1, 5), min_observations=4)
    # Returns alternate +/-10% and +/-20%. Their sample annual covariance
    # matrix is [[3.36, 6.72], [6.72, 13.44]]. Ending holdings weigh 60%/40%.
    # Independently: portfolio variance = 6.5856; no service helper is reused.
    assert result["risk_calculation_status"] == "complete"
    assert result["portfolio_volatility_annualized"] == pytest.approx(2.5662423891752706)
    rows = {row["ticker"]: row for row in result["holdings"]}
    assert rows["RISKONE"]["risk_model_weight_decimal"] == pytest.approx(0.6)
    assert rows["RISKTWO"]["risk_model_weight_decimal"] == pytest.approx(0.4)
    assert rows["RISKONE"]["marginal_volatility"] == pytest.approx(1.833030277982336)
    assert rows["RISKTWO"]["marginal_volatility"] == pytest.approx(3.666060555964672)
    assert rows["RISKONE"]["component_risk"] == pytest.approx(1.0998181667894016)
    assert rows["RISKTWO"]["component_risk"] == pytest.approx(1.4664242223858694)
    assert result["risk_reconciliation_error"] == pytest.approx(0, abs=1e-12)


def test_deleted_closed_holding_keeps_historical_risk_identity(db):
    portfolio, company, _ = seed_book(db)
    record_activity(db, portfolio, company, date(2026, 1, 16), "sell", 4, 20)
    db.query(PortfolioHolding).filter_by(portfolio_id=portfolio.id).delete()
    for day, price in [(1, 10), (2, 12)]:
        db.add(MarketPrice(company_id=company.id, ticker=company.ticker, currency="USD", price=price, as_of_date=date(2026, 1, day)))
    db.commit()
    result = calculate_portfolio_risk_return(db, portfolio.id, date(2026, 1, 3), min_observations=2)
    assert result["risk_calculation_status"] == "complete"
    assert result["holdings"][0]["holding_id"] is None
    assert result["holdings"][0]["current_market_value_base"] == 110
    assert result["risk_reconciliation_error"] == pytest.approx(0)


def test_snapshot_manual_edit_invalidates_server_calculated_provenance(client, db):
    portfolio, _, _ = seed_book(db)
    portfolio.user_id = "admin_user_id_fallback"
    db.commit()
    snapshot = record_daily_snapshot(db, portfolio.id, date(2026, 1, 3))
    assert snapshot.calculation_status == "complete"
    response = client.patch(f"/portfolio-snapshots/{snapshot.id}", json={"total_market_value": 999, "calculation_status": "complete"})
    assert response.status_code == 200, response.text
    assert response.json()["data"]["calculation_status"] == "partial"
    assert response.json()["data"]["payload_json"]["replay_basis"]["method"] == "manual-snapshot-v1"


def test_bounded_replay_and_hash_are_read_only_and_changes_are_visible(db, monkeypatch):
    from app.services import portfolio_replay
    portfolio, _, records = seed_book(db)
    before = calculate_portfolio_valuation(db, portfolio.id, date(2026, 1, 3))["replay_basis"]["input_sha256"]
    records[0].notes = "A private note is excluded from calculation hashes."
    db.commit()
    assert calculate_portfolio_valuation(db, portfolio.id, date(2026, 1, 3))["replay_basis"]["input_sha256"] == before
    records[0].quantity += 1
    db.commit()
    changed = calculate_portfolio_valuation(db, portfolio.id, date(2026, 1, 3))
    assert changed["replay_basis"]["input_sha256"] != before
    assert changed["total_portfolio_value"] is None
    monkeypatch.setattr(portfolio_replay, "MAX_TRANSACTIONS", 1)
    limited = calculate_portfolio_valuation(db, portfolio.id, date(2026, 1, 3))
    assert limited["replay_basis"]["blockers"] == ["ACTIVITY_LIMIT_EXCEEDED"]
    assert limited["total_portfolio_value"] is None
    assert not db.new and not db.dirty and not db.deleted


def test_corrected_activity_marks_saved_returns_provisional_without_rewriting_snapshots(db):
    from copy import deepcopy
    from app.services.portfolio_performance import calculate_time_weighted_return
    portfolio, _, records = seed_book(db)
    first = record_daily_snapshot(db, portfolio.id, date(2026, 1, 3))
    second = record_daily_snapshot(db, portfolio.id, date(2026, 1, 6))
    before = deepcopy(first.payload_json)
    report = calculate_time_weighted_return(db, portfolio.id, first.snapshot_date, second.snapshot_date)
    assert report.calculation_status == "complete"
    assert report.return_decimal == pytest.approx(217 / 208 - 1)
    records[0].quantity += 1
    db.commit()
    corrected = calculate_time_weighted_return(db, portfolio.id, first.snapshot_date, second.snapshot_date)
    assert corrected.calculation_status == "partial"
    assert any("changed activity" in warning for warning in corrected.warnings)
    assert first.payload_json == before
