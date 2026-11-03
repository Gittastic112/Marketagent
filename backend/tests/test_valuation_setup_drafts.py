from datetime import date

import pytest

from app.models import (
    Company,
    DamodaranDatasetFile,
    DamodaranMarginBenchmark,
    DcfAssumptionSet,
    FinancialMetric,
    FinancialStatementPeriod,
    NormalizedFinancialMetric,
    NormalizedFinancialSnapshot,
    User,
    ValuationModel,
    ValuationSetupDraft,
)
from helpers import response_data


@pytest.mark.parametrize("patch", [{}, {"cash": 25}])
def test_partial_save_and_review_preserve_scenario_projection_and_reinvestment(client, db, patch):
    company, _ = _company_with_actuals(db)
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    chosen = {"scenario": "Reviewed stationary reference", "projection_years_count": 7,
              "reinvestment_method": "roic"}
    saved = response_data(client.patch(f"/valuation-drafts/{draft['id']}", json={
        "assumptions_patch": chosen, "reviewed_fields": []}))
    reviewed = response_data(client.patch(f"/valuation-drafts/{draft['id']}", json={
        "assumptions_patch": patch, "reviewed_fields": ["projection_years_count"],
        "expected_updated_at": saved["updated_at"]}))
    for field, value in chosen.items():
        assert reviewed["assumptions_json"][field] == value
    assert reviewed["reviewed_fields_json"] == ["projection_years_count"]


def test_review_requirements_follow_the_selected_model(client, db):
    company, _ = _company_with_actuals(db)
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    metadata = draft["source_metadata_json"]
    bank = metadata["review_fields_by_model"]["financial_services"]
    assert {"book_value_of_equity", "net_income", "target_roe", "cost_of_equity"} <= set(bank)
    assert not {"starting_revenue", "revenue_growth_years_json", "debt", "wacc_start"} & set(bank)
    assert {"probability_of_failure", "distress_sale_proceeds"} <= set(metadata["review_fields_by_model"]["distressed"])


def test_direct_discount_rates_allow_reviewed_missing_components_but_not_missing_claims(client, db):
    company, _ = _company_with_actuals(db)
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    fields = sorted(set(draft["source_metadata_json"]["review_fields"]) | {
        "risk_free_rate", "beta", "equity_risk_premium", "cost_of_equity",
        "pre_tax_cost_of_debt", "debt_to_capital", "equity_to_capital"})
    components = {"risk_free_rate", "beta", "equity_risk_premium", "cost_of_equity",
                  "pre_tax_cost_of_debt", "debt_to_capital", "equity_to_capital"}
    patch = {field: _valid_review_value(field) for field in fields}
    patch.update({field: None for field in components})
    patch.update(wacc_start=.14, wacc_terminal=.14, terminal_growth_rate=0,
                 diluted_shares=100, employee_options_value=0,
                 risk_story="Mock Data: explicit 14% discount-rate assumption; funding decomposition unavailable.")
    saved = response_data(client.patch(f"/valuation-drafts/{draft['id']}", json={
        "assumptions_patch": patch, "reviewed_fields": [field for field in fields if field != "beta"]}))
    assert "beta" in saved["source_metadata_json"]["unresolved_fields"]
    command = {"name": "Mock Data explicit discount rates", "model_type": "fcff_dcf"}
    assert client.post(f"/valuation-drafts/{draft['id']}/promote", json=command).status_code == 409
    for missing in ("wacc_start", "wacc_terminal", "diluted_shares", "employee_options_value"):
        saved = response_data(client.patch(f"/valuation-drafts/{draft['id']}", json={
            "assumptions_patch": {**patch, missing: None}, "reviewed_fields": fields}))
        assert missing in saved["source_metadata_json"]["unresolved_fields"]
        assert client.post(f"/valuation-drafts/{draft['id']}/promote", json=command).status_code == 409
    saved = response_data(client.patch(f"/valuation-drafts/{draft['id']}", json={
        "assumptions_patch": patch, "reviewed_fields": fields}))
    assert saved["source_metadata_json"]["promotion_ready"] is True
    model = response_data(client.post(f"/valuation-drafts/{draft['id']}/promote", json=command))
    assumptions = response_data(client.get(f"/valuation-models/{model['id']}/assumptions"))[0]
    assert assumptions["wacc_start"] == .14
    assert assumptions["beta"] is None
    assert assumptions["cost_of_equity"] is None
    assert assumptions["outputs"]["intrinsic_value_per_share"] is not None


