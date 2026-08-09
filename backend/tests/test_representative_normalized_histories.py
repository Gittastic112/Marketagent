import json
from datetime import date
from pathlib import Path

import pytest

from app.models import Company, FinancialMetric, FinancialStatementPeriod
from app.services.accounting_normalization import MetricNormalizationEngine
from app.services.assumption_autofill_engine import AssumptionAutofillEngine
from helpers import response_data


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "normalized_financial_histories.json"
SHARE_METRICS = {"basic_shares", "diluted_shares"}


def load_histories() -> dict:
    return json.loads(FIXTURE_PATH.read_text())


@pytest.mark.parametrize("history_index", [0, 1], ids=["us-history", "india-history"])
def test_representative_history_normalizes_reconciles_and_autofills(
    client,
    db,
    history_index: int,
) -> None:
    fixture = load_histories()
    assert fixture["fixture_metadata"]["is_mock"] is True
    assert fixture["fixture_metadata"]["claim_type"] == "Mock Data"

    history = fixture["histories"][history_index]
    company_data = history["company"]
    company = Company(**company_data)
    db.add(company)
    db.flush()

    for period_data in history["periods"]:
        period = FinancialStatementPeriod(
            company_id=company.id,
            period_type="annual",
            year=period_data["year"],
            report_date=date.fromisoformat(period_data["report_date"]),
            currency=company.currency,
            currency_source="mock_integration_fixture",
            currency_confidence="high",
        )
        db.add(period)
        db.flush()
        db.add_all(
            [
                FinancialMetric(
                    period_id=period.id,
                    metric_name=metric_name,
                    value=value,
                    unit=(
                        "million shares"
                        if metric_name in SHARE_METRICS
                        else f"{company.currency} million"
                    ),
                )
                for metric_name, value in period_data["metrics"].items()
            ]
        )
        db.flush()
        MetricNormalizationEngine.normalize_period(db, period.id, commit=False)
    db.commit()

    coverage = response_data(
        client.get(
            f"/api/companies/{company.id}/financial-statements/normalized/coverage"
        )
    )
    assert coverage["status"] == "complete"
    assert coverage["period_count"] == 3
    assert coverage["normalized_period_count"] == 3
    assert coverage["trust_ready_period_count"] == 3
    assert coverage["coverage_percent"] == 100

    reconciliation = response_data(
        client.get(
            f"/api/companies/{company.id}/financial-statements/normalized/reconciliation"
        )
    )
    assert reconciliation["status"] == "complete"
    assert reconciliation["mismatch_count"] == 0
    assert reconciliation["missing_normalized_count"] == 0
    assert reconciliation["normalized_only_count"] == 0
    assert reconciliation["exact_count"] >= 48

    draft = AssumptionAutofillEngine.draft_assumptions(db, company.id)
    periods = history["periods"]
    latest_metrics = periods[-1]["metrics"]
    expected_cagr = (
        latest_metrics["revenue"] / periods[0]["metrics"]["revenue"]
    ) ** (1 / (len(periods) - 1)) - 1
    assert draft["assumptions"]["starting_revenue"] == latest_metrics["revenue"]
    assert draft["assumptions"]["starting_invested_capital"] == latest_metrics[
        "invested_capital"
    ]
    assert draft["assumptions"]["current_operating_margin"] == pytest.approx(
        latest_metrics["ebit"] / latest_metrics["revenue"]
    )
    assert draft["assumptions"]["revenue_growth_years_json"]["1"] == pytest.approx(
        expected_cagr
    )
    assert draft["provenance"]["revenue_growth_years_json"]["history_years"] == [
        period["year"] for period in periods
    ]
