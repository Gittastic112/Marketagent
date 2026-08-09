from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
import scipy.optimize as optimize

from app.models import Portfolio, PortfolioTransaction, PortfolioSnapshot
from app.services.portfolio_valuation import calculate_portfolio_valuation


class PortfolioPerformanceEngine:

    @staticmethod
    def calculate_xirr(db: Session, portfolio_id: int, as_of_date: date | None = None) -> float | None:
        """
        Calculates the Money-Weighted Return (XIRR) based on portfolio cash flows.
        """
        target_date = as_of_date or date.today()

        transactions = db.scalars(
            select(PortfolioTransaction)
            .where(PortfolioTransaction.portfolio_id == portfolio_id)
            .where(PortfolioTransaction.transaction_date <= target_date)
            .order_by(PortfolioTransaction.transaction_date.asc())
        ).all()

        if not transactions:
            return None

        # Get current portfolio value
        valuation = calculate_portfolio_valuation(db, portfolio_id, target_date)
        current_value = valuation.get("total_portfolio_value")
        if current_value is None:
            return None

        cash_flows = []
        for t in transactions:
            # Positive cash flow means user added cash to the portfolio (buying assets)
            # Actually standard IRR: inflows (deposits) are negative, outflows (withdrawals/final value) are positive.
            # But here transactions are buys/sells of stocks.
            # Real cashflows into the *portfolio* (deposits) should be negative.
            # For simplicity, we assume 'deposit' type transactions.
            # If we just have stock transactions, it's harder. Let's assume cash flows are explicitly tracked.
            # We'll mock the extraction here:
            if t.transaction_type.lower() == "deposit":
                cash_flows.append((t.transaction_date, -float(t.quantity * t.price)))
            elif t.transaction_type.lower() == "withdrawal":
                cash_flows.append((t.transaction_date, float(t.quantity * t.price)))

        # If no deposits/withdrawals, we can't calculate a meaningful user-level XIRR
        if not cash_flows:
            return None

        cash_flows.append((target_date, float(current_value)))

        def xnpv(rate, cfs):
            return sum([cf / (1 + rate)**((d - cash_flows[0][0]).days / 365.25) for d, cf in cfs])

        try:
            xirr = optimize.newton(lambda r: xnpv(r, cash_flows), 0.1)
            return float(xirr)
        except (RuntimeError, ValueError, OverflowError):
            return None

    @staticmethod
    def calculate_twr(db: Session, portfolio_id: int, start_date: date, end_date: date) -> float | None:
        """
        Calculates the Time-Weighted Return (TWR) using historical snapshots.
        """
        snapshots = db.scalars(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.portfolio_id == portfolio_id)
            .where(PortfolioSnapshot.snapshot_date >= start_date)
            .where(PortfolioSnapshot.snapshot_date <= end_date)
            .order_by(PortfolioSnapshot.snapshot_date.asc())
        ).all()

        if len(snapshots) < 2:
            return None

        twr = 1.0
        for i in range(1, len(snapshots)):
            prev = snapshots[i-1]
            curr = snapshots[i]

            # TWR calculation assumes no cash flows between snapshots, or adjusts for them.
            # Simple approximation: (Value_end - CashFlow) / Value_start
            # For now, we mock the basic TWR component.
            prev_val = float(prev.total_market_value or 0) + float(prev.total_cash or 0)
            curr_val = float(curr.total_market_value or 0) + float(curr.total_cash or 0)

            if prev_val > 0:
                period_return = curr_val / prev_val
                twr *= period_return

        return twr - 1.0
