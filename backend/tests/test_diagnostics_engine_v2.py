from app.models.dcf import DcfAssumptionSet
from app.services.diagnostics_engine import DiagnosticsEngine


def messages(warnings):
    return [warning.message for warning in warnings]


def modules(warnings):
    return [warning.module for warning in warnings]


def test_financial_services_companies_block_fcff_model():
    warnings = DiagnosticsEngine.check_financial_services_model(
        DcfAssumptionSet(),
        company_sector="Financial Services",
        company_industry="Banking",
    )

    assert any(warning.severity == "blocking" for warning in warnings)
    assert "model_selection" in modules(warnings)
    assert any("FCFF models are not appropriate" in message for message in messages(warnings))


def test_margin_and_terminal_roc_benchmark_warnings():
    assumption_set = DcfAssumptionSet(
        target_operating_margin=0.30,
        terminal_roic=0.24,
    )

    margin_warnings = DiagnosticsEngine.check_margin_vs_industry(
        assumption_set,
        industry_operating_margin=0.10,
    )
    roc_warnings = DiagnosticsEngine.check_terminal_roc_vs_industry(
        assumption_set,
        industry_roc=0.08,
    )

    assert any("industry average" in message for message in messages(margin_warnings))
    assert any("Terminal ROC" in message for message in messages(roc_warnings))


def test_negative_fcff_and_external_funding_warnings():
    projection_years = [
        {"fcff": -10.0},
        {"fcff": -15.0},
        {"fcff": -20.0},
        {"fcff": -5.0},
        {"fcff": 2.0},
    ]

    duration_warnings = DiagnosticsEngine.check_negative_fcff_duration(projection_years)
    funding_warnings = DiagnosticsEngine.check_external_funding_risk(projection_years)

    assert any("negative for 4 consecutive" in message for message in messages(duration_warnings))
    assert any(warning.severity == "info" for warning in funding_warnings)
    assert any("external capital" in message for message in messages(funding_warnings))


def test_share_count_and_basic_vs_diluted_guards():
    missing_share_warnings = DiagnosticsEngine.check_share_count(
        DcfAssumptionSet(diluted_shares=0.0)
    )
    basic_vs_diluted_warnings = DiagnosticsEngine.check_basic_vs_diluted_shares(
        DcfAssumptionSet(diluted_shares=100.0, basic_shares=100.0)
    )
    invalid_share_warnings = DiagnosticsEngine.check_basic_vs_diluted_shares(
        DcfAssumptionSet(diluted_shares=90.0, basic_shares=100.0)
    )

    assert any(warning.severity == "critical" for warning in missing_share_warnings)
    assert any("basic shares" in message for message in messages(basic_vs_diluted_warnings))
    assert any(warning.severity == "blocking" for warning in invalid_share_warnings)


def test_user_override_far_from_benchmark_flags_low_assumptions():
    warnings = DiagnosticsEngine.check_user_override_far_from_benchmark(
        DcfAssumptionSet(
            target_operating_margin=0.04,
            terminal_roic=0.03,
        ),
        industry_operating_margin=0.12,
        industry_roc=0.10,
    )

    assert len(warnings) == 2
    assert all(warning.severity == "watch" for warning in warnings)