def test_clearing_sourced_financing_component_requires_new_unavailable_review(client, db):
    company, _ = _company_with_actuals(db)
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    stored = db.get(ValuationSetupDraft, draft["id"])
    stored.source_metadata_json = {**stored.source_metadata_json,
        "review_fields": [f for f in stored.source_metadata_json["review_fields"] if f != "beta"]}
    db.commit()
    saved = response_data(client.patch(f"/valuation-drafts/{draft['id']}", json={
        "assumptions_patch": {"beta": None, "wacc_start": .14, "wacc_terminal": .14},
        "reviewed_fields": []}))
    assert "beta" in saved["source_metadata_json"]["review_fields"]
    assert "beta" in saved["source_metadata_json"]["unresolved_fields"]


def test_omitted_legacy_funding_keys_need_review_and_can_be_added_and_reviewed(client, db):
    from app.services.assumption_provenance import DISCOUNT_COMPONENT_FIELDS
    from app.services.valuation_setup_draft import ValuationSetupDraftService

    company, _ = _company_with_actuals(db)
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    stored = db.get(ValuationSetupDraft, draft["id"])
    stored.assumptions_json = {**{k: v for k, v in stored.assumptions_json.items()
        if k not in DISCOUNT_COMPONENT_FIELDS}, "wacc_start": .14, "wacc_terminal": .14}
    stored.source_metadata_json = {**stored.source_metadata_json, "review_fields": []}
    stored.reviewed_fields_json = []
    db.commit()
    assert DISCOUNT_COMPONENT_FIELDS <= set(ValuationSetupDraftService._unresolved_fields(stored))
    ValuationSetupDraftService._update_status(stored)
    assert DISCOUNT_COMPONENT_FIELDS <= set(stored.source_metadata_json["review_fields"])
    db.commit()
    saved = response_data(client.patch(f"/valuation-drafts/{draft['id']}", json={
        "assumptions_patch": {field: None for field in DISCOUNT_COMPONENT_FIELDS},
        "reviewed_fields": sorted(DISCOUNT_COMPONENT_FIELDS)}))
    assert not DISCOUNT_COMPONENT_FIELDS & set(saved["source_metadata_json"]["unresolved_fields"])


@pytest.mark.parametrize("model_type", ["fcff_dcf", "distressed", "financial_services"])
def test_missing_comparison_price_requires_explicit_review_but_allows_valuation(client, db, model_type):
    company, _ = _company_with_actuals(db)
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    assert draft["assumptions_json"]["current_market_price"] is None
    assert "current_market_price" not in draft["source_metadata_json"]["required_fields_by_model"][model_type]
    reviewed = draft["source_metadata_json"]["review_fields_by_model"][model_type]
    assert "current_market_price" in reviewed
    patch = {field: _valid_review_value(field) for field in reviewed}
    patch.update(current_market_price=None, projection_years_count=10,
                 cash_flow_currency="INR", discount_rate_currency="INR",
                 book_value_of_equity=1000, net_income=100, target_roe=0.12,
                 cost_of_equity=0.10, terminal_growth_rate=0.02,
                 probability_of_failure=0.1, distress_sale_proceeds=10)
    response_data(client.patch(f"/valuation-drafts/{draft['id']}", json={
        "assumptions_patch": patch,
        "reviewed_fields": [field for field in reviewed if field != "current_market_price"]}))
    command = {"name": "Mock Data valuation without comparison price", "model_type": model_type}
    blocked = client.post(f"/valuation-drafts/{draft['id']}/promote", json=command)
    assert blocked.status_code == 409
    assert "current_market_price" in blocked.json()["detail"]
    assert db.query(ValuationModel).filter_by(company_id=company.id).count() == 0
    response_data(client.patch(f"/valuation-drafts/{draft['id']}", json={
        "assumptions_patch": {}, "reviewed_fields": reviewed}))
    model = response_data(client.post(f"/valuation-drafts/{draft['id']}/promote", json=command))
    saved = response_data(client.get(f"/valuation-models/{model['id']}/assumptions"))[0]
    assert saved["current_market_price"] is None
    assert saved["outputs"]["intrinsic_value_per_share"] > 0
    assert saved["outputs"]["current_market_price"] is None
    assert saved["outputs"]["upside_downside_pct"] is None


