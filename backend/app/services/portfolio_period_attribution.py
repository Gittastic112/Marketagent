from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PortfolioSnapshot


def _snapshot(
    db: Session,
    portfolio_id: int,
    snapshot_date: date,
) -> PortfolioSnapshot | None:
    return db.scalar(
        select(PortfolioSnapshot).where(
            PortfolioSnapshot.portfolio_id == portfolio_id,
            PortfolioSnapshot.snapshot_date == snapshot_date,
        )
    )


def _holding_key(holding: dict) -> str:
    company_id = holding.get("company_id")
    return f"company:{company_id}" if company_id is not None else f"ticker:{holding.get('ticker')}"


def _holdings(snapshot: PortfolioSnapshot) -> dict[str, dict]:
    payload = snapshot.payload_json or {}
    return {
        _holding_key(holding): holding
        for holding in payload.get("holdings", [])
        if holding.get("ticker")
    }


def calculate_period_attribution(
    db: Session,
    portfolio_id: int,
    start_date: date,
    end_date: date,
) -> dict:
    start = _snapshot(db, portfolio_id, start_date)
    end = _snapshot(db, portfolio_id, end_date)
    warnings: list[str] = []
    if (
        start is None
        or end is None
        or start.calculation_status != "complete"
        or end.calculation_status != "complete"
        or start.total_portfolio_value is None
        or end.total_portfolio_value is None
    ):
        return {
            "portfolio_id": portfolio_id,
            "start_date": start_date,
            "end_date": end_date,
            "base_currency": (end.base_currency if end else None) or (start.base_currency if start else None),
            "calculation_status": "not_available",
            "total_change": None,
            "price_movement": None,
            "fx_impact": None,
            "position_change": None,
            "external_cash_flow": None,
            "unexplained_change": None,
            "holdings": [],
            "warnings": ["Complete source-provenance snapshots are required on both period boundaries."],
            "source_snapshot_ids": [snapshot.id for snapshot in (start, end) if snapshot],
            "source_transaction_ids": [],
        }
    if start.base_currency != end.base_currency:
        warnings.append("Snapshot base currencies differ; period attribution is blocked.")
        return {
            "portfolio_id": portfolio_id,
            "start_date": start_date,
            "end_date": end_date,
            "base_currency": end.base_currency,
            "calculation_status": "not_available",
            "total_change": None,
            "price_movement": None,
            "fx_impact": None,
            "position_change": None,
            "external_cash_flow": None,
            "unexplained_change": None,
            "holdings": [],
            "warnings": warnings,
            "source_snapshot_ids": [start.id, end.id],
            "source_transaction_ids": [],
        }

    start_holdings = _holdings(start)
    end_holdings = _holdings(end)
    holding_results: list[dict] = []
    total_price_movement = 0.0
    price_complete = True
    for key in sorted(set(start_holdings).intersection(end_holdings)):
        beginning = start_holdings[key]
        ending = end_holdings[key]
        required = (
            beginning.get("quantity"),
            beginning.get("market_price"),
            ending.get("market_price"),
            beginning.get("market_fx_rate_to_base"),
        )
        if any(value is None for value in required) or beginning.get("currency") != ending.get("currency"):
            price_complete = False
            holding_results.append(
                {
                    "key": key,
                    "ticker": ending.get("ticker") or beginning.get("ticker"),
                    "price_movement": None,
                    "fx_impact": None,
                    "position_change": None,
                    "calculation_status": "not_available",
                }
            )
            continue
        price_movement = (
            float(beginning["quantity"])
            * (float(ending["market_price"]) - float(beginning["market_price"]))
            * float(beginning["market_fx_rate_to_base"])
        )
        total_price_movement += price_movement
        holding_results.append(
            {
                "key": key,
                "ticker": ending.get("ticker") or beginning.get("ticker"),
                "price_movement": price_movement,
                "fx_impact": None,
                "position_change": None,
                "calculation_status": "partial",
            }
        )

    if set(start_holdings) != set(end_holdings):
        warnings.append("Holdings entered or exited during the period; position-change attribution is pending.")
    if not price_complete:
        warnings.append("One or more continuing holdings lack comparable price or FX inputs.")
    warnings.append("FX, position-change, and external-flow components are not included in this phase.")
    return {
        "portfolio_id": portfolio_id,
        "start_date": start_date,
        "end_date": end_date,
        "base_currency": end.base_currency,
        "calculation_status": "partial",
        "total_change": float(end.total_portfolio_value - start.total_portfolio_value),
        "price_movement": total_price_movement if price_complete else None,
        "fx_impact": None,
        "position_change": None,
        "external_cash_flow": None,
        "unexplained_change": None,
        "holdings": holding_results,
        "warnings": warnings,
        "source_snapshot_ids": [start.id, end.id],
        "source_transaction_ids": [],
    }
