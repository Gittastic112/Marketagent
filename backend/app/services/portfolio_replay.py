"""Dated recorded activity, without inferred opening positions or broker claims."""
from collections import defaultdict
from datetime import date
from decimal import Decimal
from hashlib import sha256
import json
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, Portfolio, PortfolioCashBalance, PortfolioHolding, PortfolioTransaction
from app.services.fx_rates import FxRateUnavailable, convert_amount

METHOD = "recorded-portfolio-replay-v1"
MAX_TRANSACTIONS = 20_000
ZERO = Decimal("0")
PRECISION = Decimal("0.000001")
HASH_FIELDS = ("id", "company_id", "ticker", "transaction_type", "quantity", "price", "fees", "currency", "transaction_date")


def activity_input_hash(records) -> str:
    return sha256(json.dumps([{key: str(getattr(item, key)) for key in HASH_FIELDS} for item in records],
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def snapshot_replay_is_verified(snapshot, db: Session | None = None) -> bool:
    basis = (snapshot.payload_json or {}).get("replay_basis")
    verified = (isinstance(basis, dict) and basis.get("method") == METHOD
        and basis.get("status") == "complete" and bool(basis.get("input_sha256"))
        and bool(basis.get("source_transaction_ids")))
    if verified and db is not None:
        rows = db.execute(select(*(getattr(PortfolioTransaction, key) for key in HASH_FIELDS)).where(
            PortfolioTransaction.portfolio_id == snapshot.portfolio_id,
            PortfolioTransaction.transaction_date <= snapshot.snapshot_date).order_by(
                PortfolioTransaction.transaction_date, PortfolioTransaction.id).limit(MAX_TRANSACTIONS + 1)).all()
        verified = len(rows) <= MAX_TRANSACTIONS and activity_input_hash(rows) == basis["input_sha256"]
    return verified


def manual_snapshot_basis(payload):
    return {**(payload or {}), "replay_basis": {"method": "manual-snapshot-v1", "status": "not_assessed",
        "claim_type": "User Assumption", "blockers": ["MANUALLY_EDITED_SNAPSHOT"]}}


def _key(record):
    return record.company_id, record.ticker.upper(), record.currency.upper()


def _book(transactions, convert_cost=None):
    positions, cash, blockers, missing_fx = {}, defaultdict(lambda: ZERO), set(), set()
    for item in transactions:
        quantity, price, fees = (Decimal(str(value)) for value in (item.quantity, item.price, item.fees))
        if any(not value.is_finite() or value < 0 for value in (quantity, price, fees)):
            blockers.add("INVALID_ACTIVITY_VALUE")
            continue
        currency, kind = item.currency.upper(), item.transaction_type
        delta = ZERO
        if kind in {"buy", "sell", "split", "bonus"}:
            key = _key(item)
            if item.company_id is None:
                blockers.add("SECURITY_IDENTITY_UNRESOLVED")
            position = positions.setdefault(key, SimpleNamespace(id=None, company_id=item.company_id,
                ticker=key[1], currency=currency, quantity=ZERO, cost=ZERO, cost_basis_base=ZERO,
                as_of_date=item.transaction_date, transaction_ids=[], cost_fx_ids=set(), cost_fx_is_stale=False))
            position.transaction_ids.append(item.id)
            position.as_of_date = item.transaction_date
            if kind == "buy":
                cost = quantity * price + fees
                position.quantity += quantity
                position.cost += cost
                delta = -cost
                if convert_cost is not None:
                    try:
                        converted, fx = convert_cost(cost, currency, item.transaction_date)
                        if position.cost_basis_base is not None:
                            position.cost_basis_base += converted
                        if fx.observation_id is not None:
                            position.cost_fx_ids.add(fx.observation_id)
                        position.cost_fx_is_stale |= fx.is_stale
                    except FxRateUnavailable:
                        position.cost_basis_base = None
                        missing_fx.add(currency)
            elif kind == "sell":
                if quantity > position.quantity or position.quantity == 0:
                    blockers.add("OVERSELL_OR_MISSING_OPENING_POSITION")
                    continue
                fraction = (position.quantity - quantity) / position.quantity
                position.cost *= fraction
                if position.cost_basis_base is not None:
                    position.cost_basis_base *= fraction
                position.quantity -= quantity
                delta = quantity * price - fees
            elif position.quantity <= 0 or (kind == "split" and quantity <= 0):
                blockers.add("CORPORATE_ACTION_WITHOUT_POSITION")
            elif fees != 0:
                blockers.add("UNSUPPORTED_CORPORATE_ACTION_FEES")
            elif kind == "split":
                position.quantity = (position.quantity * quantity).quantize(PRECISION)
            else:
                position.quantity += quantity
        elif kind in {"deposit", "dividend"}:
            delta = quantity - fees
        elif kind in {"withdrawal", "fee", "tax"}:
            delta = -(quantity + fees)
        else:
            blockers.add("UNSUPPORTED_ACTIVITY_TYPE")
            continue
        cash[currency] = (cash[currency] + delta).quantize(PRECISION)
        if cash[currency] < 0:
            blockers.add("NEGATIVE_CASH_OR_MISSING_OPENING_FUNDING")
    return positions, dict(cash), blockers, missing_fx


def replay_portfolio(db: Session, portfolio: Portfolio, target_date: date):
    records = list(db.scalars(select(PortfolioTransaction)
        .where(PortfolioTransaction.portfolio_id == portfolio.id)
        .order_by(PortfolioTransaction.transaction_date, PortfolioTransaction.id).limit(MAX_TRANSACTIONS + 1)))
    basis = {"method": METHOD, "as_of_date": target_date.isoformat(), "claim_type": "Calculation",
        "status": "not_available", "source_transaction_ids": [], "blockers": [],
        "ordering": "transaction_date then record ID; intraday/settlement timing is not recorded",
        "position_method": "Recorded buys/sales and explicit split ratios/bonus quantities; average cost including purchase fees",
        "cash_method": "Recorded deposits/withdrawals, trade consideration, dividends, fees and taxes",
        "limitations": ["Unrecorded opening balances or activity cannot be reconstructed.",
            "Recorded activity is not broker verification. Dividends and corporate actions require explicit records; never combine adjusted prices with a second action adjustment."]}
    if not records:
        basis["blockers"] = ["NO_RECORDED_ACTIVITY"]
        return None, None, basis
    if len(records) > MAX_TRANSACTIONS:
        basis["blockers"] = ["ACTIVITY_LIMIT_EXCEEDED"]
        return [], [], basis
    included = [item for item in records if item.transaction_date <= target_date]
    basis["source_transaction_ids"] = [item.id for item in included]
    basis["corporate_actions"] = [{"id": item.id, "company_id": item.company_id, "ticker": item.ticker,
        "date": item.transaction_date.isoformat(), "kind": item.transaction_type, "quantity": str(item.quantity)}
        for item in included if item.transaction_type in {"split", "bonus"}]
    basis["input_sha256"] = activity_input_hash(included)
    fx_cache = {}
    def convert_cost(amount, currency, day):
        key = currency, day
        if key not in fx_cache:
            _, fx_cache[key] = convert_amount(db, Decimal(1), currency, portfolio.base_currency, day)
        fx = fx_cache[key]
        return amount * fx.rate, fx
    positions, cash, blockers, missing_fx = _book(included, convert_cost)
    full_positions, full_cash, full_blockers, _ = _book(records)
    current = list(db.scalars(select(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio.id)))
    by_key = defaultdict(list)
    for holding in current:
        by_key[_key(holding)].append(holding)
    if any(len(items) != 1 for items in by_key.values()):
        blockers.add("AMBIGUOUS_CURRENT_HOLDINGS")
    for key in set(by_key) | set(full_positions):
        stored_quantity = sum((item.quantity for item in by_key.get(key, [])), ZERO)
        replayed_quantity = full_positions[key].quantity if key in full_positions else ZERO
        if abs(stored_quantity - replayed_quantity) > PRECISION:
            blockers.add("POSITION_BALANCE_MISMATCH")
    cash_records = list(db.scalars(select(PortfolioCashBalance).where(PortfolioCashBalance.portfolio_id == portfolio.id)
        .order_by(PortfolioCashBalance.as_of_date.desc(), PortfolioCashBalance.id.desc())))
    stored_cash = {}
    for item in cash_records:
        stored_cash.setdefault(item.currency.upper(), item)
    for currency in set(stored_cash) | set(full_cash):
        stored = stored_cash[currency].amount if currency in stored_cash else ZERO
        if abs(stored - full_cash.get(currency, ZERO)) > PRECISION:
            blockers.add("CASH_BALANCE_MISMATCH")
    if full_blockers:
        blockers.add("CURRENT_LEDGER_RECONCILIATION_UNAVAILABLE")
    companies = {item.id: item for item in db.scalars(select(Company).where(Company.id.in_({key[0] for key in positions if key[0] is not None})))}
    holdings = []
    for key, position in positions.items():
        if position.quantity <= 0:
            continue
        position.id = by_key[key][0].id if len(by_key.get(key, [])) == 1 else None
        position.company = companies.get(position.company_id)
        position.average_cost = position.cost / position.quantity
        position.is_replayed = True
        if position.company is None or not position.company.currency or position.company.currency.upper() != position.currency:
            blockers.add("SECURITY_CURRENCY_MISMATCH")
        holdings.append(position)
    basis.update(status="complete" if included and not blockers else "partial" if included else "not_available",
        blockers=sorted(blockers), missing_cost_fx_pairs=sorted(f"{currency}/{portfolio.base_currency.upper()}" for currency in missing_fx),
        reconciliation_holding_ids=[item.id for item in current],
        reconciliation_cash_balance_ids=[item.id for item in stored_cash.values()],
        first_recorded_date=records[0].transaction_date.isoformat())
    balances = [SimpleNamespace(id=None, currency=currency, amount=amount, as_of_date=target_date) for currency, amount in sorted(cash.items())]
    return holdings, balances, basis
