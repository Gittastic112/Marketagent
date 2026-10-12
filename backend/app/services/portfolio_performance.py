from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from math import isfinite

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PortfolioSnapshot
from app.services.portfolio_cash_flows import normalize_external_cash_flows
from app.services.portfolio_replay import snapshot_replay_is_verified

LEGACY_WARNING = "Legacy snapshot history or subsequently changed activity is unverified for transaction replay; this return is provisional."


@dataclass
class ReturnMetric:
    calculation_status: str
    return_decimal: float | None
    start_date: date | None
    end_date: date
    warnings: list[str] = field(default_factory=list)
    source_snapshot_ids: list[int] = field(default_factory=list)
    source_transaction_ids: list[int] = field(default_factory=list)


def _xnpv(rate: float, cash_flows: list[tuple[date, float]]) -> float:
    first_date = cash_flows[0][0]
    return sum(
        amount / ((1.0 + rate) ** ((flow_date - first_date).days / 365.25))
        for flow_date, amount in cash_flows
    )


def _solve_xirr(cash_flows: list[tuple[date, float]]) -> float | None:
    if not cash_flows or not any(amount < 0 for _, amount in cash_flows) or not any(
        amount > 0 for _, amount in cash_flows
    ):
        return None
    low = -0.999999
    high = 1.0
    low_value = _xnpv(low, cash_flows)
    high_value = _xnpv(high, cash_flows)
    while low_value * high_value > 0 and high < 1_000_000:
        high *= 2
        high_value = _xnpv(high, cash_flows)
    if low_value * high_value > 0:
        return None
    for _ in range(200):
        midpoint = (low + high) / 2
        value = _xnpv(midpoint, cash_flows)
        if abs(value) < 1e-9:
            return midpoint
        if low_value * value <= 0:
            high = midpoint
        else:
            low = midpoint
            low_value = value
    result = (low + high) / 2
    return result if isfinite(result) else None


def calculate_money_weighted_return(
    db: Session,
    portfolio_id: int,
    as_of_date: date,
) -> ReturnMetric:
    snapshot = db.scalar(
        select(PortfolioSnapshot).where(
            PortfolioSnapshot.portfolio_id == portfolio_id,
            PortfolioSnapshot.snapshot_date == as_of_date,
        )
    )
    if snapshot is None or snapshot.calculation_status != "complete" or snapshot.total_portfolio_value is None:
        return ReturnMetric(
            calculation_status="not_available",
            return_decimal=None,
            start_date=None,
            end_date=as_of_date,
            warnings=["A complete point-in-time snapshot is required on the performance end date."],
        )

    report = normalize_external_cash_flows(db, portfolio_id, end_date=as_of_date)
    if not report.complete:
        return ReturnMetric(
            calculation_status="not_available",
            return_decimal=None,
            start_date=None,
            end_date=as_of_date,
            warnings=[
                "Money-weighted return is blocked because one or more external cash flows lack historical FX.",
                *[f"Missing FX pair: {pair}" for pair in report.missing_fx_pairs],
            ],
            source_snapshot_ids=[snapshot.id],
            source_transaction_ids=report.missing_transaction_ids,
        )

    investor_cash_flows = [
        (flow.transaction_date, float(-flow.amount_base)) for flow in report.flows
    ]
    investor_cash_flows.append((as_of_date, float(snapshot.total_portfolio_value)))
    investor_cash_flows.sort(key=lambda item: item[0])
    if not report.flows or investor_cash_flows[0][0] == as_of_date:
        return ReturnMetric(
            calculation_status="not_available",
            return_decimal=None,
            start_date=investor_cash_flows[0][0] if investor_cash_flows else None,
            end_date=as_of_date,
            warnings=["At least one earlier external cash flow is required for money-weighted return."],
            source_snapshot_ids=[snapshot.id],
        )

    result = _solve_xirr(investor_cash_flows)
    warnings = []
    verified = snapshot_replay_is_verified(snapshot, db)
    if not verified:
        warnings.append(LEGACY_WARNING)
    if any(flow.fx_is_stale for flow in report.flows):
        warnings.append("One or more cash-flow FX observations were stale on the transaction date.")
    if result is None:
        warnings.append("The recorded cash-flow pattern does not produce a unique solvable XIRR.")
    return ReturnMetric(
        calculation_status=("complete" if verified else "partial") if result is not None else "not_available",
        return_decimal=result,
        start_date=investor_cash_flows[0][0],
        end_date=as_of_date,
        warnings=warnings,
        source_snapshot_ids=[snapshot.id],
        source_transaction_ids=[flow.transaction_id for flow in report.flows],
    )


