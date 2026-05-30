from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PortfolioCashBalance, PortfolioHolding, PortfolioTransaction


HOLDING_TRANSACTION_TYPES = {"buy", "sell", "split", "bonus", "manual_adjustment"}


def to_decimal(value: object) -> Decimal:
    return Decimal(str(value or 0))


def find_matching_holding(db: Session, transaction: PortfolioTransaction) -> PortfolioHolding | None:
    return db.scalar(
        select(PortfolioHolding)
        .where(
            PortfolioHolding.portfolio_id == transaction.portfolio_id,
            PortfolioHolding.ticker == transaction.ticker,
        )
        .order_by(PortfolioHolding.id)
        .limit(1)
    )


def create_holding_from_transaction(db: Session, transaction: PortfolioTransaction, average_cost: Decimal) -> PortfolioHolding:
    holding = PortfolioHolding(
        portfolio_id=transaction.portfolio_id,
        company_id=transaction.company_id,
        ticker=transaction.ticker,
        quantity=Decimal("0"),
        average_cost=average_cost,
        currency=transaction.currency,
        as_of_date=transaction.transaction_date,
    )
    db.add(holding)
    return holding


def apply_transaction_to_holding(db: Session, transaction: PortfolioTransaction, *, direction: int = 1) -> None:
    if transaction.transaction_type not in HOLDING_TRANSACTION_TYPES:
        return

    quantity = to_decimal(transaction.quantity)
    quantity_delta = quantity * Decimal(direction)
    price = to_decimal(transaction.price)
    fees = to_decimal(transaction.fees)
    holding = find_matching_holding(db, transaction)

    if transaction.transaction_type == "buy":
        if holding is None:
            if direction < 0:
                return
            total_cost = (quantity_delta * price) + fees
            average_cost = total_cost / quantity_delta if quantity_delta > 0 else Decimal("0")
            create_holding_from_transaction(db, transaction, average_cost).quantity = quantity_delta
            return
        apply_buy(holding, quantity_delta, price, fees, transaction)
        return

    if holding is None:
        if direction < 0 and transaction.transaction_type == "sell":
            create_holding_from_transaction(db, transaction, price).quantity = abs(quantity_delta)
            return
        raise HTTPException(status_code=409, detail=f"{transaction.transaction_type} transaction requires an existing holding")

    if transaction.transaction_type == "sell":
        apply_sell(holding, quantity_delta, transaction)
    elif transaction.transaction_type == "split":
        apply_split(holding, quantity, direction, transaction)
    elif transaction.transaction_type == "bonus":
        apply_bonus(holding, quantity_delta, transaction)
    elif transaction.transaction_type == "manual_adjustment":
        apply_manual_adjustment(holding, quantity_delta, transaction)


def apply_buy(
    holding: PortfolioHolding,
    quantity_delta: Decimal,
    price: Decimal,
    fees: Decimal,
    transaction: PortfolioTransaction,
) -> None:
    current_quantity = to_decimal(holding.quantity)
    current_average_cost = to_decimal(holding.average_cost)

    if quantity_delta >= 0:
        new_quantity = current_quantity + quantity_delta
        current_cost = current_quantity * current_average_cost
        added_cost = (quantity_delta * price) + fees
        holding.average_cost = (current_cost + added_cost) / new_quantity if new_quantity > 0 else Decimal("0")
        holding.quantity = new_quantity
    else:
        new_quantity = current_quantity + quantity_delta
        if new_quantity < 0:
            raise HTTPException(status_code=409, detail="Transaction change would make holding quantity negative")
        current_cost = current_quantity * current_average_cost
        removed_cost = (abs(quantity_delta) * price) + fees
        remaining_cost = current_cost - removed_cost
        holding.average_cost = remaining_cost / new_quantity if new_quantity > 0 else Decimal("0")
        holding.quantity = new_quantity

    if holding.company_id is None and transaction.company_id is not None:
        holding.company_id = transaction.company_id
    holding.currency = transaction.currency
    holding.as_of_date = transaction.transaction_date


