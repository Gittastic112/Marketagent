import pytest
from datetime import date
from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.damodaran import DamodaranDatasetFile
from app.models.assumption_methodology import AssumptionMethodValue
from app.models.financial import FinancialStatementPeriod, FinancialMetric, NormalizedFinancialSnapshot, NormalizedFinancialMetric
from app.models.damodaran_fundamentals import DamodaranMarginBenchmark
from app.services.assumption_autofill_engine import AssumptionAutofillEngine

def test_autofill_engine_with_no_data(db_session: Session):
    company = Company(name="Empty Co", ticker="EMP", market="US")
    db_session.add(company)
    db_session.commit()

    res = AssumptionAutofillEngine.draft_assumptions(db_session, company.id)

    assert res["warnings"]
    assert any("no extracted actuals" in w for w in res["warnings"])
    assert any("not mapped" in w for w in res["warnings"])

    # Check fallbacks are correctly tagged
    provenance = res["provenance"]
    source_metadata = res["source_metadata"]

    assert source_metadata["promotion_ready"] is False
    assert source_metadata["requires_review"] is True
    assert "starting_revenue" in source_metadata["placeholder_fields"]
    assert source_metadata["source_counts_by_type"]["missing_actual_default"] > 0

    assert provenance.get("revenue_growth_years_json", {}).get("source_type") == "generic_market_default"
    assert provenance["revenue_growth_years_json"]["is_placeholder"] is True
    assert provenance["revenue_growth_years_json"]["label"].startswith("[PLACEHOLDER]")
    assert provenance.get("terminal_growth_rate", {}).get("source_type") == "missing_dependency"
    assert provenance["terminal_growth_rate"]["requires_review"] is True
    assert provenance.get("starting_revenue", {}).get("source_type") == "missing_actual_default"
    assert provenance["starting_revenue"]["label"].startswith("[PLACEHOLDER]")
    assert provenance["starting_revenue"]["requires_review"] is True
    assert set(item["field"] for item in source_metadata["input_readiness"]) == set(
        AssumptionAutofillEngine.INPUT_CONTRACT
    )
    assert source_metadata["input_readiness_summary"]["required_missing_fields"]


def test_autofill_uses_currency_matched_active_workbook_methods(db_session: Session):
    company = Company(
        name="Transportation Co",
        ticker="TRANS",
        market="India",
        country="India",
        currency="INR",
        damodaran_industry="Transportation",
    )
    dataset = DamodaranDatasetFile(
        uploaded_filename="waccIndia.xls",
        dataset_code="wacc_methods",
        country="India",
        source_file_type="xls",
        source_sha256="workbook-hash",
        source_as_of="2026-01-05",
        canonical_source_path="raw/datasets/waccIndia.xls",
        import_kind="typed",
        is_active=True,
        row_count=4,
    )
    db_session.add_all([company, dataset])
    db_session.flush()
    common = {
        "dataset_file_id": dataset.id,
        "country": "India",
        "unit": "decimal",
        "source_type": "damodaran",
        "source_name": "Damodaran January 2026 benchmark",
        "source_file": "waccIndia.xls",
        "source_sheet": "Industry Averages",
        "confidence": "high",
        "is_default_candidate": True,
    }
    db_session.add_all([
        AssumptionMethodValue(
            **common,
            assumption_key="risk_free_rate",
            method_key="inflation_parity_from_us_treasury",
            currency="INR",
            value=0.06485365853658531,
            source_row="9,16,17",
            source_column="Rows 9, 16, and 17",
        ),
        AssumptionMethodValue(
            **common,
            assumption_key="equity_risk_premium",
            method_key="damodaran_country_erp",
            value=0.0708,
            source_row="10",
            source_column="Risk Premium to Use for Equity",
        ),
        AssumptionMethodValue(
            **common,
            assumption_key="wacc_start",
            method_key="industry_cost_of_capital_local",
            industry="Transportation",
            currency="INR",
            value=0.13400219494298193,
            source_row="31",
            source_column="Cost of Capital (Local Currency)",
        ),
        AssumptionMethodValue(
            **common,
            assumption_key="debt_to_capital",
            method_key="industry_market_debt_ratio",
            industry="Transportation",
            value=0.17552459524761466,
            source_row="31",
            source_column="D/(D+E)",
        ),
    ])
    db_session.commit()

    result = AssumptionAutofillEngine.draft_assumptions(db_session, company.id)

    assert result["assumptions"]["risk_free_rate"] == pytest.approx(0.06485365853658531)
    assert result["assumptions"]["equity_risk_premium"] == pytest.approx(0.0708)
    assert result["assumptions"]["debt_to_capital"] == pytest.approx(0.17552459524761466)
    assert result["assumptions"]["wacc_start"] == pytest.approx(0.13400219494298193)
    source = result["provenance"]["wacc_start"]
    assert source["source_file"] == "waccIndia.xls"
    assert source["source_sha256"] == "workbook-hash"
    assert source["source_as_of"] == "2026-01-05"
    assert source["source_row"] == "31"
    assert source["requires_review"] is True
    assert result["assumptions"]["cash_flow_currency"] == "INR"
    assert result["assumptions"]["discount_rate_currency"] == "INR"