@pytest.mark.parametrize("missing", [None, "book_value_of_equity", "net_income", "target_roe"])
@pytest.mark.parametrize("unused_value", [None, 0.0])
def test_bank_draft_requires_equity_basis_without_invented_operating_inputs(client, db, missing, unused_value):
    company, _ = _company_with_actuals(db)
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    equity_inputs = {"projection_years_count": 10, "book_value_of_equity": 100_000_000,
        "net_income": 10_000_000, "target_roe": 0.12, "cost_of_equity": 0.10,
        "terminal_growth_rate": 0.03, "diluted_shares": 10_000_000,
        "cash_flow_currency": "INR", "discount_rate_currency": "INR", "current_market_price": 10}
    if missing:
        equity_inputs[missing] = None
    unused = {"starting_revenue": None, "revenue_growth_years_json": None,
        "current_operating_margin": None, "target_operating_margin": None,
        "sales_to_capital_ratio": None, "starting_invested_capital": None,
        "wacc_start": None, "wacc_terminal": None}
    unused.update(starting_revenue=unused_value, starting_invested_capital=unused_value,
                  sales_to_capital_ratio=unused_value)
    response_data(client.patch(f"/valuation-drafts/{draft['id']}", json={
        "assumptions_patch": {**equity_inputs, **unused}, "reviewed_fields": list(equity_inputs)}))
    response = client.post(f"/valuation-drafts/{draft['id']}/promote", json={
        "name": "Mock Data equity-input bank model", "model_type": "financial_services"})
    if missing:
        assert response.status_code == 409
        assert missing in response.json()["detail"]
        assert db.query(ValuationModel).filter_by(company_id=company.id).count() == 0
    else:
        model = response_data(response)
        assumptions = response_data(client.get(f"/valuation-models/{model['id']}/assumptions"))
        assert assumptions[0]["starting_revenue"] is None
        assert assumptions[0]["starting_invested_capital"] is None
        assert assumptions[0]["sales_to_capital_ratio"] is None
        db.expire_all()
        retained = db.get(ValuationSetupDraft, draft["id"])
        assert retained.assumptions_json["starting_revenue"] == unused_value
        assert retained.assumptions_json["starting_invested_capital"] == unused_value
        assert retained.source_metadata_json["promotion_excluded_fields"] == [
            "starting_revenue", "starting_invested_capital", "sales_to_capital_ratio"]
        assert assumptions[0]["outputs"]["intrinsic_value_per_share"] > 0
        assert assumptions[0]["outputs"]["enterprise_value"] is None


