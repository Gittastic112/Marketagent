import math

import pytest
from pydantic import ValidationError

from app.services.relative_valuation import FinancialsInput, RelativeValuationRequest, RelativeValuationRunService
from test_relative_valuation_benchmarks import _add_source, _seed_pricing_sources


def request_body(**updates):
    return {"country": "India", "industryName": "Advertising", "financials": {"netIncome": 10, "dilutedShares": 2}, "methods": ["pe"], **updates}


@pytest.mark.parametrize("field", list(FinancialsInput.model_fields))
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), True])
def test_financial_inputs_reject_nonfinite_and_boolean_values(field, value):
    with pytest.raises(ValidationError):
        FinancialsInput(**{field: value})


@pytest.mark.parametrize("financials", [{"cash": -1}, {"debt": -1}, {"dilutedShares": 0}, {"dilutedShares": -1}, {"net_income": 1}])
def test_api_rejects_invalid_bridge_shares_and_unknown_financial_fields(client, financials):
    response = client.post("/api/valuation/relative/run", json=request_body(financials=financials))
    assert response.status_code == 422
    assert response.json()["data"] is None


def test_losses_zero_bridge_and_missing_inputs_remain_representable():
    financials = FinancialsInput(netIncome=-10, ebit=-2, ebitda=-1, bookEquity=-20, cash=0, debt=0)
    assert financials.netIncome == -10
    assert financials.dilutedShares is None


@pytest.mark.parametrize("updates", [
    {"methods": []}, {"methods": ["pe", "pe"]}, {"methods": ["pe"] * 7},
    {"methods": ["unknown"]}, {"country": " "}, {"industryName": " "},
    {"peerSetId": 1}, {"peerSetId": 0, "country": None, "industryName": None},
    {"peerSetId": True, "country": None, "industryName": None},
    {"companyId": "0"}, {"companyId": "1.5"}, {"companyId": "abc"},
    {"companyId": "2147483648"}, {"peerSetId": 2147483648},
    {"unexpectedInput": 10},
])
def test_relative_request_contract_rejects_ambiguous_or_malformed_requests(client, updates):
    response = client.post("/api/valuation/relative/run", json=request_body(**updates))
    assert response.status_code == 422


def test_relative_request_normalizes_source_selection():
    request = RelativeValuationRequest(**request_body(country=" India ", industryName=" Advertising ", companyId=" 12 "))
    assert (request.country, request.industryName, request.companyId) == ("India", "Advertising", "12")
    peer = RelativeValuationRequest(**request_body(country=None, industryName=None, peerSetId=4))
    assert peer.peerSetId == 4


@pytest.mark.parametrize("financials", [
    {"netIncome": 1e308, "dilutedShares": 1},
    {"netIncome": 10, "dilutedShares": 1e-308},
])
def test_overflow_is_reported_per_method_without_infinite_response(db_session, financials):
    _add_source(db_session, "pe", pe_current=10.0)
    result = RelativeValuationRunService.run_valuation(db_session, RelativeValuationRequest(**request_body(financials=financials)))
    assert result["relativeValues"] == []
    assert result["range"] is None
    assert "numeric range" in result["unavailableMethods"][0]["reason"]


def test_large_finite_method_prices_have_finite_mean(db_session):
    _seed_pricing_sources(db_session)
    result = RelativeValuationRunService.run_valuation(db_session, RelativeValuationRequest(**request_body(
        methods=["pe", "pbv"], financials={"netIncome": 1e307, "bookEquity": 5e307, "dilutedShares": 1},
    )))
    assert len(result["relativeValues"]) == 2
    assert math.isfinite(result["range"]["base"])
    assert result["range"]["base"] == pytest.approx(1e308)


def test_one_overflow_does_not_hide_other_valid_methods(client, db_session):
    _seed_pricing_sources(db_session)
    response = client.post("/api/valuation/relative/run", json=request_body(
        methods=["pe", "pbv"], financials={"netIncome": 1e308, "bookEquity": 5, "dilutedShares": 1},
    ))
    assert response.status_code == 200
    result = response.json()["data"]
    assert [value["methodId"] for value in result["relativeValues"]] == ["pbv"]
    assert result["range"]["base"] == 10
    assert result["unavailableMethods"][0]["method"] == "pe"


@pytest.mark.parametrize("number", ["1e400", "NaN", "-Infinity"])
def test_nonfinite_json_request_returns_serializable_validation_error(client, number):
    body = '{"country":"India","industryName":"Advertising","methods":["pe"],"financials":{"netIncome":' + number + '}}'
    response = client.post("/api/valuation/relative/run", content=body, headers={"content-type": "application/json"})
    assert response.status_code == 422
    assert response.json()["errors"][0]["code"] == "VALIDATION_ERROR"
    assert "input" not in response.json()["detail"][0]


def test_equity_bridge_overflow_keeps_other_methods_usable(db_session):
    _seed_pricing_sources(db_session)
    request = RelativeValuationRequest(**request_body(methods=["pe", "ev_ebitda"], financials={
        "netIncome": 1, "ebitda": 2e307, "cash": 1e308, "debt": 0, "dilutedShares": 1,
    }))
    result = RelativeValuationRunService.run_valuation(db_session, request)
    assert [row["methodId"] for row in result["relativeValues"]] == ["pe"]
    assert result["unavailableMethods"][0]["method"] == "ev_ebitda"