def test_autofill_engine_with_priors(db_session: Session):
    company = Company(name="Priors Co", ticker="PRI", market="India", damodaran_industry="Software (Internet)")
    dataset = DamodaranDatasetFile(
        uploaded_filename="marginIndia.xls",
        dataset_code="margin",
        country="India",
        source_file_type="xls",
    )
    db_session.add_all([company, dataset])
    db_session.flush()

    bm = DamodaranMarginBenchmark(
        dataset_file_id=dataset.id,
        industry_name="Software (Internet)",
        number_of_firms=10,
        gross_margin=0.8,
        ebitda_margin=0.3,
        ebit_margin=0.2,
        net_margin=0.15,
        country="India"
    )
    db_session.add(bm)
    db_session.commit()

    res = AssumptionAutofillEngine.draft_assumptions(db_session, company.id)

    # target margin should pull from priors
    assert res["assumptions"]["target_operating_margin"] == 0.2
    assert "Damodaran Prior" in res["provenance"]["target_operating_margin"]["label"]
    assert res["provenance"]["target_operating_margin"]["source_type"] == "industry_benchmark"

def test_autofill_engine_with_actuals(db_session: Session):
    company = Company(name="Actuals Co", ticker="ACT", market="India")
    db_session.add(company)
    db_session.commit()

    period = FinancialStatementPeriod(
        company_id=company.id,
        year=2023,
        quarter=4,
        period_type="annual",
        report_date=date(2023, 12, 31),
    )
    db_session.add(period)
    db_session.commit()

    # Legacy metrics
    rev = FinancialMetric(period_id=period.id, metric_name="revenue", value=5000)
    ebit = FinancialMetric(period_id=period.id, metric_name="ebit", value=1000)
    db_session.add_all([rev, ebit])
    db_session.commit()

    # Normalized metrics override legacy metrics
    snapshot = NormalizedFinancialSnapshot(company_id=company.id, period_id=period.id)
    db_session.add(snapshot)
    db_session.commit()

    n_rev = NormalizedFinancialMetric(snapshot_id=snapshot.id, metric_code="revenue", value=5500)
    n_ebit = NormalizedFinancialMetric(snapshot_id=snapshot.id, metric_code="ebit", value=1100)
    db_session.add_all([n_rev, n_ebit])
    db_session.commit()

    res = AssumptionAutofillEngine.draft_assumptions(db_session, company.id)

    assert res["assumptions"]["starting_revenue"] == 5500
    assert "Normalized Financials" in res["provenance"]["starting_revenue"]["label"]
    assert "FY2023" in res["provenance"]["starting_revenue"]["label"]
    assert res["provenance"]["starting_revenue"]["source_type"] == "company_actual"
    assert res["provenance"]["starting_revenue"]["claim_type"] == "Fact"
    assert res["provenance"]["starting_revenue"]["source_table"] == "normalized_financial_metrics"
    assert res["provenance"]["starting_revenue"]["source_record_id"] == n_rev.id
    assert res["provenance"]["starting_revenue"]["snapshot_id"] == snapshot.id
    assert res["provenance"]["starting_revenue"]["period_id"] == period.id
    assert res["provenance"]["starting_revenue"]["fiscal_year"] == 2023

    # 1100 / 5500 = 0.2
    assert res["assumptions"]["current_operating_margin"] == 0.2
    margin_source = res["provenance"]["current_operating_margin"]
    assert margin_source["source_type"] == "calculation"
    assert margin_source["claim_type"] == "Calculation"
    assert margin_source["calculation_basis"]["revenue"]["source_record_id"] == n_rev.id
    assert margin_source["calculation_basis"]["ebit"]["source_record_id"] == n_ebit.id


