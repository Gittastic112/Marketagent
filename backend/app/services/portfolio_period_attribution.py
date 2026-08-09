from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, PortfolioSnapshot
from app.services.portfolio_cash_flows import normalize_external_cash_flows


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
    formula = (
        "Total change = price movement + FX impact + position change + cash change + unexplained change; "
        "cash change = external cash flow + internal cash change."
    )
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
            "cash_change": None,
            "external_cash_flow": None,
            "internal_cash_change": None,
            "unexplained_change": None,
            "holdings": [],
            "attribution_by_sector": {},
            "attribution_by_geography": {},
            "attribution_by_asset_type": {},
            "attribution_by_tag": {},
            "warnings": ["Complete source-provenance snapshots are required on both period boundaries."],
            "blockers": ["missing_complete_boundary_snapshot"],
            "confidence": "invalid",
            "formula": formula,
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
            "cash_change": None,
            "external_cash_flow": None,
            "internal_cash_change": None,
            "unexplained_change": None,
            "holdings": [],
            "attribution_by_sector": {},
            "attribution_by_geography": {},
            "attribution_by_asset_type": {},
            "attribution_by_tag": {},
            "warnings": warnings,
            "blockers": ["base_currency_changed"],
            "confidence": "invalid",
            "formula": formula,
            "source_snapshot_ids": [start.id, end.id],
            "source_transaction_ids": [],
        }

    start_holdings = _holdings(start)
    end_holdings = _holdings(end)
    holding_results: list[dict] = []
    total_price_movement = 0.0
    total_fx_impact = 0.0
    price_complete = True
    fx_complete = True
    total_position_change = 0.0
    component_complete = True
    blockers: list[str] = []
    for key in sorted(set(start_holdings).union(end_holdings)):
        beginning = start_holdings.get(key)
        ending = end_holdings.get(key)
        if beginning is None or ending is None:
            boundary = ending or beginning
            market_value_base = boundary.get("market_value_base") if boundary else None
            if market_value_base is None:
                component_complete = False
                blockers.append(f"missing_boundary_value:{key}")
                holding_results.append(
                    {
                        "key": key,
                        "company_id": boundary.get("company_id") if boundary else None,
                        "ticker": boundary.get("ticker") if boundary else None,
                        "price_movement": None,
                        "fx_impact": None,
                        "position_change": None,
                        "calculation_status": "not_available",
                    }
                )
                continue
            position_change = float(market_value_base) if beginning is None else -float(market_value_base)
            total_position_change += position_change
            holding_results.append(
                {
                    "key": key,
                    "company_id": boundary.get("company_id"),
                    "ticker": boundary.get("ticker"),
                    "price_movement": 0.0,
                    "fx_impact": 0.0,
                    "position_change": position_change,
                    "total_contribution": position_change,
                    "calculation_status": "complete",
                }
            )
            continue
        required = (
            beginning.get("quantity"),
            beginning.get("market_price"),
            ending.get("market_price"),
            beginning.get("market_fx_rate_to_base"),
            ending.get("market_fx_rate_to_base"),
        )
        if any(value is None for value in required) or beginning.get("currency") != ending.get("currency"):
            price_complete = False
            fx_complete = False
            component_complete = False
            blockers.append(f"missing_comparable_holding_inputs:{key}")
            holding_results.append(
                {
                    "key": key,
                    "company_id": ending.get("company_id") or beginning.get("company_id"),
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
        fx_impact = (
            float(beginning["quantity"])
            * float(ending["market_price"])
            * (
                float(ending["market_fx_rate_to_base"])
                - float(beginning["market_fx_rate_to_base"])
            )
        )
        total_fx_impact += fx_impact
        if beginning.get("market_value_base") is None or ending.get("market_value_base") is None:
            component_complete = False
            blockers.append(f"missing_position_value:{key}")
            position_change = None
        else:
            position_change = (
                float(ending["market_value_base"])
                - float(beginning["market_value_base"])
                - price_movement
                - fx_impact
            )
            total_position_change += position_change
        holding_results.append(
            {
                "key": key,
                "company_id": ending.get("company_id") or beginning.get("company_id"),
                "ticker": ending.get("ticker") or beginning.get("ticker"),
                "price_movement": price_movement,
                "fx_impact": fx_impact,
                "position_change": position_change,
                "total_contribution": (
                    price_movement + fx_impact + position_change
                    if position_change is not None
                    else None
                ),
                "calculation_status": "complete" if position_change is not None else "not_available",
            }
        )

    if not price_complete:
        warnings.append("One or more continuing holdings lack comparable price or FX inputs.")
    flow_report = normalize_external_cash_flows(
        db,
        portfolio_id,
        start_date=start_date,
        end_date=end_date,
    )
    external_cash_flow = (
        float(flow_report.net_external_cash_flow)
        if flow_report.net_external_cash_flow is not None
        else None
    )
    if not flow_report.complete:
        component_complete = False
        blockers.append("missing_external_flow_fx")
        warnings.append("External cash-flow attribution is blocked by missing historical FX.")
    cash_change = None
    internal_cash_change = None
    if start.total_cash is not None and end.total_cash is not None:
        cash_change = float(end.total_cash - start.total_cash)
        if external_cash_flow is not None:
            internal_cash_change = cash_change - external_cash_flow
    else:
        component_complete = False
        blockers.append("missing_snapshot_cash_total")
        warnings.append("Snapshot cash totals are required for internal position-flow reconciliation.")

    total_change = float(end.total_portfolio_value - start.total_portfolio_value)
    unexplained_change = None
    if (
        component_complete
        and price_complete
        and fx_complete
        and cash_change is not None
    ):
        unexplained_change = (
            total_change
            - total_price_movement
            - total_fx_impact
            - total_position_change
            - cash_change
        )
        if abs(unexplained_change) > 0.01:
            warnings.append(
                "Attribution does not reconcile within 0.01 base-currency units; inspect snapshot provenance."
            )
            component_complete = False
            blockers.append("reconciliation_out_of_tolerance")

    stale_inputs = any(
        holding.get("is_stale_price")
        or holding.get("market_fx_is_stale")
        or holding.get("cost_fx_is_stale")
        for holding in [*start_holdings.values(), *end_holdings.values()]
    )
    if stale_inputs:
        warnings.append("One or more boundary price or FX inputs were stale at snapshot capture time.")

    company_ids = {
        holding["company_id"]
        for holding in holding_results
        if holding.get("company_id") is not None
    }
    companies = {
        company.id: company
        for company in db.scalars(select(Company).where(Company.id.in_(company_ids))).all()
    } if company_ids else {}
    sector_attribution: dict[str, float] = {}
    geography_attribution: dict[str, float] = {}
    asset_type_attribution: dict[str, float] = {}
    tag_attribution: dict[str, float] = {}
    for holding in holding_results:
        contribution = holding.get("total_contribution")
        if contribution is None:
            continue
        company = companies.get(holding.get("company_id"))
        sector = company.sector if company and company.sector else "Unknown"
        geography = company.country if company and company.country else "Unknown"
        asset_type = company.asset_type if company and company.asset_type else "Unknown"
        sector_attribution[sector] = sector_attribution.get(sector, 0.0) + contribution
        geography_attribution[geography] = geography_attribution.get(geography, 0.0) + contribution
        asset_type_attribution[asset_type] = asset_type_attribution.get(asset_type, 0.0) + contribution
        tags = company.exposure_tags if company else []
        for tag in tags:
            tag_attribution[tag.name] = tag_attribution.get(tag.name, 0.0) + contribution
    calculation_status = "complete" if component_complete and price_complete and fx_complete else "partial"
    confidence = "high" if calculation_status == "complete" and not stale_inputs else "medium"
    if calculation_status == "partial":
        confidence = "low"
    return {
        "portfolio_id": portfolio_id,
        "start_date": start_date,
        "end_date": end_date,
        "base_currency": end.base_currency,
        "calculation_status": calculation_status,
        "total_change": total_change,
        "price_movement": total_price_movement if price_complete else None,
        "fx_impact": total_fx_impact if fx_complete else None,
        "position_change": total_position_change if component_complete else None,
        "cash_change": cash_change,
        "external_cash_flow": external_cash_flow,
        "internal_cash_change": internal_cash_change,
        "unexplained_change": unexplained_change,
        "holdings": holding_results,
        "attribution_by_sector": sector_attribution,
        "attribution_by_geography": geography_attribution,
        "attribution_by_asset_type": asset_type_attribution,
        "attribution_by_tag": tag_attribution,
        "warnings": warnings,
        "blockers": sorted(set(blockers)),
        "confidence": confidence,
        "formula": formula,
        "source_snapshot_ids": [start.id, end.id],
        "source_transaction_ids": [flow.transaction_id for flow in flow_report.flows],
    }
