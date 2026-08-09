from datetime import date

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
    assert created["assumptions_json"]["starting_revenue"] == 1000
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
    assert refreshed["assumptions_json"][source_field] == 1100
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

    assert reset["assumptions_json"]["starting_revenue"] == 1000
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