@pytest.mark.parametrize("change", ["review_policy", "financials", "industry", "currency"])
def test_promotion_rejects_changed_source_basis(client, db, change):
    company, snapshot = _company_with_actuals(db)
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    reviewed = draft["source_metadata_json"]["review_fields"]
    response_data(client.patch(f"/valuation-drafts/{draft['id']}", json={
        "assumptions_patch": {field: _valid_review_value(field) for field in reviewed},
        "reviewed_fields": reviewed,
    }))
    stored = db.get(ValuationSetupDraft, draft["id"])
    if change == "review_policy":
        stored.source_metadata_json = {**stored.source_metadata_json,
            "source_input_signature": "legacy-review-policy"}
    elif change == "financials":
        db.query(NormalizedFinancialMetric).filter_by(snapshot_id=snapshot.id,
            metric_code="revenue").one().value = 1100
    elif change == "industry":
        company.damodaran_industry = "Retail (General)"
    else:
        company.currency = "USD"
    db.commit()

    response = client.post(f"/valuation-drafts/{draft['id']}/promote", json={
        "name": "Mock Data stale draft", "model_type": "fcff_dcf"})
    assert response.status_code == 409
    assert "Refresh" in response.json()["detail"]
    assert db.query(ValuationModel).filter_by(company_id=company.id).count() == 0
    assert db.get(ValuationSetupDraft, draft["id"]).promoted_model_id is None


@pytest.mark.parametrize("change", ["benchmark", "freshness"])
def test_promotion_rechecks_generated_basis_without_overwriting_draft(client, db, monkeypatch, change):
    from app.services import assumption_provenance
    from app.services.valuation_setup_draft import ValuationSetupDraftService

    company, _ = _company_with_actuals(db)
    dataset = DamodaranDatasetFile(uploaded_filename="Mock Data margins.xls",
        dataset_code="margin", country="India", source_file_type="xls")
    db.add(dataset)
    db.flush()
    margin = DamodaranMarginBenchmark(dataset_file_id=dataset.id,
        industry_name=company.damodaran_industry, country="India", ebit_margin=0.20)
    db.add(margin)
    db.commit()
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    reviewed = draft["source_metadata_json"]["review_fields"]
    patch = {field: _valid_review_value(field) for field in reviewed
        if not ValuationSetupDraftService._valid_value(field, draft["assumptions_json"].get(field))}
    saved = response_data(client.patch(f"/valuation-drafts/{draft['id']}", json={
        "assumptions_patch": patch, "reviewed_fields": reviewed}))
    if change == "benchmark":
        margin.ebit_margin = 0.15
        db.commit()
    else:
        class FutureDate(date):
            @classmethod
            def today(cls):
                return cls(2030, 1, 1)
        monkeypatch.setattr(assumption_provenance, "date", FutureDate)

    response = client.post(f"/valuation-drafts/{draft['id']}/promote", json={
        "name": "Mock Data changed source", "model_type": "fcff_dcf"})
    assert response.status_code == 409
    assert "Refresh" in response.json()["detail"]
    db.expire_all()
    stored = db.get(ValuationSetupDraft, draft["id"])
    assert stored.assumptions_json == saved["assumptions_json"]
    assert stored.reviewed_fields_json == saved["reviewed_fields_json"]
    assert db.query(ValuationModel).filter_by(company_id=company.id).count() == 0


def test_legacy_growth_review_is_invalidated_without_losing_user_edits(client, db):
    company, _ = _company_with_actuals(db)
    older = FinancialStatementPeriod(company_id=company.id, year=2025,
        period_type="annual", report_date=date(2025, 3, 31), currency="INR")
    db.add(older)
    db.flush()
    db.add(FinancialMetric(period_id=older.id, metric_name="revenue", value=800, unit="INR million"))
    db.commit()
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    response_data(client.patch(f"/valuation-drafts/{draft['id']}", json={
        "assumptions_patch": {"starting_revenue": 1250},
        "reviewed_fields": ["starting_revenue", "revenue_growth_years_json"],
    }))
    stored = db.get(ValuationSetupDraft, draft["id"])
    stored.source_metadata_json = {**stored.source_metadata_json,
        "source_input_signature": "legacy-review-policy"}
    old_growth = {**stored.provenance_json["revenue_growth_years_json"],
        "claim_type": "Calculation", "requires_review": False}
    stored.provenance_json = {**stored.provenance_json, "revenue_growth_years_json": old_growth}
    db.commit()

    reopened = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    assert reopened["id"] == draft["id"]
    assert reopened["assumptions_json"]["starting_revenue"] == 1250
    assert "starting_revenue" in reopened["reviewed_fields_json"]
    assert "revenue_growth_years_json" not in reopened["reviewed_fields_json"]
    assert "revenue_growth_years_json" in reopened["source_metadata_json"]["unresolved_fields"]
    assert reopened["provenance_json"]["revenue_growth_years_json"]["claim_type"] == "Estimate"


