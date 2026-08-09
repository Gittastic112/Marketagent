from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.dcf import DcfAssumptionSet, DcfOutput, ValuationModel
from helpers import response_data, response_errors


def _company(client: TestClient) -> dict:
    return response_data(client.post("/companies", json={
        "ticker": "QUICK",
        "name": "Quick Valuation Test",
        "market": "US",
        "country": "United States",
        "currency": "USD",
    }))


def _valid_payload(company_id: int) -> dict:
    return {
        "company_id": company_id,
        "projection_years_count": 10,
        "starting_revenue": 1_000.0,
        "revenue_growth_years_json": {
            str(year): 0.08 if year <= 5 else 0.04 for year in range(1, 11)
        },
        "current_operating_margin": 0.15,
        "target_operating_margin": 0.18,
        "tax_rate": 0.21,
        "sales_to_capital_ratio": 1.5,
        "starting_invested_capital": 650.0,
        "wacc_start": 0.10,
        "wacc_terminal": 0.085,
        "terminal_growth_rate": 0.025,
        "terminal_roic": 0.10,
        "cash": 100.0,
        "debt": 50.0,
        "minority_interests": 10.0,
        "preferred_stock": 0.0,
        "employee_options_value": 5.0,
        "diluted_shares": 100.0,
        "current_market_price": 12.0,
    }


def test_quick_valuation_generates_reviewable_baseline(client: TestClient) -> None:
    company = _company(client)

    result = response_data(client.post(
        "/api/valuation/quick/assumptions",
        json={"company_id": company["id"]},
    ))

    assert result["company_id"] == company["id"]
    assert result["assumptions"]["scenario"] == "Base"
    assert result["provenance"]["starting_revenue"]["is_placeholder"] is True
    assert result["source_metadata"]["requires_review"] is True
    assert any("Manual entry required" in warning for warning in result["warnings"])


def test_quick_valuation_calculates_without_persisting_models(
    client: TestClient,
    db_session: Session,
) -> None:
    company = _company(client)

    result = response_data(client.post(
        "/api/valuation/quick/calculate",
        json=_valid_payload(company["id"]),
    ))

    assert result["company_id"] == company["id"]
    assert result["currency"] == "USD"
    assert result["claim_type"] == "Calculation"
    assert result["is_persisted"] is False
    assert result["enterprise_value"] > 0
    assert result["intrinsic_value_per_share"] > 0
    assert len(result["projection_years"]) == 10
    assert "not persisted" in " ".join(result["limitations"]).lower()
    assert db_session.query(ValuationModel).count() == 0
    assert db_session.query(DcfAssumptionSet).count() == 0
    assert db_session.query(DcfOutput).count() == 0


def test_quick_valuation_rejects_unsafe_or_malformed_inputs(client: TestClient) -> None:
    company = _company(client)
    payload = _valid_payload(company["id"])
    payload["terminal_growth_rate"] = payload["wacc_terminal"]
    invalid_terminal = client.post("/api/valuation/quick/calculate", json=payload)

    payload = _valid_payload(company["id"])
    payload["diluted_shares"] = 0
    invalid_shares = client.post("/api/valuation/quick/calculate", json=payload)

    payload = _valid_payload(company["id"])
    payload["revenue_growth_years_json"] = {"year-one": 0.1}
    invalid_growth = client.post("/api/valuation/quick/calculate", json=payload)

    assert invalid_terminal.status_code == 422
    assert invalid_shares.status_code == 422
    assert invalid_growth.status_code == 422
    assert response_errors(invalid_terminal)[0]["code"] == "VALIDATION_ERROR"


def test_quick_valuation_returns_stable_company_not_found_error(client: TestClient) -> None:
    baseline = client.post(
        "/api/valuation/quick/assumptions",
        json={"company_id": 999_999},
    )
    calculate = client.post(
        "/api/valuation/quick/calculate",
        json=_valid_payload(999_999),
    )

    assert baseline.status_code == 404
    assert calculate.status_code == 404
    assert response_errors(baseline)[0]["code"] == "QUICK_VALUATION_COMPANY_NOT_FOUND"
    assert response_errors(calculate)[0]["code"] == "QUICK_VALUATION_COMPANY_NOT_FOUND"
