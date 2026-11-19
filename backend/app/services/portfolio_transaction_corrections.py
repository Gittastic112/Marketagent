"""Atomic corrections from a reconciled recorded ledger, never inferred openings."""
from decimal import ROUND_HALF_UP
from types import SimpleNamespace

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select

from app.models import Portfolio, PortfolioTransaction, PortfolioHolding, PortfolioCashBalance
from app.schemas.portfolio import PortfolioTransactionCreate
from app.services.portfolio_replay import _book, _key, MAX_TRANSACTIONS, PRECISION, ZERO


def _conflict(reason):
    raise HTTPException(status_code=409, detail=f"Financial correction requires complete, reconciled recorded history: {reason}. No balances were changed.")


def correct_transaction(db, transaction, changes: dict | None, *, inserting: bool = False):
    if not inserting and changes is not None and all(key == "notes" or getattr(transaction, key) == value for key, value in changes.items()):
        # A note does not participate in holdings, cash, timestamps or replay hashes.
        for key, value in changes.items():
            setattr(transaction, key, value)
        return
    portfolio_ids = sorted({transaction.portfolio_id, (changes or {}).get("portfolio_id") or transaction.portfolio_id})
    db.execute(select(Portfolio.id).where(Portfolio.id.in_(portfolio_ids)).order_by(Portfolio.id).with_for_update()).all()
    db.refresh(transaction)
    replacement = transaction if inserting else None
    if changes is not None:
        try:
            values = PortfolioTransactionCreate.model_validate({
                **{key: getattr(transaction, key) for key in PortfolioTransactionCreate.model_fields}, **changes}).model_dump()
        except ValidationError:
            raise HTTPException(status_code=422, detail="The complete corrected transaction must retain valid amounts, identity and date.") from None
        replacement = SimpleNamespace(id=transaction.id, **values)
    plans = []
    for portfolio_id in portfolio_ids:
        records = list(db.scalars(select(PortfolioTransaction).where(PortfolioTransaction.portfolio_id == portfolio_id)
            .order_by(PortfolioTransaction.transaction_date, PortfolioTransaction.id).limit(MAX_TRANSACTIONS + 1)
            .with_for_update().execution_options(populate_existing=True)))
        if inserting:
            records = [row for row in records if row.id != transaction.id]
        if len(records) + int(inserting) > MAX_TRANSACTIONS:
            _conflict("recorded activity exceeds the supported correction limit")
        holdings = list(db.scalars(select(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio_id).with_for_update()))
        balances = list(db.scalars(select(PortfolioCashBalance).where(PortfolioCashBalance.portfolio_id == portfolio_id).with_for_update()))
        old_positions, old_cash, blockers, _ = _book(records)
        if blockers:
            _conflict("opening funding, security identity or ordered activity is incomplete")
        by_key = {_key(row): row for row in holdings}
        by_currency = {row.currency.upper(): row for row in balances}
        if len(by_key) != len(holdings) or len(by_currency) != len(balances):
            _conflict("ambiguous holdings or cash balances")
        for key in set(by_key) | set(old_positions):
            stored, replayed = by_key.get(key), old_positions.get(key)
            quantity = replayed.quantity if replayed else ZERO
            if (stored is None and quantity > 0) or abs((stored.quantity if stored else ZERO) - quantity) > PRECISION:
                _conflict("recorded trades do not explain current positions")
            if quantity and abs(stored.average_cost - replayed.cost / quantity) > PRECISION:
                _conflict("recorded trades do not explain current cost basis")
        for currency in set(by_currency) | set(old_cash):
            if abs((by_currency[currency].amount if currency in by_currency else ZERO) - old_cash.get(currency, ZERO)) > PRECISION:
                _conflict("recorded activity does not explain current cash")
        proposed = [row for row in records if row.id != transaction.id]
        if replacement is not None and replacement.portfolio_id == portfolio_id:
            proposed.append(replacement)
        proposed.sort(key=lambda row: (row.transaction_date, row.id))
        positions, cash, blockers, _ = _book(proposed)
        if blockers:
            _conflict("the correction leaves an unfunded trade, unsupported action or sale without a position")
        plans.append((portfolio_id, by_key, by_currency, proposed, positions, cash))
    # No mutation occurs until both source and destination plans are verified.
    for portfolio_id, holdings, balances, records, positions, cash in plans:
        final_date = max((row.transaction_date for row in records), default=transaction.transaction_date)
        for key in set(holdings) | set(positions):
            row = holdings.get(key)
            position = positions.get(key)
            if row is None:
                row = PortfolioHolding(portfolio_id=portfolio_id, company_id=key[0], ticker=key[1], currency=key[2])
                db.add(row)
            row.quantity = position.quantity if position else ZERO
            row.average_cost = ((position.cost / position.quantity).quantize(PRECISION, rounding=ROUND_HALF_UP)
                if position and position.quantity else ZERO)
            row.as_of_date = position.as_of_date if position else final_date
        for currency in set(balances) | set(cash):
            row = balances.get(currency)
            if row is None:
                row = PortfolioCashBalance(portfolio_id=portfolio_id, currency=currency)
                db.add(row)
            row.amount = cash.get(currency, ZERO)
            row.as_of_date = max((item.transaction_date for item in records if item.currency.upper() == currency), default=final_date)
    if inserting:
        return
    if changes is None:
        db.delete(transaction)
    else:
        for key, value in values.items():
            setattr(transaction, key, value)
