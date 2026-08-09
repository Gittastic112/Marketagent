from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Portfolio, PortfolioTransaction
from app.services.fx_rates import FxRateUnavailable, convert_amount


@dataclass(frozen=True)
class ExternalCashFlow:
    transaction_id: int
    transaction_date: date
    currency: str
    amount_local: Decimal
    amount_base: Decimal
    fx_rate: Decimal
    fx_observation_id: int | None
    fx_as_of_date: date
    fx_is_stale: bool


@dataclass
class ExternalCashFlowReport:
    base_currency: str
    flows: list[ExternalCashFlow] = field(default_factory=list)
    missing_fx_pairs: list[str] = field(default_factory=list)
    missing_transaction_ids: list[int] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not self.missing_transaction_ids

    @property
    def net_external_cash_flow(self) -> Decimal | None:
        if not self.complete:
            return None
        return sum((flow.amount_base for flow in self.flows), Decimal("0"))


def normalize_external_cash_flows(
    db: Session,
    portfolio_id: int,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> ExternalCashFlowReport:
    portfolio = db.get(Portfolio, portfolio_id)
    if portfolio is None:
        raise ValueError(f"Portfolio {portfolio_id} not found")

    query = select(PortfolioTransaction).where(
        PortfolioTransaction.portfolio_id == portfolio_id,
        PortfolioTransaction.transaction_type.in_(("deposit", "withdrawal")),
    )
    if start_date is not None:
        query = query.where(PortfolioTransaction.transaction_date > start_date)
    if end_date is not None:
        query = query.where(PortfolioTransaction.transaction_date <= end_date)
    transactions = list(
        db.scalars(query.order_by(PortfolioTransaction.transaction_date, PortfolioTransaction.id))
    )

    report = ExternalCashFlowReport(base_currency=portfolio.base_currency.upper())
    missing_pairs: set[str] = set()
    for transaction in transactions:
        direction = Decimal("1") if transaction.transaction_type == "deposit" else Decimal("-1")
        local_amount = Decimal(transaction.quantity) * direction
        try:
            base_amount, conversion = convert_amount(
                db,
                local_amount,
                transaction.currency,
                portfolio.base_currency,
                transaction.transaction_date,
            )
        except FxRateUnavailable:
            missing_pairs.add(f"{transaction.currency.upper()}/{portfolio.base_currency.upper()}")
            report.missing_transaction_ids.append(transaction.id)
            continue
        report.flows.append(
            ExternalCashFlow(
                transaction_id=transaction.id,
                transaction_date=transaction.transaction_date,
                currency=transaction.currency.upper(),
                amount_local=local_amount,
                amount_base=base_amount,
                fx_rate=conversion.rate,
                fx_observation_id=conversion.observation_id,
                fx_as_of_date=conversion.as_of_date,
                fx_is_stale=conversion.is_stale,
            )
        )
    report.missing_fx_pairs = sorted(missing_pairs)
    return report
