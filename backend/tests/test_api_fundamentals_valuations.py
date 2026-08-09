from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.company import Company
from app.models.dcf import ValuationModel, DcfAssumptionSet
from helpers import response_data

@pytest.fixture
def db() -> Generator[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db: Session) -> Generator[TestClient]:
    def override_get_db() -> Generator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

def test_create_valuation_model(client: TestClient, db: Session):
    company = Company(ticker="TEST", name="Test Co")
    db.add(company)
    db.commit()

    response = client.post(f"/companies/{company.id}/valuation-models", json={
        "name": "Base Model",
        "description": "Initial setup"
    })
    assert response.status_code == 201
    assert response_data(response)["name"] == "Base Model"


def test_create_dcf_assumption_set(client: TestClient, db: Session):
    company = Company(ticker="TEST2", name="Test Co 2")
    db.add(company)
    db.commit()

    vmodel = ValuationModel(company_id=company.id, name="Test")
    db.add(vmodel)
    db.commit()

    response = client.post(f"/valuation-models/{vmodel.id}/assumptions", json={
        "scenario": "Bull",
        "projection_years_count": 5,
        "starting_revenue": 1000.0,
        "revenue_growth_years_json": {
            "1": 0.08,
            "2": 0.07,
            "3": 0.06,
            "4": 0.05,
            "5": 0.04,
        },
        "current_operating_margin": 0.18,
        "target_operating_margin": 0.22,
        "tax_rate": 0.25,
        "sales_to_capital_ratio": 2.5,
        "starting_invested_capital": 600.0,
        "wacc_start": 0.10,
        "wacc_terminal": 0.09,
        "terminal_growth_rate": 0.02,
        "terminal_roic": 0.12,
        "cash": 100.0,
        "debt": 50.0,
        "diluted_shares": 10.0,
        "current_market_price": 100.0,
    })
    assert response.status_code == 201
    data = response_data(response)
    assert data["scenario"] == "Bull"
    # Outputs should be generated automatically
    assert data["outputs"] is not None
    assert data["outputs"]["enterprise_value"] > 0


def test_create_financial_period(client: TestClient, db: Session):
    company = Company(ticker="TEST3", name="Test Co 3")
    db.add(company)
    db.commit()

    response = client.post(f"/companies/{company.id}/financial-periods", json={
        "period_type": "Q1",
        "year": 2026,
        "quarter": 1,
        "report_date": "2026-04-15",
        "currency": "USD"
    })
    assert response.status_code == 201
    data = response_data(response)
    assert data["year"] == 2026
    assert data["currency_source"] == "manual_entry"
    assert data["currency_confidence"] == "medium"
    period_id = data["id"]

    response = client.post(f"/financial-periods/{period_id}/metrics", json={
        "metric_name": "Revenue",
        "value": 500.0,
        "unit": "Millions"
    })
    assert response.status_code == 201
    assert response_data(response)["metric_name"] == "Revenue"
