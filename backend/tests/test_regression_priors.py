import math

from app.models.damodaran_fundamentals import RegressionModelCoefficient
from app.services.regression_model_catalog import REGRESSION_MODEL_SPECS
from app.services.regression_prior_service import RegressionPriorService
from app.services.regression_seed_service import sync_source_backed_regression_coefficients


def _seed(db_session) -> None:
    sync_source_backed_regression_coefficients(db_session)
    db_session.commit()


def test_source_catalog_contains_exact_january_2025_models():
    specs = {spec.model_name: spec for spec in REGRESSION_MODEL_SPECS}

    assert len(specs) == 6
    assert sum(len(spec.coefficients) for spec in specs.values()) == 26
    assert specs["global_debt_ratio"].coefficients == {
        "intercept": 17.419,
        "effective_tax_rate_pct": -0.057,
        "expected_eps_growth": -20.401,
        "institutional_holdings": -2.153,
        "company_age_years": 0.033,
    }
    assert specs["global_dividend_yield"].coefficients == {
        "intercept": 1.835,
        "effective_tax_rate_pct": 0.035,
        "expected_eps_growth": -3.603,
        "company_age_years": 0.004,
        "beta": -0.279,
    }
    assert specs["global_dividend_payout"].usable is False
    assert specs["global_dividend_payout"].adjusted_r_squared == 0.0


def test_seed_is_scoped_and_idempotent(db_session):
    unrelated = RegressionModelCoefficient(
        model_name="unrelated_research_model",
        variable_name="intercept",
        coefficient_value=123.0,
        region="Other",
    )
    legacy = RegressionModelCoefficient(
        model_name="Global_Debt_Ratio",
        variable_name="EBITDA_to_Value",
        coefficient_value=0.18,
        region="Global",
    )
    db_session.add_all([unrelated, legacy])
    db_session.commit()

    first = sync_source_backed_regression_coefficients(db_session)
    db_session.commit()
    second = sync_source_backed_regression_coefficients(db_session)
    db_session.commit()

    assert first == {
        "models": 6,
        "coefficients": 26,
        "created": 26,
        "updated": 0,
        "deleted": 1,
        "unchanged": 0,
    }
    assert second["created"] == 0
    assert second["updated"] == 0
    assert second["deleted"] == 0
    assert second["unchanged"] == 26
    assert db_session.query(RegressionModelCoefficient).filter_by(
        model_name="unrelated_research_model"
    ).one().coefficient_value == 123.0


def test_global_debt_ratio_matches_pdf_worked_example(db_session):
    _seed(db_session)

    result = RegressionPriorService.calculate_debt_ratio_prior(
        db_session,
        effective_tax_rate=0.25,
        expected_eps_growth=0.12,
        institutional_holdings=0.30,
        company_age_years=37,
        region="Global",
    )

    assert math.isclose(result["prior_value"], 0.1412098, abs_tol=1e-10)
    assert result["claim_type"] == "Estimate"
    assert result["source_as_of"] == "2025-01"
    assert result["adjusted_r_squared"] == 0.065
    assert result["confidence"] == "low"
    assert any("LOW_EXPLANATORY_POWER" in warning for warning in result["warnings"])


def test_global_dividend_yield_matches_pdf_worked_example(db_session):
    _seed(db_session)

    result = RegressionPriorService.calculate_dividend_yield_prior(
        db_session,
        effective_tax_rate=0.20,
        expected_eps_growth=0.10,
        company_age_years=35,
        beta=1.20,
        region="Global",
    )

    assert math.isclose(result["prior_value"], 0.019799, abs_tol=1e-12)
    assert result["model"] == "global_dividend_yield"


def test_statistically_unusable_payout_prior_returns_no_value(db_session):
    _seed(db_session)

    result = RegressionPriorService.calculate_dividend_payout_prior(
        db_session,
        beta=1.0,
        return_on_equity=0.15,
        region="Global",
    )

    assert result["prior_value"] is None
    assert result["usable"] is False
    assert result["confidence"] == "not_usable"
    assert any("MODEL_NOT_USABLE" in warning for warning in result["warnings"])


def test_tampered_coefficient_fails_closed(db_session):
    _seed(db_session)
    row = db_session.query(RegressionModelCoefficient).filter_by(
        model_name="global_debt_ratio",
        variable_name="intercept",
    ).one()
    row.coefficient_value = 99.0
    db_session.commit()

    result = RegressionPriorService.calculate_debt_ratio_prior(
        db_session,
        effective_tax_rate=0.25,
        expected_eps_growth=0.12,
        institutional_holdings=0.30,
        company_age_years=37,
    )

    assert result["prior_value"] is None
    assert any("COEFFICIENT_SOURCE_MISMATCH" in warning for warning in result["warnings"])


def test_regression_prior_api_contract_and_validation(client, db_session):
    _seed(db_session)

    response = client.post(
        "/api/priors/debt-ratio",
        json={
            "effective_tax_rate": 0.25,
            "expected_eps_growth": 0.12,
            "institutional_holdings": 0.30,
            "company_age_years": 37,
            "region": "Global",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert math.isclose(data["prior_value"], 0.1412098, abs_tol=1e-10)
    assert data["source_path"].endswith("debt regression.pdf")
    assert data["input_units"]["effective_tax_rate"] == "decimal"

    invalid = client.post(
        "/api/priors/debt-ratio",
        json={
            "effective_tax_rate": 25,
            "expected_eps_growth": 0.12,
            "institutional_holdings": 0.30,
            "company_age_years": 37,
            "region": "Global",
        },
    )
    assert invalid.status_code == 422