def test_new_unit_policy_preserves_manual_values_but_requires_scale_review(client, db):
    company, _ = _company_with_actuals(db)
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    response_data(client.patch(f"/valuation-drafts/{draft['id']}", json={
        "assumptions_patch": {"starting_revenue": 1250}, "reviewed_fields": ["starting_revenue"]}))
    stored = db.get(ValuationSetupDraft, draft["id"])
    stored.source_metadata_json = {key: value for key, value in stored.source_metadata_json.items()
        if key != "input_unit_policy"}
    stored.source_metadata_json = {**stored.source_metadata_json, "source_input_signature": "legacy-unit-policy"}
    db.commit()
    reopened = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    assert reopened["assumptions_json"]["starting_revenue"] == 1250
    assert "starting_revenue" not in reopened["reviewed_fields_json"]
    assert "starting_revenue" in reopened["source_metadata_json"]["unresolved_fields"]
    assert reopened["provenance_json"]["starting_revenue"]["unit_policy_review_required"] is True
    assert any("Manual values need review" in warning for warning in reopened["warnings_json"])


def _valid_review_value(field: str):
    if field == "revenue_growth_years_json":
        return {str(year): 0.05 for year in range(1, 11)}
    if field in {"starting_revenue", "starting_invested_capital", "diluted_shares", "current_market_price"}:
        return 100
    if field == "beta":
        return 1
    if field == "debt_to_capital":
        return 0.2
    if field == "equity_to_capital":
        return 0.8
    if field in {
        "current_operating_margin",
        "target_operating_margin",
        "tax_rate",
        "risk_free_rate",
        "equity_risk_premium",
        "cost_of_equity",
        "pre_tax_cost_of_debt",
        "wacc_start",
        "wacc_terminal",
        "terminal_growth_rate",
        "terminal_roic",
    }:
        return 0.1
    if field == "sales_to_capital_ratio":
        return 2
    return 0


def _company_with_actuals(db) -> tuple[Company, NormalizedFinancialSnapshot]:
    company = Company(
        ticker="DRAFT",
        name="Draft Workflow Co",
        market="IN",
        primary_exchange="NSE",
        local_symbol="DRAFT",
        country="India",
        currency="INR",
        damodaran_industry="Software (Internet)",
    )
    db.add(company)
    db.flush()
    period = FinancialStatementPeriod(
        company_id=company.id,
        period_type="annual",
        year=2026,
        report_date=date(2026, 3, 31),
        currency="INR",
    )
    db.add(period)
    db.flush()
    db.add_all(
        [
            FinancialMetric(period_id=period.id, metric_name="cash", value=100, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="debt", value=250, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="diluted_shares", value=50, unit="million shares"),
        ]
    )
    snapshot = NormalizedFinancialSnapshot(company_id=company.id, period_id=period.id)
    db.add(snapshot)
    db.flush()
    db.add_all(
        [
            NormalizedFinancialMetric(snapshot_id=snapshot.id, metric_code="revenue", value=1000, unit="INR million"),
            NormalizedFinancialMetric(snapshot_id=snapshot.id, metric_code="ebit", value=200, unit="INR million"),
            NormalizedFinancialMetric(snapshot_id=snapshot.id, metric_code="invested_capital", value=500, unit="INR million"),
        ]
    )
    db.commit()
    return company, snapshot


