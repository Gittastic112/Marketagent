import math

import pytest
from sqlalchemy import select

from app.models.company import Company
from app.models.dcf import DcfAssumptionSet, ValuationModel
from app.services.saved_relative_inputs import build_saved_relative_inputs
from test_relative_valuation_benchmarks import _seed_pricing_sources


def assumption(**overrides):
    return DcfAssumptionSet(id=7, valuation_model_id=3, starting_revenue=1000,
        current_operating_margin=0.2, cash=0, debt=0, diluted_shares=10,
        net_income=100, book_value_of_equity=500, cash_flow_currency="USD", **overrides)


def test_saved_mapping_preserves_zero_bridge_and_book_equity():
    result = build_saved_relative_inputs(assumption(), company_id=2)
    assert result["financials"] == {"revenue": 1000, "ebit": 200, "ebitda": None,
        "netIncome": 100, "bookEquity": 500, "investedCapital": None,
        "cash": 0, "debt": 0, "dilutedShares": 10}
    assert result["canCalculate"]
    assert result["assumptionSetId"] == 7
    assert result["fields"]["ebit"]["claimType"] == "Calculation"
    assert result["fields"]["bookEquity"]["sourceFields"] == ["book_value_of_equity"]


@pytest.mark.parametrize("depreciation", [None, 0, 40])
def test_depreciation_does_not_prove_complete_da_for_ebitda(depreciation):
    result = build_saved_relative_inputs(assumption(depreciation=depreciation), company_id=2)
    assert result["financials"]["ebitda"] is None
    assert "amortization" in result["fields"]["ebitda"]["reason"]


@pytest.mark.parametrize("field", ["starting_revenue", "current_operating_margin"])
def test_missing_ebit_operand_does_not_turn_into_zero(field):
    row = assumption()
    setattr(row, field, None)
    result = build_saved_relative_inputs(row, company_id=2)
    assert result["financials"]["ebit"] is None


@pytest.mark.parametrize("value", [0, -10])
def test_zero_and_loss_inputs_are_preserved(value):
    row = assumption()
    row.net_income = row.book_value_of_equity = value
    result = build_saved_relative_inputs(row, company_id=2)
    assert result["financials"]["netIncome"] == value
    assert result["financials"]["bookEquity"] == value


@pytest.mark.parametrize("field,value", [("cash", -1), ("debt", -1), ("diluted_shares", 0),
    ("current_operating_margin", 20), ("starting_revenue", math.inf), ("net_income", math.nan)])
def test_invalid_saved_values_are_readable_but_block_calculation(field, value):
    row = assumption()
    setattr(row, field, value)
    result = build_saved_relative_inputs(row, company_id=2)
    assert not result["canCalculate"]
    assert result["blockers"]
    assert all(value is None or math.isfinite(value) for value in result["financials"].values())


def test_stale_assumptions_block_calculation():
    result = build_saved_relative_inputs(assumption(is_stale=True), company_id=2)
    assert "Saved assumptions are marked stale; review and save current inputs." in result["blockers"]


@pytest.mark.parametrize("currency", [None, "", "US", "US12"])
def test_unknown_or_invalid_currency_is_not_guessed(currency):
    row = assumption()
    row.cash_flow_currency = currency
    result = build_saved_relative_inputs(row, company_id=2)
    assert result["currency"] is None
    assert not result["canCalculate"]


def test_input_basis_discloses_unmodeled_bridge_adjustments():
    result = build_saved_relative_inputs(assumption(minority_interests=20), company_id=2)
    assert any("minority_interests" in warning for warning in result["warnings"])
    assert result["fields"]["cash"]["claimType"] == "User Assumption"


def seed(db):
    company = Company(ticker="SAVEDINPUT", name="Saved input test")
    db.add(company)
    db.flush()
    model = ValuationModel(company_id=company.id, name="Saved test")
    db.add(model)
    db.flush()
    row = assumption()
    row.id = None
    row.valuation_model_id = model.id
    db.add(row)
    db.commit()
    return company, model, row


def basis_hash(row):
    return build_saved_relative_inputs(row, company_id=row.valuation_model.company_id)["inputBasisSha256"]


def test_owned_read_is_nonmutating_and_source_linked(client, db_session):
    company, model, row = seed(db_session)
    response = client.get(f"/api/valuation/relative/assumptions/{row.id}/inputs")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["companyId"] == company.id
    assert body["data"]["modelId"] == model.id
    assert body["meta"]["source"] == "saved_dcf_user_assumptions"
    assert len(db_session.scalars(select(DcfAssumptionSet)).all()) == 1


