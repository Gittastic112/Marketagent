import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.macro_sensitivity import SectorMacroSensitivityBenchmark
from app.services.macro_scenario_translation import MacroScenarioTranslationService


def _session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return TestingSessionLocal()


def test_translates_sector_macro_shocks_into_estimated_impacts():
    db = _session()
    db.add(
        SectorMacroSensitivityBenchmark(
            source_file="macrodur.xls",
            sic_code="9999",
            industry_name="Test Industry",
            firm_value_duration=-3.0,
            firm_value_cyclicality=0.5,
            firm_value_inflation=-1.0,
            firm_value_currency=0.2,
            operating_income_duration=-1.0,
            operating_income_cyclicality=0.25,
            operating_income_inflation=-0.5,
            operating_income_currency=0.1,
        )
    )
    db.commit()

    result = MacroScenarioTranslationService.translate(
        db,
        sic_code="9999",
        rate_shock=0.01,
        gdp_shock=-0.02,
        inflation_shock=0.015,
        currency_shock=0.05,
    )

    assert result["method"] == "sector_macro_sensitivity"
    assert result["sic_code"] == "9999"
    assert result["industry_name"] == "Test Industry"
    assert result["estimated_value_impact_pct"] == pytest.approx(-0.045)
    assert result["estimated_operating_income_impact_pct"] == pytest.approx(-0.0175)
    assert result["affected_assumptions"] == [
        "risk_free_rate",
        "terminal_value",
        "revenue_growth",
        "operating_margin",
        "currency_translation",
    ]
    assert result["confidence"] == "medium"
    assert "source_file=macrodur.xls" in result["formula"]
    assert any("does not automatically change valuation assumptions" in warning for warning in result["warnings"])
    assert any("Currency sensitivity" in warning for warning in result["warnings"])


def test_missing_sector_macro_sensitivity_raises_lookup_error():
    db = _session()

    with pytest.raises(LookupError):
        MacroScenarioTranslationService.translate(
            db,
            sic_code="missing",
            rate_shock=0.01,
            gdp_shock=0.0,
            inflation_shock=0.0,
            currency_shock=0.0,
        )