def test_create_and_reopen_owned_valuation_setup_draft(client, db) -> None:
    company, _ = _company_with_actuals(db)

    created_response = client.post(f"/companies/{company.id}/valuation-drafts", json={})

    assert created_response.status_code == 201
    created = response_data(created_response)
    assert created["company_id"] == company.id
    assert created["status"] == "draft"
    assert created["assumptions_json"]["starting_revenue"] == 1_000_000_000
    assert created["provenance_json"]["starting_revenue"]["source_table"] == "normalized_financial_metrics"
    assert created["assumptions_json"]["basic_shares"] is None
    assert "basic_shares" not in created["source_metadata_json"]["review_fields"]
    assert created["reviewed_fields_json"] == []
    assert created["source_metadata_json"]["financial_history_signature"]

    reopened = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    assert reopened["id"] == created["id"]


def test_reopen_refreshes_changed_financial_history_without_losing_user_edits(client, db) -> None:
    company, snapshot = _company_with_actuals(db)
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    saved = response_data(
        client.patch(
            f"/valuation-drafts/{draft['id']}",
            json={
                "assumptions_patch": {"starting_revenue": 1250},
                "reviewed_fields": ["starting_revenue"],
            },
        )
    )
    old_signature = saved["source_metadata_json"]["financial_history_signature"]
    ebit = db.query(NormalizedFinancialMetric).filter_by(snapshot_id=snapshot.id, metric_code="ebit").one()
    ebit.value = 250
    db.commit()

    reopened = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))

    assert reopened["id"] == draft["id"]
    assert reopened["assumptions_json"]["starting_revenue"] == 1250
    assert "starting_revenue" in reopened["reviewed_fields_json"]
    assert reopened["assumptions_json"]["current_operating_margin"] == 0.25
    assert reopened["source_metadata_json"]["financial_history_signature"] != old_signature


def test_draft_refresh_preserves_user_edits_and_updates_unreviewed_priors(client, db) -> None:
    company, _ = _company_with_actuals(db)
    dataset = DamodaranDatasetFile(
        uploaded_filename="marginIndia.xls",
        dataset_code="margin",
        country="India",
        source_file_type="xls",
    )
    db.add(dataset)
    db.flush()
    db.add_all(
        [
            DamodaranMarginBenchmark(
                dataset_file_id=dataset.id,
                industry_name="Software (Internet)",
                country="India",
                number_of_firms=10,
                ebit_margin=0.20,
            ),
            DamodaranMarginBenchmark(
                dataset_file_id=dataset.id,
                industry_name="Retail (General)",
                country="India",
                number_of_firms=12,
                ebit_margin=0.08,
            ),
        ]
    )
    db.commit()
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))

    persisted_draft = db.get(ValuationSetupDraft, draft["id"])
    persisted_draft.source_metadata_json = {
        **(persisted_draft.source_metadata_json or {}),
        "valuation_cutoff_date": "2026-08-01",
        "latest_statutory_financial_source": "https://example.test/statutory-filing",
    }
    db.commit()

    saved = response_data(
        client.patch(
            f"/valuation-drafts/{draft['id']}",
            json={
                "assumptions_patch": {"starting_revenue": 1250},
                "reviewed_fields": ["starting_revenue"],
            },
        )
    )
    assert saved["assumptions_json"]["starting_revenue"] == 1250
    assert saved["provenance_json"]["starting_revenue"]["source_type"] == "user_input"

    company.damodaran_industry = "Retail (General)"
    db.commit()
    refreshed = response_data(client.post(f"/valuation-drafts/{draft['id']}/refresh", json={}))

    assert refreshed["industry_name"] == "Retail (General)"
    assert refreshed["assumptions_json"]["starting_revenue"] == 1250
    assert "starting_revenue" in refreshed["reviewed_fields_json"]
    assert refreshed["assumptions_json"]["target_operating_margin"] == 0.08
    assert refreshed["provenance_json"]["target_operating_margin"]["industry"] == "Retail (General)"
    assert refreshed["source_metadata_json"]["valuation_cutoff_date"] == "2026-08-01"
    assert (
        refreshed["source_metadata_json"]["latest_statutory_financial_source"]
        == "https://example.test/statutory-filing"
    )


