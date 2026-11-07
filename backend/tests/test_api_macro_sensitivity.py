from collections.abc import Generator
from contextlib import contextmanager
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.macro import MacroObservation, MacroSeries
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


def test_get_sector_macro_sensitivity_by_sic():
    with _client_with_db() as (client, db):
        db.add(
            SectorMacroSensitivityBenchmark(
                source_file="macrodur.xls",
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

        response = client.get("/api/valuation/macro/sector?sic=5311")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["sic_code"] == "5311"
        assert body["data"]["industry_name"] == "Retail-Department Stores"
        assert body["data"]["firm_value_duration"] == -3.01009
        assert body["meta"]["source"] == "internal"


def test_get_macro_data_filters_by_frequency_and_series_name():
    with _client_with_db() as (client, db):
        series = MacroSeries(
            name="macrodur.quarterly.t_bond_rate",
            description="T.Bond Rate from macrodur.xls",
            frequency="quarterly",
        )
        db.add(series)
        db.flush()
        db.add_all(
            [
                MacroObservation(series_id=series.id, date_recorded=date(2025, 9, 30), value=0.0416),
                MacroObservation(series_id=series.id, date_recorded=date(2025, 12, 31), value=0.0418),
            ]
        )
        db.commit()

        response = client.get(
            "/api/valuation/macro/data"
            "?frequency=quarterly"
            "&series_name=macrodur.quarterly.t_bond_rate"
            "&start=2025-10-01"
            "&end=2025-12-31"
        )

        assert response.status_code == 200
        body = response.json()
        assert body["data"] == [
            {
                "series_name": "macrodur.quarterly.t_bond_rate",
                "description": "T.Bond Rate from macrodur.xls",
                "frequency": "quarterly",
                "date_recorded": "2025-12-31",
                "value": 0.0418,
            }
        ]


def test_post_macro_scenario_translates_shocks():
    with _client_with_db() as (client, db):
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

        response = client.post(
            "/api/valuation/macro/scenario",
            json={
                "sic_code": "9999",
                "rate_shock": 0.01,
                "gdp_shock": -0.02,
                "inflation_shock": 0.015,
                "currency_shock": 0.05,
                "currencyVariableDirection": "Mock Data source: stronger USD",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["estimated_value_impact_pct"] == -0.045
        assert body["data"]["estimated_operating_income_impact_pct"] == -0.0175
        assert "currency_translation" in body["data"]["affected_assumptions"]
        assert body["meta"]["source"] == "internal"


def test_post_macro_scenario_returns_404_for_missing_sic():
    with _client_with_db() as (client, _db):
        response = client.post(
            "/api/valuation/macro/scenario",
            json={
                "sic_code": "missing",
                "rate_shock": 0.01,
                "gdp_shock": 0.0,
                "inflation_shock": 0.0,
                "currency_shock": 0.0,
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Sector macro sensitivity benchmark not found"


def test_post_top_down_macro_sensitivity_calculates_duration():
    with _client_with_db() as (client, _db):
        response = client.post(
            "/api/valuation/macro/top-down",
            json={
                "frequency": "annual",
                "periods": [
                    {
                        "period": "2021",
                        "operating_income": 50.0,
                        "market_cap": 80.0,
                        "total_debt": 20.0,
                        "change_in_long_term_bond_rate": 0.0,
                        "gdp_growth": 0.0,
                        "inflation_change": 0.0,
                        "currency_change": 0.0,
                    },
                    {
                        "period": "2022",
                        "operating_income": 49.5,
                        "market_cap": 78.0,
                        "total_debt": 20.0,
                        "change_in_long_term_bond_rate": 0.01,
                        "gdp_growth": 0.0,
                        "inflation_change": 0.0,
                        "currency_change": 0.0,
                    },
                    {
                        "period": "2023",
                        "operating_income": 48.51,
                        "market_cap": 74.08,
                        "total_debt": 20.0,
                        "change_in_long_term_bond_rate": 0.02,
                        "gdp_growth": 0.0,
                        "inflation_change": 0.0,
                        "currency_change": 0.0,
                    },
                    {
                        "period": "2024",
                        "operating_income": 47.0547,
                        "market_cap": 68.4352,
                        "total_debt": 20.0,
                        "change_in_long_term_bond_rate": 0.03,
                        "gdp_growth": 0.0,
                        "inflation_change": 0.0,
                        "currency_change": 0.0,
                    },
                ],
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["method"] == "top_down"
        assert body["data"]["observation_count"] == 3
        assert body["data"]["firm_value"]["duration"] == 2.0
        assert body["data"]["operating_income"]["duration"] == 1.0
        assert body["data"]["confidence_label"] == "low"


def test_post_top_down_macro_sensitivity_rejects_too_few_periods():
    with _client_with_db() as (client, _db):
        response = client.post(
            "/api/valuation/macro/top-down",
            json={
                "frequency": "annual",
                "periods": [
                    {
                        "period": "2023",
                        "operating_income": 50.0,
                        "market_cap": 80.0,
                        "total_debt": 20.0,
                        "change_in_long_term_bond_rate": 0.0,
                        "gdp_growth": 0.0,
                        "inflation_change": 0.0,
                        "currency_change": 0.0,
                    },
                    {
                        "period": "2024",
                        "operating_income": 49.5,
                        "market_cap": 78.0,
                        "total_debt": 20.0,
                        "change_in_long_term_bond_rate": 0.01,
                        "gdp_growth": 0.0,
                        "inflation_change": 0.0,
                        "currency_change": 0.0,
                    },
                ],
            },
        )

        assert response.status_code == 400
        assert "At least 3 periods" in response.json()["detail"]


def test_post_bottom_up_macro_sensitivity_calculates_segment_weighted_exposure():
    with _client_with_db() as (client, db):
        db.add_all(
            [
                SectorMacroSensitivityBenchmark(
                    source_file="macrodur.xls",
                    sic_code="5311",
                    industry_name="Retail",
                    firm_value_duration=3.0,
                    firm_value_cyclicality=-0.3,
                    firm_value_inflation=1.9,
                    firm_value_currency=0.7,
                    operating_income_duration=1.5,
                    operating_income_cyclicality=-0.15,
                    operating_income_inflation=0.95,
                    operating_income_currency=0.35,
                ),
                SectorMacroSensitivityBenchmark(
                    source_file="macrodur.xls",
                    sic_code="3571",
                    industry_name="Hardware",
                    firm_value_duration=1.0,
                    firm_value_cyclicality=1.2,
                    firm_value_inflation=-0.4,
                    firm_value_currency=-0.2,
                    operating_income_duration=0.5,
                    operating_income_cyclicality=0.6,
                    operating_income_inflation=-0.2,
                    operating_income_currency=-0.1,
                ),
            ]
        )
        db.commit()

        response = client.post(
            "/api/valuation/macro/bottom-up",
            json={
                "segments": [
                    {"name": "Retail", "sicCode": "5311", "value": 60.0},
                    {"name": "Hardware", "sicCode": "3571", "value": 40.0},
                ]
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["method"] == "bottom_up"
        assert body["data"]["duration"] == 2.2
        assert body["data"]["cyclicality"] == 0.3
        assert body["data"]["inflation_sensitivity"] == 0.98
        assert body["data"]["currency_sensitivity"] == 0.34
        assert body["data"]["covered_weight"] == 1.0


def test_post_bottom_up_macro_sensitivity_rejects_zero_total_value():
    with _client_with_db() as (client, _db):
        response = client.post(
            "/api/valuation/macro/bottom-up",
            json={"segments": [{"name": "Retail", "sicCode": "5311", "value": 0.0}]},
        )

        assert response.status_code == 400
        assert "Total segment value must be greater than zero" in response.json()["detail"]
