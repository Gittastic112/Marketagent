"""Accounting identity cases without a database or synthetic application data."""
from datetime import date
from types import SimpleNamespace

import pytest

from app.services.financial_statement_identity import FinancialStatementIdentityService
from app.services.sec_xbrl_extractor import select_annual_facts


def period(metrics):
    return SimpleNamespace(
        id=1, year=2025, quarter=None, period_type="annual",
        report_date=date(2025, 12, 31), currency="USD",
        metrics=[SimpleNamespace(metric_name=key, value=value, unit="USD million")
                 for key, value in metrics],
    )


@pytest.mark.parametrize("pretax,tax,adjustment,profit", [
    (37557, 7120, -12, 30425),
    (68614, 9265, -101, 59248),
    (97311, 19087, -554, 77670),
    (100, 20, 10, 90),
    (100, 20, 0, 80),
    (-100, -20, -5, -85),
])
def test_explicit_after_tax_equity_income_keeps_reported_sign(pretax, tax, adjustment, profit):
    report = FinancialStatementIdentityService.evaluate_period(period([
        ("pre_tax_income", pretax), ("tax_expense", tax), ("net_income", profit),
        ("equity_method_income_after_tax", adjustment),
    ]))
    check = report["checks"][0]
    assert check["status"] == "passed"
    assert check["expected_value"] == profit
    assert check["inputs"]["equity_method_income_after_tax"] == adjustment
    assert check["formula"] == (
        "net_income = pre_tax_income - tax_expense + equity_method_income_after_tax"
    )


def test_absent_adjustment_does_not_invent_reconciling_amount():
    check = FinancialStatementIdentityService.evaluate_period(period([
        ("pre_tax_income", 100), ("tax_expense", 20), ("net_income", 75),
    ]))["checks"][0]
    assert check["status"] == "failed"
    assert check["delta"] == -5
    assert check["formula"] == "net_income = pre_tax_income - tax_expense"
    assert "equity_method_income_after_tax" not in check["inputs"]


def test_ambiguous_after_tax_adjustment_blocks_identity():
    check = FinancialStatementIdentityService.evaluate_period(period([
        ("pre_tax_income", 100), ("tax_expense", 20), ("net_income", 75),
        ("equity_method_income_after_tax", -5), ("equity_method_income_after_tax", -5),
    ]))["checks"][0]
    assert check["status"] == "failed"
    assert check["ambiguous_metrics"] == ["equity_method_income_after_tax"]
    assert check["blocking"]


def test_before_tax_equity_income_is_not_added_again():
    check = FinancialStatementIdentityService.evaluate_period(period([
        ("pre_tax_income", 100), ("tax_expense", 20), ("net_income", 80),
        ("equity_method_income_before_tax", 5),
    ]))["checks"][0]
    assert check["status"] == "passed"
    assert "equity_method_income_before_tax" not in check["inputs"]


def test_generic_sec_equity_income_does_not_infer_after_tax_presentation():
    facts = {"IncomeLossFromEquityMethodInvestments": {
        "label": "Income (Loss) from Equity Method Investments",
        "units": {"USD": [
            {"start": "2025-01-01", "end": "2025-12-31", "val": -554000000,
             "filed": "2026-02-06", "form": "10-K", "fp": "FY"},
            {"start": "2025-10-01", "end": "2025-12-31", "val": -1,
             "filed": "2026-02-07", "form": "10-K", "fp": "FY"},
        ]},
    }}
    selected = select_annual_facts(facts, "USD")
    # The actual generic SEC concept does not establish statement presentation.
    # An exact report review must establish the after-tax metric separately.
    assert ("equity_method_income_after_tax", 2025) not in selected