def test_draft_refresh_invalidates_review_when_source_value_changes(client, db) -> None:
    company, snapshot = _company_with_actuals(db)
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    source_field = "starting_revenue"
    reviewed = response_data(
        client.patch(
            f"/valuation-drafts/{draft['id']}",
            json={"assumptions_patch": {}, "reviewed_fields": [source_field]},
        )
    )
    assert source_field in reviewed["reviewed_fields_json"]

    revenue = db.query(NormalizedFinancialMetric).filter_by(snapshot_id=snapshot.id, metric_code="revenue").one()
    revenue.value = 1100
    db.commit()

    refreshed = response_data(client.post(f"/valuation-drafts/{draft['id']}/refresh", json={}))
    assert refreshed["assumptions_json"][source_field] == 1_100_000_000
    assert source_field not in refreshed["reviewed_fields_json"]


def test_draft_is_not_visible_to_another_user(client, db) -> None:
    from app.api.dependencies import get_current_user
    from app.main import app

    company, _ = _company_with_actuals(db)
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    other_user = User(id="other-user", email="other@example.com", name="Other")
    db.add(other_user)
    db.commit()
    app.dependency_overrides[get_current_user] = lambda: {
        "id": other_user.id,
        "email": other_user.email,
        "name": other_user.name,
    }

    response = client.get(f"/valuation-drafts/{draft['id']}")

    assert response.status_code == 404


def test_reviewed_draft_promotes_atomically_to_valuation_model(client, db) -> None:
    company, _ = _company_with_actuals(db)
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    assumptions_patch = {
        field: _valid_review_value(field)
        for field in draft["source_metadata_json"]["review_fields"]
    }
    saved = response_data(
        client.patch(
            f"/valuation-drafts/{draft['id']}",
            json={
                "assumptions_patch": assumptions_patch,
                "reviewed_fields": draft["source_metadata_json"]["review_fields"],
            },
        )
    )
    assert saved["status"] == "ready_to_value"

    promoted_response = client.post(
        f"/valuation-drafts/{draft['id']}/promote",
        json={"name": "Reviewed DCF", "description": "Promoted from durable draft", "model_type": "fcff_dcf"},
    )

    assert promoted_response.status_code == 201
    promoted = response_data(promoted_response)
    assert promoted["company_id"] == company.id
    assert promoted["name"] == "Reviewed DCF"
    refreshed_draft = response_data(client.get(f"/valuation-drafts/{draft['id']}"))
    assert refreshed_draft["status"] == "promoted"
    assert refreshed_draft["promoted_model_id"] == promoted["id"]

    repeated_response = client.post(
        f"/valuation-drafts/{draft['id']}/promote",
        json={"name": "Duplicate DCF", "model_type": "fcff_dcf"},
    )
    assert repeated_response.status_code == 409
    assert db.query(ValuationModel).filter_by(company_id=company.id).count() == 1