def test_autofill_uses_normalized_capital_and_revenue_history(db_session: Session):
    company = Company(name="History Co", ticker="HIST", market="India", country="India")
    db_session.add(company)
    db_session.flush()

    periods = []
    for year, revenue in ((2024, 1000), (2025, 1200), (2026, 1500)):
        period = FinancialStatementPeriod(
            company_id=company.id,
            year=year,
            quarter=4,
            period_type="annual",
            report_date=date(year, 12, 31),
            currency="INR",
        )
        db_session.add(period)
        db_session.flush()
        snapshot = NormalizedFinancialSnapshot(company_id=company.id, period_id=period.id)
        db_session.add(snapshot)
        db_session.flush()
        metrics = [
            NormalizedFinancialMetric(
                snapshot_id=snapshot.id,
                metric_code="revenue",
                value=revenue,
                unit="INR million",
                provenance_notes=f"Reviewed FY{year} revenue",
            )
        ]
        if year == 2026:
            metrics.extend(
                [
                    NormalizedFinancialMetric(snapshot_id=snapshot.id, metric_code="ebit", value=300, unit="INR million"),
                    NormalizedFinancialMetric(
                        snapshot_id=snapshot.id,
                        metric_code="invested_capital",
                        value=750,
                        unit="INR million",
                        provenance_notes="Computed from reviewed balance sheet items",
                    ),
                ]
            )
        db_session.add_all(metrics)
        periods.append(period)
    db_session.commit()

    result = AssumptionAutofillEngine.draft_assumptions(db_session, company.id)

    assumptions = result["assumptions"]
    assert assumptions["starting_invested_capital"] == 750
    assert assumptions["sales_to_capital_ratio"] == pytest.approx(2.0)
    expected_cagr = (1500 / 1000) ** (1 / 2) - 1
    assert assumptions["revenue_growth_years_json"]["1"] == pytest.approx(expected_cagr)

    capital_source = result["provenance"]["starting_invested_capital"]
    assert capital_source["claim_type"] == "Calculation"
    assert capital_source["source_table"] == "normalized_financial_metrics"
    assert capital_source["provenance_notes"] == "Computed from reviewed balance sheet items"

    ratio_source = result["provenance"]["sales_to_capital_ratio"]
    assert ratio_source["source_type"] == "calculation"
    assert ratio_source["calculation_basis"]["invested_capital"]["source_record_id"] == capital_source["source_record_id"]

    growth_source = result["provenance"]["revenue_growth_years_json"]
    assert growth_source["source_type"] == "calculation"
    assert growth_source["history_years"] == [2024, 2025, 2026]
    assert growth_source["claim_type"] == "Calculation"


def test_autofill_derives_invested_capital_when_reported_value_is_zero(db_session: Session):
    company = Company(name="Zero Capital Co", ticker="ZERO", market="US")
    db_session.add(company)
    db_session.flush()
    period = FinancialStatementPeriod(
        company_id=company.id,
        year=2026,
        period_type="annual",
        report_date=date(2026, 12, 31),
        currency="USD",
    )
    db_session.add(period)
    db_session.flush()
    snapshot = NormalizedFinancialSnapshot(company_id=company.id, period_id=period.id)
    db_session.add(snapshot)
    db_session.flush()
    db_session.add_all([
        NormalizedFinancialMetric(snapshot_id=snapshot.id, metric_code="revenue", value=1500, unit="USD"),
        NormalizedFinancialMetric(snapshot_id=snapshot.id, metric_code="invested_capital", value=0, unit="USD"),
    ])
    db_session.commit()

    result = AssumptionAutofillEngine.draft_assumptions(db_session, company.id)

    assumptions = result["assumptions"]
    assert assumptions["starting_invested_capital"] == pytest.approx(
        assumptions["starting_revenue"] / assumptions["sales_to_capital_ratio"]
    )
    assert result["provenance"]["starting_invested_capital"]["source_type"] == "formula"


