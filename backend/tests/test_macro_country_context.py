from collections.abc import Generator
from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.macro_sensitivity import SectorMacroSensitivityBenchmark


@contextmanager
def _client_with_db() -> Generator[tuple[TestClient, Session]]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    db = TestingSessionLocal()

    def override_get_db() -> Generator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client, db
    finally:
        app.dependency_overrides.clear()
        db.close()


def _add_benchmark(db: Session) -> None:
    db.add(
        SectorMacroSensitivityBenchmark(
            source_file="macrodur.xls",
            market="IN",
            country="India",
            classification_system="SIC",
            currency_context="INR",
            currency_variable_description="Source file currency movement convention not fully verified.",
            sic_code="5311",
            industry_name="Retail-Department Stores",
            firm_value_duration=-3.01009,
            firm_value_cyclicality=0.297745,
            firm_value_inflation=-2.659937,
            firm_value_currency=-2.017377,
            operating_income_duration=1.906778,
            operating_income_cyclicality=0.693889,
            operating_income_inflation=-1.906778,
            operating_income_currency=-0.693889,
        )
    )
    db.commit()


def test_sector_macro_sensitivity_returns_country_context_and_raw_duration_interpretation() -> None:
    with _client_with_db() as (client, db):
        _add_benchmark(db)

        response = client.get("/api/valuation/macro/sector?market=IN&country=India&sic=5311")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["market"] == "IN"
    assert data["country"] == "India"
    assert data["classification_system"] == "SIC"
    assert data["currency_context"] == "INR"
    assert data["currency_variable_description"] == "Source file currency movement convention not fully verified."
    assert data["raw_duration"] == -3.01009
    assert data["duration_magnitude"] == 3.01009
    assert "Negative raw duration" in data["duration_interpretation"]
    assert data["firm_value_duration"] == -3.01009


def test_macro_scenario_preserves_source_coefficients_and_returns_context() -> None:
    with _client_with_db() as (client, db):
        _add_benchmark(db)

        response = client.post(
            "/api/valuation/macro/scenario",
            json={
                "market": "IN",
                "country": "India",
                "sic_code": "5311",
                "rate_shock": 0.01,
                "gdp_shock": 0.0,
                "inflation_shock": 0.0,
                "currency_shock": 0.0,
                "currencyVariableDirection": "stronger_usd",
            },
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["market"] == "IN"
    assert data["country"] == "India"
    assert data["raw_duration"] == -3.01009
    assert data["estimated_value_impact_pct"] == -0.0301009
    assert "Negative raw duration" in data["warnings"][-1]


def test_bottom_up_macro_sensitivity_returns_segment_country_context() -> None:
    with _client_with_db() as (client, db):
        _add_benchmark(db)

        response = client.post(
            "/api/valuation/macro/bottom-up",
            json={
                "market": "IN",
                "country": "India",
                "segments": [{"name": "Retail", "sicCode": "5311", "value": 100.0}],
            },
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["market"] == "IN"
    assert data["country"] == "India"
    assert data["duration"] == -3.01009
    assert data["duration_magnitude"] == 3.01009
    assert data["segment_exposures"][0]["classification_system"] == "SIC"
    assert data["segment_exposures"][0]["market"] == "IN"
