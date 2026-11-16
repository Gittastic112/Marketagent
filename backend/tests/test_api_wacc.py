from helpers import response_data, response_errors
import pytest


def _payload(**overrides) -> dict:
    payload = {
        "risk_free_rate": 0.03,
        "beta": 1.1,
        "mature_erp": 0.05,
        "interest_coverage_ratio": 6.25,
        "marginal_tax_rate": 0.25,
        "market_equity": 800.0,
        "total_debt": 200.0,
        "terminal_wacc": 0.08,
    }
    payload.update(overrides)
    return payload


def test_wacc_api_returns_source_backed_rating_provenance(client) -> None:
    response = client.post(
        "/api/valuation/wacc/calculate",
        json=_payload(firm_type="small_or_risky"),
    )

    assert response.status_code == 200
    result = response_data(response)
    assert result["synthetic_rating"] == "A2/A"
    assert result["default_spread"] == 0.0078
    assert result["synthetic_rating_details"] == {
        "interest_coverage_ratio": 6.25,
        "firm_type": "small_or_risky",
        "rating": "A2/A",
        "default_spread": 0.0078,
        "band_lower_bound": 6.0,
        "band_upper_bound": 7.499999,
        "claim_type": "Calculation",
        "catalog_version": "ratings-xls-45d1f61c67f0",
    }
    provenance = result["synthetic_rating_provenance"]
    assert provenance["source_filename"] == "ratings.xls"
    assert provenance["canonical_path"] == "raw/models/ratings.xls"
    assert provenance["source_as_of"] == "unknown"
    assert provenance["date_confidence"] == "low"
    assert provenance["recency_claim_type"] == "User Assumption"
    assert response.json()["meta"]["confidence"] == "low"
    assert "unknown" in " ".join(response.json()["meta"]["warnings"]).lower()


def test_wacc_api_supports_financial_firm_rating_table(client) -> None:
    result = response_data(client.post(
        "/api/valuation/wacc/calculate",
        json=_payload(interest_coverage_ratio=3.0, firm_type="financial_service"),
    ))

    assert result["synthetic_rating"] == "Aaa/AAA"
    assert result["default_spread"] == 0.004
    assert result["synthetic_rating_details"]["firm_type"] == "financial_service"


def test_wacc_api_preserves_legacy_large_manufacturer_boolean(client) -> None:
    legacy_large = response_data(client.post(
        "/api/valuation/wacc/calculate",
        json=_payload(interest_coverage_ratio=3.5, is_large_mfg=True),
    ))
    legacy_small = response_data(client.post(
        "/api/valuation/wacc/calculate",
        json=_payload(interest_coverage_ratio=3.5, is_large_mfg=False),
    ))

    assert legacy_large["synthetic_rating_details"]["firm_type"] == "large_non_financial"
    assert legacy_small["synthetic_rating_details"]["firm_type"] == "small_or_risky"


def test_wacc_api_rejects_conflicting_firm_type_inputs(client) -> None:
    response = client.post(
        "/api/valuation/wacc/calculate",
        json=_payload(firm_type="financial_service", is_large_mfg=True),
    )

    assert response.status_code == 422
    assert response_errors(response)[0]["code"] == "VALIDATION_ERROR"
    assert "conflict" in response.text.lower()


@pytest.mark.parametrize("overrides", [
    {"risk_free_rate": 4}, {"mature_erp": 5}, {"country_risk_premium": -1},
    {"marginal_tax_rate": 25}, {"terminal_wacc": 8}, {"beta": -1}, {"lambda_crp": -1},
    {"market_equity": -1}, {"total_debt": -1}, {"market_equity": 0, "total_debt": 0},
    {"market_equity": 1e308, "total_debt": 1e308},
    {"total_years": 0}, {"total_years": 31}, {"years_to_fade": -1}, {"years_to_fade": 11},
])
def test_wacc_rejects_invalid_units_capital_and_horizons(client, overrides):
    response = client.post("/api/valuation/wacc/calculate", json=_payload(**overrides))
    assert response.status_code == 422, response.text


def test_negative_coverage_and_zero_debt_remain_valid(client):
    response = client.post("/api/valuation/wacc/calculate", json=_payload(
        interest_coverage_ratio=-2, total_debt=0, years_to_fade=0))
    assert response.status_code == 200, response.text
    assert response.json()["data"]["equity_weight"] == 1
    assert len(set(response.json()["data"]["wacc_array"])) == 1
