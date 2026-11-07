import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.macro_sensitivity import SectorMacroSensitivityBenchmark
from app.services.bottom_up_macro_sensitivity import BottomUpMacroSensitivityService


def _session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return TestingSessionLocal()


def _add_benchmark(
    db,
    *,
    sic_code: str,
    industry_name: str,
    duration: float,
    cyclicality: float,
    inflation: float,
    currency: float,
):
    db.add(
        SectorMacroSensitivityBenchmark(
            source_file="macrodur.xls",
            sic_code=sic_code,
            industry_name=industry_name,
            firm_value_duration=duration,
            firm_value_cyclicality=cyclicality,
            firm_value_inflation=inflation,
            firm_value_currency=currency,
            operating_income_duration=duration / 2,
            operating_income_cyclicality=cyclicality / 2,
            operating_income_inflation=inflation / 2,
            operating_income_currency=currency / 2,
        )
    )


def test_calculates_segment_weighted_bottom_up_sensitivity():
    db = _session()
    _add_benchmark(
        db,
        sic_code="5311",
        industry_name="Retail",
        duration=3.0,
        cyclicality=-0.3,
        inflation=1.9,
        currency=0.7,
    )
    _add_benchmark(
        db,
        sic_code="3571",
        industry_name="Hardware",
        duration=1.0,
        cyclicality=1.2,
        inflation=-0.4,
        currency=-0.2,
    )
    db.commit()

    result = BottomUpMacroSensitivityService.calculate(
        db,
        segments=[
            {"name": "Retail", "sic_code": "5311", "value": 60.0},
            {"name": "Hardware", "sic_code": "3571", "value": 40.0},
        ],
    )

    assert result["method"] == "bottom_up"
    assert result["duration"] == pytest.approx(2.2)
    assert result["cyclicality"] == pytest.approx(0.3)
    assert result["inflation_sensitivity"] == pytest.approx(0.98)
    assert result["currency_sensitivity"] == pytest.approx(0.34)
    assert result["covered_weight"] == 1.0
    assert result["confidence"] == "medium"
    assert result["segment_exposures"][0]["weight"] == pytest.approx(0.6)


def test_bottom_up_sensitivity_reports_missing_segment_coverage():
    db = _session()
    _add_benchmark(
        db,
        sic_code="5311",
        industry_name="Retail",
        duration=3.0,
        cyclicality=-0.3,
        inflation=1.9,
        currency=0.7,
    )
    db.commit()

    result = BottomUpMacroSensitivityService.calculate(
        db,
        segments=[
            {"name": "Retail", "sic_code": "5311", "value": 60.0},
            {"name": "Unknown", "sic_code": "0000", "value": 40.0},
        ],
    )

    assert result["duration"] is None
    assert result["covered_contributions"]["duration"] == pytest.approx(1.8)
    assert result["metric_coverage"]["duration"] == pytest.approx(0.6)
    assert result["covered_weight"] == 0.6
    assert result["confidence"] == "low"
    assert result["missing_segments"] == [{"name": "Unknown", "sic_code": "0000", "weight": 0.4}]
    assert any("Missing SIC benchmark" in warning for warning in result["warnings"])


def test_bottom_up_sensitivity_rejects_zero_total_value():
    db = _session()

    with pytest.raises(ValueError, match="Total segment value must be greater than zero"):
        BottomUpMacroSensitivityService.calculate(
            db,
            segments=[{"name": "Retail", "sic_code": "5311", "value": 0.0}],
        )
