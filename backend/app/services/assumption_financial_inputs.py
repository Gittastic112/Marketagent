import hashlib
import json
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.financial import FinancialMetric, FinancialStatementPeriod, NormalizedFinancialMetric, NormalizedFinancialSnapshot
from app.services.assumption_provenance import DERIVED_NORMALIZED_METRICS, _freshness_metadata, _provenance
from app.services.valuation_input_units import canonical_financial_input

def financial_history_signature(db: Session, company_id: int) -> str:
    rows = db.execute(
        select(
            FinancialStatementPeriod.year,
            FinancialStatementPeriod.period_type,
            FinancialStatementPeriod.report_date,
            FinancialStatementPeriod.currency,
            FinancialMetric.metric_name,
            FinancialMetric.value,
            FinancialMetric.unit,
        )
        .join(FinancialMetric, FinancialMetric.period_id == FinancialStatementPeriod.id)
        .where(FinancialStatementPeriod.company_id == company_id)
        .order_by(
            FinancialStatementPeriod.year,
            FinancialStatementPeriod.period_type,
            FinancialMetric.metric_name,
        )
    ).all()
    source_payload = [
        [year, period_type, report_date.isoformat(), currency, metric_name, value, unit]
        for year, period_type, report_date, currency, metric_name, value, unit in rows
    ]
    normalized_payload = [
        list(row)
        for row in db.execute(
            select(
                FinancialStatementPeriod.year,
                FinancialStatementPeriod.period_type,
                NormalizedFinancialMetric.metric_code,
                NormalizedFinancialMetric.value,
                NormalizedFinancialMetric.unit,
                NormalizedFinancialMetric.warnings,
            )
            .join(
                NormalizedFinancialSnapshot,
                NormalizedFinancialSnapshot.period_id == FinancialStatementPeriod.id,
            )
            .join(
                NormalizedFinancialMetric,
                NormalizedFinancialMetric.snapshot_id == NormalizedFinancialSnapshot.id,
            )
            .where(FinancialStatementPeriod.company_id == company_id)
            .order_by(
                FinancialStatementPeriod.year,
                FinancialStatementPeriod.period_type,
                NormalizedFinancialMetric.metric_code,
            )
        ).all()
    ]
    payload = {"source": source_payload, "normalized": normalized_payload}
    return hashlib.sha256(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _extract_latest_actuals(db: Session, company: Company) -> Dict[str, tuple[float, Dict[str, Any]]]:
    """
    Extract the latest reviewed/promoted financial metrics for valuation autofill.
    """
    period = db.scalar(
        select(FinancialStatementPeriod)
        .where(FinancialStatementPeriod.company_id == company.id)
        .where(FinancialStatementPeriod.period_type == "annual")
        .order_by(FinancialStatementPeriod.year.desc(), FinancialStatementPeriod.report_date.desc())
    )
    if period is None:
        return {}

    period_str = f"FY{period.year}"
    financial_freshness = _freshness_metadata(
        period.report_date.isoformat(),
        550,
    )

    def currency_metadata(unit: str | None) -> Dict[str, Any]:
        unit_upper = (unit or "").upper()
        has_explicit_metric_currency = bool(period.currency and period.currency.upper() in unit_upper)
        source = "reviewed_metric_unit" if has_explicit_metric_currency else period.currency_source
        confidence = "high" if has_explicit_metric_currency else period.currency_confidence
        return {
            "reporting_currency": period.currency,
            "reporting_currency_source": source,
            "reporting_currency_confidence": confidence,
        }

    legacy_metrics = {}
    for metric in db.scalars(
        select(FinancialMetric).where(FinancialMetric.period_id == period.id)
    ):
        legacy_metrics[metric.metric_name] = (
            metric.value,
            _provenance(
                "company_actual",
                f"Legacy Metrics ({period_str})",
                "medium",
                source_table="financial_metrics",
                source_record_id=metric.id,
                period_id=period.id,
                fiscal_year=period.year,
                period_type=period.period_type,
                report_date=period.report_date.isoformat(),
                unit=metric.unit,
                **financial_freshness,
                **currency_metadata(metric.unit),
            ),
        )
    normalized_metrics = {}
    snapshot = db.scalar(
        select(NormalizedFinancialSnapshot)
        .where(NormalizedFinancialSnapshot.company_id == company.id)
        .where(NormalizedFinancialSnapshot.period_id == period.id)
        .order_by(NormalizedFinancialSnapshot.updated_at.desc(), NormalizedFinancialSnapshot.id.desc())
    )
    if snapshot is not None:
        for metric in db.scalars(
            select(NormalizedFinancialMetric).where(NormalizedFinancialMetric.snapshot_id == snapshot.id)
        ):
            is_derived = metric.metric_code in DERIVED_NORMALIZED_METRICS or (metric.provenance_notes or "").startswith("Computed:")
            normalized_metrics[metric.metric_code] = (
                metric.value,
                _provenance(
                    "calculation" if is_derived else "company_actual",
                    f"Normalized Financials ({period_str})",
                    "medium" if metric.warnings else "high",
                    source_table="normalized_financial_metrics",
                    source_record_id=metric.id,
                    snapshot_id=snapshot.id,
                    period_id=period.id,
                    fiscal_year=period.year,
                    period_type=period.period_type,
                    report_date=period.report_date.isoformat(),
                    unit=metric.unit,
                    **{
                        **financial_freshness,
                        "requires_review": bool(metric.warnings) or financial_freshness["requires_review"],
                    },
                    **currency_metadata(metric.unit),
                    provenance_notes=metric.provenance_notes,
                    warnings=metric.warnings,
                ),
            )

    if snapshot is None:
        metrics = legacy_metrics
    else:
        bridge_fallbacks = {}
        for metric_code in (
            "cash",
            "debt",
            "diluted_shares",
            "basic_shares",
            "lease_liabilities",
            "operating_leases",
            "cross_holdings",
            "minority_interests",
            "preferred_stock",
            "employee_options_value",
            "cost_of_debt",
            "new_debt_issued",
            "debt_repaid",
            "dividends",
            "buybacks",
            "stock_issuances",
            "book_equity",
        ):
            if metric_code not in legacy_metrics or metric_code in normalized_metrics:
                continue
            value, source = legacy_metrics[metric_code]
            bridge_fallbacks[metric_code] = (
                value,
                {
                    **source,
                    "fallback_policy": "same_period_missing_normalized_bridge_metric",
                    "normalized_snapshot_id": snapshot.id,
                },
            )
        metrics = {**bridge_fallbacks, **normalized_metrics}

    metrics = {key: canonical_financial_input(key, value, source, period.currency)
               for key, (value, source) in metrics.items()}
    actuals: Dict[str, tuple[float, Dict[str, Any]]] = {}
    for source_key, target_key in (
        ("revenue", "revenue"),
        ("cash", "cash"),
        ("debt", "debt"),
        ("diluted_shares", "diluted_shares"),
        ("basic_shares", "basic_shares"),
        ("operating_leases", "operating_leases"),
        ("cross_holdings", "cross_holdings"),
        ("minority_interests", "minority_interests"),
        ("preferred_stock", "preferred_stock"),
        ("employee_options_value", "employee_options_value"),
        ("cost_of_debt", "cost_of_debt"),
        ("effective_tax_rate", "effective_tax_rate"),
        ("invested_capital", "invested_capital"),
        ("net_income", "net_income"),
        ("capex", "capex"),
        ("depreciation", "depreciation"),
        ("change_in_nwc", "change_in_nwc"),
        ("new_debt_issued", "new_debt_issued"),
        ("debt_repaid", "debt_repaid"),
        ("dividends", "dividends"),
        ("buybacks", "buybacks"),
        ("stock_issuances", "stock_issuances"),
        ("book_equity", "book_value_of_equity"),
    ):
        if source_key in metrics:
            actuals[target_key] = metrics[source_key]
    if "operating_leases" not in actuals and "lease_liabilities" in metrics:
        actuals["operating_leases"] = metrics["lease_liabilities"]

    revenue_tuple = metrics.get("revenue")
    ebit_tuple = metrics.get("ebit")
    if revenue_tuple and ebit_tuple and revenue_tuple[0] not in (None, 0) and ebit_tuple[0] is not None:
        is_normalized = "Normalized" in ebit_tuple[1]["label"]
        actuals["operating_margin"] = (
            ebit_tuple[0] / revenue_tuple[0],
            _provenance(
                "calculation",
                f"Calculated from Normalized Financials ({period_str})" if is_normalized else f"Calculated from Legacy Metrics ({period_str})",
                "high" if is_normalized else "medium",
                calculation_basis={
                    "revenue": revenue_tuple[1],
                    "ebit": ebit_tuple[1],
                },
                **financial_freshness,
            )
        )

    invested_capital_tuple = metrics.get("invested_capital")
    if (revenue_tuple and revenue_tuple[0] is not None and invested_capital_tuple
            and invested_capital_tuple[0] is not None and invested_capital_tuple[0] > 0):
        actuals["sales_to_capital"] = (
            revenue_tuple[0] / invested_capital_tuple[0],
            _provenance(
                "calculation",
                f"Calculated from Normalized Financials ({period_str})",
                "high",
                calculation_basis={
                    "revenue": revenue_tuple[1],
                    "invested_capital": invested_capital_tuple[1],
                },
                **financial_freshness,
            ),
        )

    revenue_history = _extract_revenue_history(db, company.id)
    if revenue_history is not None:
        actuals["historical_revenue_growth"] = revenue_history

    return actuals


def _extract_revenue_history(
    db: Session,
    company_id: int,
) -> Optional[tuple[float, Dict[str, Any]]]:
    periods = list(
        db.scalars(
            select(FinancialStatementPeriod)
            .where(FinancialStatementPeriod.company_id == company_id)
            .where(FinancialStatementPeriod.period_type == "annual")
            .order_by(FinancialStatementPeriod.year.asc(), FinancialStatementPeriod.report_date.asc())
        )
    )
    history: list[tuple[int, float, Dict[str, Any]]] = []
    for period in periods[-6:]:
        snapshot = db.scalar(
            select(NormalizedFinancialSnapshot)
            .where(NormalizedFinancialSnapshot.period_id == period.id)
            .order_by(NormalizedFinancialSnapshot.updated_at.desc(), NormalizedFinancialSnapshot.id.desc())
        )
        metric = None
        if snapshot is not None:
            metric = db.scalar(
                select(NormalizedFinancialMetric)
                .where(NormalizedFinancialMetric.snapshot_id == snapshot.id)
                .where(NormalizedFinancialMetric.metric_code == "revenue")
            )
        if metric is not None and metric.value > 0:
            source = _provenance(
                "company_actual",
                f"Normalized Financials (FY{period.year})",
                "high",
                source_table="normalized_financial_metrics",
                source_record_id=metric.id,
                snapshot_id=snapshot.id,
                period_id=period.id,
                fiscal_year=period.year,
                unit=metric.unit,
                reporting_currency=period.currency,
            )
            value, source = canonical_financial_input("revenue", metric.value, source, period.currency)
            if value is None:
                return None
            history.append((period.year, value, source))
            continue

        if snapshot is not None:
            continue

        legacy_metric = db.scalar(
            select(FinancialMetric)
            .where(FinancialMetric.period_id == period.id)
            .where(FinancialMetric.metric_name == "revenue")
        )
        if legacy_metric is not None and legacy_metric.value > 0:
            source = _provenance(
                "company_actual",
                f"Legacy Metrics (FY{period.year})",
                "medium",
                source_table="financial_metrics",
                source_record_id=legacy_metric.id,
                period_id=period.id,
                fiscal_year=period.year,
                unit=legacy_metric.unit,
                reporting_currency=period.currency,
            )
            value, source = canonical_financial_input("revenue", legacy_metric.value, source, period.currency)
            if value is None:
                return None
            history.append((period.year, value, source))

    if len(history) < 2 or len({source["reporting_currency"] for _, _, source in history}) != 1:
        return None

    oldest_year, oldest_revenue, _ = history[0]
    latest_year, latest_revenue, _ = history[-1]
    year_span = latest_year - oldest_year
    if year_span <= 0:
        return None

    cagr = (latest_revenue / oldest_revenue) ** (1 / year_span) - 1
    requires_review = cagr > 0.50 or cagr < -0.20
    return (
        cagr,
        _provenance(
            "calculation",
            f"Historical Revenue CAGR (FY{oldest_year}-FY{latest_year})",
            "medium" if requires_review else "high",
            calculation_basis=[source for _, _, source in history],
            history_years=[year for year, _, _ in history],
            history_values=[value for _, value, _ in history],
            requires_review=requires_review,
            warnings="Historical revenue CAGR is outside the normal review range." if requires_review else None,
        ),
    )
