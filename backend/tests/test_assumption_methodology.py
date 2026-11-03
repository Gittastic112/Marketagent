from app.models.assumption_methodology import AssumptionMethodValue
from app.models.damodaran import DamodaranDatasetFile
from app.services.assumption_methodology import AssumptionMethodologyService


def _dataset(db_session, *, active: bool = True) -> DamodaranDatasetFile:
    dataset = DamodaranDatasetFile(
        uploaded_filename="waccIndia.xls",
        dataset_code="wacc_methods",
        country="India",
        source_file_type="xls",
        source_sha256="abc123",
        source_as_of="2026-01-05",
        canonical_source_path="raw/datasets/waccIndia.xls",
        import_kind="typed",
        is_active=active,
        row_count=1,
    )
    db_session.add(dataset)
    db_session.flush()
    return dataset


def test_unseeded_methods_are_honest_user_input_only(db_session):
    methods = AssumptionMethodologyService.get_available_methods(
        db_session, "equity_risk_premium", "India"
    )

    assert [method["method_key"] for method in methods] == ["user_custom"]
    assert AssumptionMethodologyService.get_default_method(
        db_session, "equity_risk_premium", "India"
    ) is None


def test_default_method_uses_active_currency_and_industry_source(db_session):
    active = _dataset(db_session)
    inactive = _dataset(db_session, active=False)
    db_session.add_all([
        AssumptionMethodValue(
            dataset_file_id=active.id,
            assumption_key="wacc_start",
            method_key="industry_cost_of_capital_local",
            country="India",
            industry="Transportation",
            currency="INR",
            value=0.13400219494298193,
            unit="decimal",
            source_type="damodaran",
            source_name="Damodaran January 2026 benchmark",
            source_file="waccIndia.xls",
            source_sheet="Industry Averages",
            source_row="31",
            source_column="Cost of Capital (Local Currency)",
            confidence="high",
            is_default_candidate=True,
        ),
        AssumptionMethodValue(
            dataset_file_id=inactive.id,
            assumption_key="wacc_start",
            method_key="obsolete_method",
            country="India",
            industry="Transportation",
            currency="INR",
            value=0.99,
            unit="decimal",
            source_type="damodaran",
            source_name="Obsolete",
            confidence="low",
            is_default_candidate=True,
        ),
    ])
    db_session.commit()

    default = AssumptionMethodologyService.get_default_method(
        db_session,
        "wacc_start",
        "India",
        "Transportation",
        "INR",
    )

    assert default is not None
    assert default["method_key"] == "industry_cost_of_capital_local"
    assert default["value"] == 0.13400219494298193
    assert default["source"]["dataset_file_id"] == active.id
    assert default["source"]["source_sha256"] == "abc123"
    assert default["source"]["source_as_of"] == "2026-01-05"
    assert default["source"]["source_row"] == "31"


def test_build_pack_exposes_all_discount_rate_components(db_session):
    pack = AssumptionMethodologyService.build_country_assumption_pack(
        db_session, "India", "Transportation", "INR"
    )

    for key in (
        "equity_risk_premium",
        "risk_free_rate",
        "beta",
        "pre_tax_cost_of_debt",
        "debt_to_capital",
        "equity_to_capital",
        "wacc_start",
        "country_default_spread",
        "tax_rate",
    ):
        assert key in pack
        assert pack[key]["default_method"] == "user_custom"


def test_country_alias_matches_us_workbook_without_cross_country_fallback(db_session):
    dataset = _dataset(db_session)
    db_session.add(AssumptionMethodValue(dataset_file_id=dataset.id,
        assumption_key="tax_rate", method_key="country_marginal_corporate_tax_rate",
        country="United States of America", value=0.2577, unit="decimal",
        source_type="damodaran", source_name="Mock Data country tax workbook",
        is_default_candidate=True))
    db_session.commit()
    for country in ("United States", "United States of America", "US", "USA", "us"):
        method = AssumptionMethodologyService.get_default_method(db_session, "tax_rate", country)
        assert method["value"] == 0.2577
    assert AssumptionMethodologyService.get_default_method(db_session, "tax_rate", "India") is None


def test_wacc_workbook_global_input_is_not_labeled_country_fact(db_session):
    dataset = _dataset(db_session)
    db_session.add(AssumptionMethodValue(dataset_file_id=dataset.id,
        assumption_key="equity_risk_premium", method_key="damodaran_country_erp",
        country="India", value=0.0708, unit="decimal", source_type="damodaran",
        source_name="Mock Data workbook", source_file="waccIndia.xls",
        notes="India total ERP used by the dated WACC workbook.", is_default_candidate=True))
    db_session.commit()
    method = AssumptionMethodologyService.get_default_method(db_session, "equity_risk_premium", "India")
    assert "workbook" in method["label"]
    assert "Global weighted average" in method["notes"]
    assert "India total ERP" not in method["notes"]