def test_failed_promotion_rolls_back_model_and_assumption_set(client, db, monkeypatch) -> None:
    company, _ = _company_with_actuals(db)
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    assumptions_patch = {
        field: _valid_review_value(field)
        for field in draft["source_metadata_json"]["review_fields"]
    }
    response_data(
        client.patch(
            f"/valuation-drafts/{draft['id']}",
            json={
                "assumptions_patch": assumptions_patch,
                "reviewed_fields": draft["source_metadata_json"]["review_fields"],
            },
        )
    )

    def fail_calculation(*args, **kwargs):
        raise RuntimeError("calculation failed")

    monkeypatch.setattr(
        "app.services.valuation_setup_draft.calculate_dcf",
        fail_calculation,
    )

    try:
        client.post(
            f"/valuation-drafts/{draft['id']}/promote",
            json={"name": "Failed DCF", "model_type": "fcff_dcf"},
        )
    except RuntimeError as error:
        assert str(error) == "calculation failed"
    else:
        raise AssertionError("Expected the calculation failure to propagate")

    assert db.query(ValuationModel).filter_by(company_id=company.id).count() == 0
    assert db.query(DcfAssumptionSet).count() == 0
    refreshed_draft = response_data(client.get(f"/valuation-drafts/{draft['id']}"))
    assert refreshed_draft["status"] != "promoted"
    assert refreshed_draft["promoted_model_id"] is None


def test_stale_draft_update_is_rejected(client, db) -> None:
    company, _ = _company_with_actuals(db)
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    saved = response_data(
        client.patch(
            f"/valuation-drafts/{draft['id']}",
            json={
                "assumptions_patch": {"starting_revenue": 1250},
                "reviewed_fields": [],
                "expected_updated_at": draft["updated_at"],
            },
        )
    )
    assert saved["updated_at"] != draft["updated_at"]

    stale_response = client.patch(
        f"/valuation-drafts/{draft['id']}",
        json={
            "assumptions_patch": {"starting_revenue": 1300},
            "reviewed_fields": [],
            "expected_updated_at": draft["updated_at"],
        },
    )

    assert stale_response.status_code == 409
    assert "changed since it was loaded" in stale_response.json()["detail"]


def test_reset_field_restores_latest_source_value(client, db) -> None:
    company, _ = _company_with_actuals(db)
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    saved = response_data(
        client.patch(
            f"/valuation-drafts/{draft['id']}",
            json={
                "assumptions_patch": {"starting_revenue": 1250},
                "reviewed_fields": ["starting_revenue"],
                "expected_updated_at": draft["updated_at"],
            },
        )
    )

    reset = response_data(
        client.post(
            f"/valuation-drafts/{draft['id']}/reset",
            json={
                "fields": ["starting_revenue"],
                "expected_updated_at": saved["updated_at"],
            },
        )
    )

    assert reset["assumptions_json"]["starting_revenue"] == 1_000_000_000
    assert reset["provenance_json"]["starting_revenue"]["source_table"] == "normalized_financial_metrics"
    assert "starting_revenue" not in reset["edited_fields_json"]
    assert "starting_revenue" not in reset["reviewed_fields_json"]


def test_archive_excludes_draft_from_reopen_and_blocks_changes(client, db) -> None:
    company, _ = _company_with_actuals(db)
    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))

    archived = response_data(
        client.post(
            f"/valuation-drafts/{draft['id']}/archive",
            json={"expected_updated_at": draft["updated_at"]},
        )
    )

    assert archived["status"] == "archived"
    assert archived["source_metadata_json"]["promotion_ready"] is False
    blocked = client.patch(
        f"/valuation-drafts/{draft['id']}",
        json={"assumptions_patch": {}, "reviewed_fields": []},
    )
    assert blocked.status_code == 409
    replacement = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))
    assert replacement["id"] != draft["id"]


def test_old_financial_sources_are_flagged_for_explicit_review(client, db) -> None:
    company, snapshot = _company_with_actuals(db)
    period = db.get(FinancialStatementPeriod, snapshot.period_id)
    period.report_date = date(2020, 3, 31)
    period.year = 2020
    db.commit()

    draft = response_data(client.post(f"/companies/{company.id}/valuation-drafts", json={}))

    metadata = draft["source_metadata_json"]
    assert "starting_revenue" in metadata["stale_source_fields"]
    assert "starting_revenue" in metadata["review_fields"]
    assert metadata["oldest_source_as_of"] == "2020-03-31"
    assert metadata["promotion_ready"] is False
    assert any("stale source data" in warning.lower() for warning in draft["warnings_json"])