def calculate_time_weighted_return(
    db: Session,
    portfolio_id: int,
    start_date: date,
    end_date: date,
) -> ReturnMetric:
    if end_date <= start_date:
        return ReturnMetric(
            calculation_status="not_available",
            return_decimal=None,
            start_date=start_date,
            end_date=end_date,
            warnings=["Performance end date must be after the start date."],
        )
    snapshots = list(
        db.scalars(
            select(PortfolioSnapshot)
            .where(
                PortfolioSnapshot.portfolio_id == portfolio_id,
                PortfolioSnapshot.snapshot_date >= start_date,
                PortfolioSnapshot.snapshot_date <= end_date,
                PortfolioSnapshot.calculation_status == "complete",
                PortfolioSnapshot.total_portfolio_value.is_not(None),
            )
            .order_by(PortfolioSnapshot.snapshot_date, PortfolioSnapshot.id)
        )
    )
    if len(snapshots) < 2 or snapshots[0].snapshot_date != start_date or snapshots[-1].snapshot_date != end_date:
        return ReturnMetric(
            calculation_status="not_available",
            return_decimal=None,
            start_date=start_date,
            end_date=end_date,
            warnings=["Complete point-in-time snapshots are required on both period boundaries."],
            source_snapshot_ids=[snapshot.id for snapshot in snapshots],
        )

    compounded = 1.0
    source_transactions: list[int] = []
    warnings: list[str] = []
    timing_is_partial = False
    replay_is_partial = not all(snapshot_replay_is_verified(snapshot, db) for snapshot in snapshots)
    if replay_is_partial:
        warnings.append(LEGACY_WARNING)
    for previous, current in zip(snapshots, snapshots[1:]):
        starting_value = float(previous.total_portfolio_value)
        if starting_value <= 0:
            return ReturnMetric(
                calculation_status="not_available",
                return_decimal=None,
                start_date=start_date,
                end_date=end_date,
                warnings=["Time-weighted return requires positive starting value for every subperiod."],
                source_snapshot_ids=[snapshot.id for snapshot in snapshots],
            )
        report = normalize_external_cash_flows(
            db,
            portfolio_id,
            start_date=previous.snapshot_date,
            end_date=current.snapshot_date,
        )
        if not report.complete:
            return ReturnMetric(
                calculation_status="not_available",
                return_decimal=None,
                start_date=start_date,
                end_date=end_date,
                warnings=[
                    "Time-weighted return is blocked because an external cash flow lacks historical FX.",
                    *[f"Missing FX pair: {pair}" for pair in report.missing_fx_pairs],
                ],
                source_snapshot_ids=[snapshot.id for snapshot in snapshots],
                source_transaction_ids=report.missing_transaction_ids,
            )
        net_flow = float(report.net_external_cash_flow or Decimal("0"))
        ending_value = float(current.total_portfolio_value)
        subperiod_growth = (ending_value - net_flow) / starting_value
        if subperiod_growth < 0:
            return ReturnMetric(
                calculation_status="not_available",
                return_decimal=None,
                start_date=start_date,
                end_date=end_date,
                warnings=["A cash-flow-adjusted subperiod value was negative; return is not meaningful."],
                source_snapshot_ids=[snapshot.id for snapshot in snapshots],
            )
        compounded *= subperiod_growth
        source_transactions.extend(flow.transaction_id for flow in report.flows)
        if report.flows:
            timing_is_partial = True
        if any(flow.fx_is_stale for flow in report.flows):
            warnings.append("One or more cash-flow FX observations were stale on the transaction date.")

    if timing_is_partial:
        warnings.append(
            "External cash flows use an end-of-subperiod adjustment because intraday pre-flow valuations are unavailable."
        )
    return ReturnMetric(
        calculation_status="partial" if timing_is_partial or replay_is_partial else "complete",
        return_decimal=compounded - 1.0,
        start_date=start_date,
        end_date=end_date,
        warnings=warnings,
        source_snapshot_ids=[snapshot.id for snapshot in snapshots],
        source_transaction_ids=source_transactions,
    )