def apply_sell(holding: PortfolioHolding, quantity_delta: Decimal, transaction: PortfolioTransaction) -> None:
    current_quantity = to_decimal(holding.quantity)
    new_quantity = current_quantity - quantity_delta
    if new_quantity < 0:
        raise HTTPException(status_code=409, detail="Sell transaction exceeds current holding quantity")

    holding.quantity = new_quantity
    if holding.company_id is None and transaction.company_id is not None:
        holding.company_id = transaction.company_id
    holding.currency = transaction.currency
    holding.as_of_date = transaction.transaction_date


def apply_split(holding: PortfolioHolding, split_ratio: Decimal, direction: int, transaction: PortfolioTransaction) -> None:
    if split_ratio <= 0:
        raise HTTPException(status_code=400, detail="Split ratio must be greater than 0")
    
    current_quantity = to_decimal(holding.quantity)
    current_cost = to_decimal(holding.average_cost)
    
    if direction > 0:
        holding.quantity = current_quantity * split_ratio
        holding.average_cost = current_cost / split_ratio if split_ratio > 0 else Decimal("0")
    else:
        holding.quantity = current_quantity / split_ratio
        holding.average_cost = current_cost * split_ratio

    if holding.company_id is None and transaction.company_id is not None:
        holding.company_id = transaction.company_id
    holding.currency = transaction.currency
    holding.as_of_date = transaction.transaction_date


def apply_bonus(holding: PortfolioHolding, quantity_delta: Decimal, transaction: PortfolioTransaction) -> None:
    current_quantity = to_decimal(holding.quantity)
    current_cost = to_decimal(holding.average_cost)
    new_quantity = current_quantity + quantity_delta
    
    if new_quantity < 0:
        raise HTTPException(status_code=409, detail="Bonus rollback exceeds current holding quantity")
        
    holding.quantity = new_quantity
    # Cost basis per share changes because total cost stays the same but quantity changes
    total_cost = current_quantity * current_cost
    holding.average_cost = total_cost / new_quantity if new_quantity > 0 else Decimal("0")

    if holding.company_id is None and transaction.company_id is not None:
        holding.company_id = transaction.company_id
    holding.currency = transaction.currency
    holding.as_of_date = transaction.transaction_date


def apply_manual_adjustment(holding: PortfolioHolding, quantity_delta: Decimal, transaction: PortfolioTransaction) -> None:
    current_quantity = to_decimal(holding.quantity)
    new_quantity = current_quantity + quantity_delta
    
    if new_quantity < 0:
        raise HTTPException(status_code=409, detail="Manual adjustment makes holding quantity negative")
        
    holding.quantity = new_quantity
    
    if holding.company_id is None and transaction.company_id is not None:
        holding.company_id = transaction.company_id
    holding.currency = transaction.currency
    holding.as_of_date = transaction.transaction_date


def get_or_create_cash_balance(db: Session, portfolio_id: int, currency: str, as_of_date: date) -> PortfolioCashBalance:
    from datetime import date
    balance = db.scalar(
        select(PortfolioCashBalance)
        .where(
            PortfolioCashBalance.portfolio_id == portfolio_id,
            PortfolioCashBalance.currency == currency
        )
        .order_by(PortfolioCashBalance.id)
        .limit(1)
    )
    if not balance:
        balance = PortfolioCashBalance(
            portfolio_id=portfolio_id,
            currency=currency,
            amount=Decimal("0"),
            as_of_date=as_of_date
        )
        db.add(balance)
        db.flush()
    else:
        if as_of_date > balance.as_of_date:
            balance.as_of_date = as_of_date
    return balance


def apply_transaction_to_cash(db: Session, transaction: PortfolioTransaction, *, direction: int = 1) -> None:
    t_type = transaction.transaction_type
    
    quantity = to_decimal(transaction.quantity)
    price = to_decimal(transaction.price)
    fees = to_decimal(transaction.fees)
    
    cash_delta = Decimal("0")
    
    if t_type == "buy":
        cash_delta = -((quantity * price) + fees)
    elif t_type == "sell":
        cash_delta = (quantity * price) - fees
    elif t_type in ("deposit", "dividend"):
        cash_delta = quantity - fees
    elif t_type in ("withdrawal", "fee", "tax"):
        cash_delta = -(quantity + fees)
        
    if cash_delta == Decimal("0"):
        return
        
    cash_delta *= Decimal(direction)
    
    balance = get_or_create_cash_balance(db, transaction.portfolio_id, transaction.currency, transaction.transaction_date)
    balance.amount += cash_delta
