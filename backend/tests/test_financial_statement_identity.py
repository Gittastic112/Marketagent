from datetime import date

import pytest

from app.models import Company, FinancialMetric, FinancialStatementPeriod
from app.services.assumption_autofill_engine import AssumptionAutofillEngine
from app.services.financial_statement_identity import FinancialStatementIdentityService
from helpers import response_data


def _seed_period(db, *, metrics: dict[str, float], year: int = 2025):
    company = Company(
        ticker=f"IDENT{year}",
        name=f"Identity Test {year}",
        market="IN",
        country="India",
        currency="INR",
    )
    db.add(company)
    db.flush()
    period = FinancialStatementPeriod(
        company_id=company.id,
        period_type="annual",
        year=year,
        report_date=date(year, 3, 31),
        currency="INR",
        currency_source="reviewed_candidate_unit",
        currency_confidence="high",
    )
    db.add(period)
    db.flush()
    db.add_all(
        FinancialMetric(
            period_id=period.id,
            metric_name=metric_name,
            value=value,
            unit="INR crore",
        )
        for metric_name, value in metrics.items()
    )
    db.commit()
    return company, period


def test_statement_identities_pass_within_explicit_tolerance(db):
    company, _ = _seed_period(db, metrics={
        "net_income": 100.005,
        "pre_tax_income": 125,
        "tax_expense": 25,
        "net_income_parent": 98,
        "net_income_nci": 2,
    })

    report = FinancialStatementIdentityService.evaluate_company(db, company.id)

    assert report["status"] == "passed"
    assert report["passed_check_count"] == 2
    assert report["failed_check_count"] == 0
    assert report["tolerance_contract"]["absolute_tolerance"] == 0.01
    assert report["periods"][0]["checks"][0]["delta"] == pytest.approx(0.005)


def test_statement_identity_reports_missing_inputs_without_false_failure(db):
    company, _ = _seed_period(db, metrics={"net_income": 100, "revenue": 1000})

    report = FinancialStatementIdentityService.evaluate_company(db, company.id)

    assert report["status"] == "not_available"
    assert report["applicable_check_count"] == 0
    assert report["unavailable_check_count"] == 2
    assert report["periods"][0]["checks"][0]["missing_metrics"] == [
        "pre_tax_income",
        "tax_expense",
    ]


def test_statement_identity_fails_arithmetic_mismatch_and_duplicate_metric(db):
    company, period = _seed_period(db, metrics={
        "net_income": 100,
        "pre_tax_income": 140,
        "tax_expense": 25,
        "net_income_parent": 98,
        "net_income_nci": 2,
    })
    db.add(FinancialMetric(
        period_id=period.id,
        metric_name="net_income_parent",
        value=97,
        unit="INR crore",
    ))
    db.commit()

    report = FinancialStatementIdentityService.evaluate_company(db, company.id)
    checks = {check["identity_code"]: check for check in report["periods"][0]["checks"]}

    assert report["status"] == "failed"
    assert checks["profit_after_tax"]["status"] == "failed"
    assert checks["profit_after_tax"]["delta"] == -15
    assert checks["profit_attribution"]["status"] == "failed"
    assert checks["profit_attribution"]["ambiguous_metrics"] == ["net_income_parent"]


def test_statement_identity_endpoint_returns_period_checks(client, db):
    company, _ = _seed_period(db, metrics={
        "net_income": 100,
        "pre_tax_income": 125,
        "tax_expense": 25,
        "net_income_parent": 98,
        "net_income_nci": 2,
    })

    response = client.get(
        f"/api/companies/{company.id}/financial-statements/identities"
    )
    report = response_data(response)

    assert report["status"] == "passed"
    assert report["periods"][0]["checks"][0]["formula"] == (
        "net_income = pre_tax_income - tax_expense"
    )
    assert response.json()["meta"]["source"] == "internal"


def test_failed_identity_downgrades_valuation_autofill_trust(db):
    company, _ = _seed_period(db, metrics={
        "revenue": 1000,
        "ebit": 200,
        "net_income": 100,
        "pre_tax_income": 150,
        "tax_expense": 25,
        "net_income_parent": 98,
        "net_income_nci": 2,
    })

    draft = AssumptionAutofillEngine.draft_assumptions(db, company.id)

    identity = draft["source_metadata"]["financial_statement_identity"]
    assert identity["status"] == "failed"
    assert identity["valuation_trust_status"] == "blocked"
    assert draft["provenance"]["starting_revenue"]["requires_review"] is True
    assert any("identity checks failed" in warning for warning in draft["warnings"])
