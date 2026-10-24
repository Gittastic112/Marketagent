from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.financial import FinancialStatementPeriod


ABSOLUTE_TOLERANCE = 0.01
RELATIVE_TOLERANCE = 1e-6


IDENTITIES: tuple[dict[str, Any], ...] = (
    {
        "code": "profit_after_tax",
        "label": "Profit after tax",
        "formula": "net_income = pre_tax_income - tax_expense",
        "required_metrics": ("net_income", "pre_tax_income", "tax_expense"),
        "actual_metric": "net_income",
        "expected": lambda values: values["pre_tax_income"] - values["tax_expense"],
    },
    {
        "code": "profit_attribution",
        "label": "Profit attribution",
        "formula": "net_income = net_income_parent + net_income_nci",
        "required_metrics": ("net_income", "net_income_parent", "net_income_nci"),
        "actual_metric": "net_income",
        "expected": lambda values: values["net_income_parent"] + values["net_income_nci"],
    },
)


def _tolerance(actual: float, expected: float) -> float:
    scale = max(abs(actual), abs(expected))
    return max(ABSOLUTE_TOLERANCE, scale * RELATIVE_TOLERANCE)


def _period_status(checks: list[dict[str, Any]]) -> str:
    statuses = {check["status"] for check in checks}
    if "failed" in statuses:
        return "failed"
    if statuses == {"passed"}:
        return "passed"
    if "passed" in statuses:
        return "partial"
    return "not_available"


class FinancialStatementIdentityService:
    """Evaluate source financial facts against explicit accounting identities."""

    @staticmethod
    def evaluate_period(period: FinancialStatementPeriod) -> dict[str, Any]:
        metrics_by_name: dict[str, list[Any]] = defaultdict(list)
        for metric in period.metrics:
            metrics_by_name[metric.metric_name].append(metric)

        checks: list[dict[str, Any]] = []
        for identity in IDENTITIES:
            required_metrics = identity["required_metrics"]
            formula = identity["formula"]
            after_tax_adjustment = (
                identity["code"] == "profit_after_tax"
                and bool(metrics_by_name["equity_method_income_after_tax"])
            )
            if after_tax_adjustment:
                # Only an explicitly reviewed after-tax presentation belongs here.
                # Generic equity-method income may already be included before tax.
                required_metrics = (*required_metrics, "equity_method_income_after_tax")
                formula += " + equity_method_income_after_tax"
            missing_metrics = [name for name in required_metrics if not metrics_by_name[name]]
            ambiguous_metrics = [name for name in required_metrics if len(metrics_by_name[name]) > 1]
            base = {
                "identity_code": identity["code"],
                "label": identity["label"],
                "formula": formula,
                "unit": period.currency,
                "missing_metrics": missing_metrics,
                "ambiguous_metrics": ambiguous_metrics,
            }
            if ambiguous_metrics:
                checks.append({
                    **base,
                    "status": "failed",
                    "actual_value": None,
                    "expected_value": None,
                    "delta": None,
                    "tolerance": None,
                    "inputs": {},
                    "blocking": True,
                })
                continue
            if missing_metrics:
                checks.append({
                    **base,
                    "status": "not_available",
                    "actual_value": None,
                    "expected_value": None,
                    "delta": None,
                    "tolerance": None,
                    "inputs": {},
                    "blocking": False,
                })
                continue

            values = {name: float(metrics_by_name[name][0].value) for name in required_metrics}
            actual = values[identity["actual_metric"]]
            expected_fn: Callable[[dict[str, float]], float] = identity["expected"]
            expected = expected_fn(values)
            if after_tax_adjustment:
                expected += values["equity_method_income_after_tax"]
            delta = actual - expected
            tolerance = _tolerance(actual, expected)
            passed = abs(delta) <= tolerance
            checks.append({
                **base,
                "status": "passed" if passed else "failed",
                "actual_value": actual,
                "expected_value": expected,
                "delta": delta,
                "tolerance": tolerance,
                "inputs": values,
                "blocking": not passed,
            })

        status = _period_status(checks)
        return {
            "period_id": period.id,
            "year": period.year,
            "quarter": period.quarter,
            "period_type": period.period_type,
            "report_date": period.report_date,
            "currency": period.currency,
            "status": status,
            "applicable_check_count": sum(check["status"] != "not_available" for check in checks),
            "passed_check_count": sum(check["status"] == "passed" for check in checks),
            "failed_check_count": sum(check["status"] == "failed" for check in checks),
            "unavailable_check_count": sum(check["status"] == "not_available" for check in checks),
            "checks": checks,
        }

    @staticmethod
    def evaluate_company(
        db: Session,
        company_id: int,
        *,
        period_type: str = "annual",
    ) -> dict[str, Any]:
        periods = list(
            db.scalars(
                select(FinancialStatementPeriod)
                .options(selectinload(FinancialStatementPeriod.metrics))
                .where(
                    FinancialStatementPeriod.company_id == company_id,
                    FinancialStatementPeriod.period_type == period_type,
                )
                .order_by(
                    FinancialStatementPeriod.year.desc(),
                    FinancialStatementPeriod.report_date.desc(),
                )
            )
        )
        results = [FinancialStatementIdentityService.evaluate_period(period) for period in periods]
        failed_period_count = sum(period["status"] == "failed" for period in results)
        passed_period_count = sum(period["status"] == "passed" for period in results)
        partial_period_count = sum(period["status"] == "partial" for period in results)
        unavailable_period_count = sum(period["status"] == "not_available" for period in results)
        applicable_period_count = len(results) - unavailable_period_count

        if failed_period_count:
            status = "failed"
        elif not applicable_period_count:
            status = "not_available"
        elif passed_period_count == len(results):
            status = "passed"
        else:
            status = "partial"

        return {
            "company_id": company_id,
            "period_type": period_type,
            "status": status,
            "tolerance_contract": {
                "absolute_tolerance": ABSOLUTE_TOLERANCE,
                "relative_tolerance": RELATIVE_TOLERANCE,
                "formula": "max(absolute_tolerance, max(abs(actual), abs(expected)) * relative_tolerance)",
            },
            "period_count": len(results),
            "applicable_period_count": applicable_period_count,
            "passed_period_count": passed_period_count,
            "partial_period_count": partial_period_count,
            "failed_period_count": failed_period_count,
            "unavailable_period_count": unavailable_period_count,
            "applicable_check_count": sum(period["applicable_check_count"] for period in results),
            "passed_check_count": sum(period["passed_check_count"] for period in results),
            "failed_check_count": sum(period["failed_check_count"] for period in results),
            "unavailable_check_count": sum(period["unavailable_check_count"] for period in results),
            "periods": results,
        }