def test_other_owner_and_missing_assumptions_return_same_404(client, db_session):
    _, model, row = seed(db_session)
    model.user_id = "another-owner"
    db_session.commit()
    for assumption_id in [row.id, 999999]:
        assert client.get(f"/api/valuation/relative/assumptions/{assumption_id}/inputs").status_code == 404
        assert client.post(f"/api/valuation/relative/assumptions/{assumption_id}/run",
            json={"country": "India", "industryName": "Advertising", "methods": ["pe"], "confirmInputBasis": True, "inputBasisSha256": "0" * 64}).status_code == 404


def test_saved_run_uses_server_financials_and_preserves_basis(client, db_session):
    _seed_pricing_sources(db_session)
    _, _, row = seed(db_session)
    response = client.post(f"/api/valuation/relative/assumptions/{row.id}/run", json={
        "country": "India", "industryName": "Advertising", "methods": ["pe", "pbv", "ev_ebitda"], "confirmInputBasis": True, "inputBasisSha256": basis_hash(row)})
    assert response.status_code == 200
    result = response.json()["data"]
    assert result["inputBasis"]["financials"]["cash"] == 0
    assert {value["methodId"] for value in result["relativeValues"]} == {"pe", "pbv"}
    assert result["unavailableMethods"][0]["method"] == "ev_ebitda"


@pytest.mark.parametrize("extra", [{"financials": {"netIncome": 999}}, {"companyId": "999"},
    {"confirmInputBasis": False}, {"confirmInputBasis": "true"}])
def test_saved_run_rejects_overrides_and_requires_basis_confirmation(client, db_session, extra):
    _, _, row = seed(db_session)
    response = client.post(f"/api/valuation/relative/assumptions/{row.id}/run", json={
        "country": "India", "industryName": "Advertising", "methods": ["pe"], "confirmInputBasis": True, "inputBasisSha256": basis_hash(row), **extra})
    assert response.status_code == 422


def test_run_rechecks_stale_state_after_input_preview(client, db_session):
    _, _, row = seed(db_session)
    assert client.get(f"/api/valuation/relative/assumptions/{row.id}/inputs").json()["data"]["canCalculate"]
    row.is_stale = True
    db_session.commit()
    response = client.post(f"/api/valuation/relative/assumptions/{row.id}/run", json={
        "country": "India", "industryName": "Advertising", "methods": ["pe"], "confirmInputBasis": True, "inputBasisSha256": basis_hash(row)})
    assert response.status_code == 422


def test_preview_hash_rejects_changed_saved_inputs(client, db_session):
    _, _, row = seed(db_session)
    original = basis_hash(row)
    row.net_income = 200
    db_session.commit()
    response = client.post(f"/api/valuation/relative/assumptions/{row.id}/run", json={
        "country": "India", "industryName": "Advertising", "methods": ["pe"],
        "confirmInputBasis": True, "inputBasisSha256": original})
    assert response.status_code == 409


def test_method_input_coverage_separates_base_bridge_and_shares():
    row = assumption()
    row.cash = None
    result = build_saved_relative_inputs(row, company_id=2)
    methods = {item["method"]: item for item in result["methodInputs"]}
    assert methods["pe"]["hasPerShareInputs"]
    assert methods["ev_sales"]["hasPositiveBase"]
    assert not methods["ev_sales"]["hasPerShareInputs"]
    assert not methods["ev_ebitda"]["hasPositiveBase"]
    row.diluted_shares = None
    assert not any(item["hasPerShareInputs"] for item in build_saved_relative_inputs(row, company_id=2)["methodInputs"])


def test_no_positive_company_base_blocks_empty_calculations():
    row = DcfAssumptionSet(cash_flow_currency="USD")
    result = build_saved_relative_inputs(row, company_id=2)
    assert not result["canCalculate"]
    assert any("No method" in reason for reason in result["blockers"])


@pytest.mark.parametrize("identifier", ["0", "-1", "2147483648", "abc"])
def test_input_route_rejects_invalid_identifiers(client, identifier):
    assert client.get(f"/api/valuation/relative/assumptions/{identifier}/inputs").status_code == 422


def test_input_hash_changes_with_currency_zero_and_stale_state():
    row = assumption()
    previous = build_saved_relative_inputs(row, company_id=2)["inputBasisSha256"]
    for field, value in [("cash", None), ("cash_flow_currency", "INR"), ("is_stale", True)]:
        setattr(row, field, value)
        current = build_saved_relative_inputs(row, company_id=2)["inputBasisSha256"]
        assert current != previous
        previous = current
