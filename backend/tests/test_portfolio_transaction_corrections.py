"""Mock Data chronological corrections with independent expected balances."""
from datetime import date
from decimal import Decimal
import pytest
from app.models import Company, Portfolio, PortfolioHolding, PortfolioCashBalance, PortfolioTransaction
from test_portfolio_replay import record_activity


def book(db):
    portfolio = Portfolio(name="Mock Data corrections", base_currency="USD")
    company = Company(ticker="FIXBOOK", name="Mock Data corrections", currency="USD")
    db.add_all([portfolio, company]); db.flush()
    record_activity(db, portfolio, None, date(2026, 1, 1), "deposit", 2000)
    buy = record_activity(db, portfolio, company, date(2026, 1, 2), "buy", 10, 100)
    split = record_activity(db, portfolio, company, date(2026, 1, 3), "split", 2)
    record_activity(db, portfolio, company, date(2026, 1, 4), "bonus", 5)
    sell = record_activity(db, portfolio, company, date(2026, 1, 5), "sell", 5, 60)
    db.commit()
    return portfolio, buy, split, sell


def balances(db, portfolio):
    db.expire_all()
    holding = db.query(PortfolioHolding).filter_by(portfolio_id=portfolio.id).one()
    cash = db.query(PortfolioCashBalance).filter_by(portfolio_id=portfolio.id).one()
    return holding.quantity, holding.average_cost, holding.as_of_date, cash.amount, cash.as_of_date


def test_notes_only_edit_never_reapplies_old_accounting(client, db_session):
    portfolio, buy, _, _ = book(db_session)
    before = balances(db_session, portfolio)
    response = client.patch(f"/portfolio-transactions/{buy.id}", json={"notes": "Mock Data corrected note"})
    assert response.status_code == 200, response.text
    assert balances(db_session, portfolio) == before


def test_earlier_purchase_change_replays_later_actions_and_sale(client, db_session):
    portfolio, buy, _, _ = book(db_session)
    response = client.patch(f"/portfolio-transactions/{buy.id}", json={"quantity": 12})
    assert response.status_code == 200, response.text
    qty, cost, day, cash, cash_day = balances(db_session, portfolio)
    assert qty == 24  # 12*2 +5 -5
    assert cost == pytest.approx(Decimal(1200) / 29, abs=Decimal(".000001"))
    assert cash == 1100 and day == cash_day == date(2026, 1, 5)


def test_split_deletion_replays_subsequent_bonus_and_sale(client, db_session):
    portfolio, _, split, _ = book(db_session)
    response = client.delete(f"/portfolio-transactions/{split.id}")
    assert response.status_code == 204, response.text
    qty, cost, day, cash, _ = balances(db_session, portfolio)
    assert qty == 10 and cost == pytest.approx(Decimal(1000) / 15, abs=Decimal(".000001"))
    assert day == date(2026, 1, 5) and cash == 1300


@pytest.mark.parametrize("change", ["delete_buy", "oversell", "move_sale_early", "unknown_opening"])
def test_unreplayable_correction_is_atomic(client, db_session, change):
    portfolio, buy, _, sell = book(db_session)
    if change == "unknown_opening":
        db_session.query(PortfolioHolding).filter_by(portfolio_id=portfolio.id).one().quantity += 1
        db_session.commit()
    before = balances(db_session, portfolio)
    if change == "delete_buy":
        response = client.delete(f"/portfolio-transactions/{buy.id}")
    else:
        row = buy if change == "unknown_opening" else sell
        update = {"transaction_date": "2026-01-01"} if change == "move_sale_early" else {"quantity": 100}
        response = client.patch(f"/portfolio-transactions/{row.id}", json=update)
    assert response.status_code == 409, response.text
    assert balances(db_session, portfolio) == before
    assert db_session.get(PortfolioTransaction, buy.id).quantity == 10

def test_backdated_insert_replays_subsequent_actions_and_rolls_back_invalid_activity(client, db_session):
    portfolio, buy, _, _ = book(db_session)
    payload = dict(portfolio_id=portfolio.id, company_id=buy.company_id, ticker=buy.ticker,
        currency="USD", transaction_type="buy", transaction_date="2026-01-02", quantity=2, price=100, fees=0)
    inserted = client.post("/portfolio-transactions", json=payload)
    assert inserted.status_code == 201, inserted.text
    after = balances(db_session, portfolio)
    assert after[0] == 24 and after[3] == 1100
    rejected = client.post("/portfolio-transactions", json=payload | {"quantity": 1000})
    assert rejected.status_code == 409
    assert balances(db_session, portfolio) == after
    assert client.delete(f"/portfolio-transactions/{inserted.json()['data']['id']}").status_code == 204
    assert balances(db_session, portfolio)[0] == 20