def test_autofill_marks_warning_bearing_normalized_metric_for_review(db_session: Session):
    company = Company(name="Warnings Co", ticker="WARN", market="India", country="India")
    db_session.add(company)
    db_session.flush()
    period = FinancialStatementPeriod(
        company_id=company.id,
        year=2026,
        period_type="annual",
        report_date=date(2026, 12, 31),
        currency="INR",
    )
    db_session.add(period)
    db_session.flush()
    snapshot = NormalizedFinancialSnapshot(company_id=company.id, period_id=period.id)
    db_session.add(snapshot)
    db_session.flush()
    metric = NormalizedFinancialMetric(
        snapshot_id=snapshot.id,
        metric_code="effective_tax_rate",
        value=0.25,
        provenance_notes="Default or capped",
        warnings="Pre-tax income missing or negative, using default 25% tax rate.",
    )
    db_session.add(metric)
    db_session.commit()

    result = AssumptionAutofillEngine.draft_assumptions(db_session, company.id)

    source = result["provenance"]["tax_rate"]
    assert source["claim_type"] == "Calculation"
    assert source["requires_review"] is True
    assert source["warnings"] == metric.warnings
    assert "tax_rate" in result["source_metadata"]["review_fields"]
    assert result["source_metadata"]["promotion_ready"] is False


def test_autofill_legacy_fallback_is_limited_to_same_period_bridge_fields(db_session: Session):
    company = Company(name="Fallback Co", ticker="FBK", market="India", country="India")
    db_session.add(company)
    db_session.flush()
    period = FinancialStatementPeriod(
        company_id=company.id,
        year=2026,
        period_type="annual",
        report_date=date(2026, 12, 31),
        currency="INR",
    )
    db_session.add(period)
    db_session.flush()
    legacy_revenue = FinancialMetric(period_id=period.id, metric_name="revenue", value=9999)
    legacy_cash = FinancialMetric(period_id=period.id, metric_name="cash", value=400)
    db_session.add_all([legacy_revenue, legacy_cash])
    snapshot = NormalizedFinancialSnapshot(company_id=company.id, period_id=period.id)
    db_session.add(snapshot)
    db_session.flush()
    normalized_revenue = NormalizedFinancialMetric(
        snapshot_id=snapshot.id,
        metric_code="revenue",
        value=1200,
    )
    db_session.add(normalized_revenue)
    db_session.commit()

    result = AssumptionAutofillEngine.draft_assumptions(db_session, company.id)

    assert result["assumptions"]["starting_revenue"] == 1200
    assert result["provenance"]["starting_revenue"]["source_record_id"] == normalized_revenue.id
    assert result["assumptions"]["cash"] == 400
    assert result["provenance"]["cash"]["fallback_policy"] == "same_period_missing_normalized_bridge_metric"
    assert result["source_metadata"]["legacy_fallback_fields"] == ["cash"]


def test_autofill_uses_normalized_fcfe_inputs_and_currency_metadata(db_session: Session):
    company = Company(name="Bridge Co", ticker="BRIDGE", market="India", country="India")
    db_session.add(company)
    db_session.flush()
    period = FinancialStatementPeriod(
        company_id=company.id,
        year=2026,
        period_type="annual",
        report_date=date(2026, 12, 31),
        currency="INR",
    )
    db_session.add(period)
    db_session.flush()
    snapshot = NormalizedFinancialSnapshot(company_id=company.id, period_id=period.id)
    db_session.add(snapshot)
    db_session.flush()
    values = {
        "revenue": 1000,
        "ebit": 200,
        "cash": 100,
        "debt": 250,
        "diluted_shares": 50,
        "net_income": 120,
        "capex": 80,
        "depreciation": 30,
        "change_in_nwc": 10,
    }
    db_session.add_all(
        [
            NormalizedFinancialMetric(
                snapshot_id=snapshot.id,
                metric_code=code,
                value=value,
                unit="million shares" if code == "diluted_shares" else "INR million",
            )
            for code, value in values.items()
        ]
    )
    db_session.commit()

    result = AssumptionAutofillEngine.draft_assumptions(db_session, company.id)

    for key in ("cash", "debt", "diluted_shares", "net_income", "capex", "depreciation", "change_in_nwc"):
        assert result["assumptions"][key] == values[key]
        assert result["provenance"][key]["source_table"] == "normalized_financial_metrics"
    assert result["source_metadata"]["legacy_fallback_fields"] == []
    assert result["source_metadata"]["reporting_currency"] == "INR"
    assert result["source_metadata"]["reporting_currency_source"] == "reviewed_metric_unit"
    assert result["source_metadata"]["reporting_currency_confidence"] == "high"
