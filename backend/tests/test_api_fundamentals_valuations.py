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
    assert response.json()["name"] == "Base Model"


def test_create_dcf_assumption_set(client: TestClient, db: Session):
    company = Company(ticker="TEST2", name="Test Co 2")
    db.add(company)
    db.commit()

    vmodel = ValuationModel(company_id=company.id, name="Test")
    db.add(vmodel)
    db.commit()

    response = client.post(f"/valuation-models/{vmodel.id}/assumptions", json={
        "scenario": "Bull",
        "discount_rate": 0.10,
        "terminal_growth_rate": 0.02,
        "projection_years": 5,
        "assumptions_json": {
            "current_fcf": 1000.0,
            "shares_outstanding": 10.0,
            "net_debt": 0.0,
            "fcf_growth_rate": 0.05
        }
    })
    assert response.status_code == 201
    data = response.json()
    assert data["scenario"] == "Bull"
    # Outputs should be generated automatically
    assert len(data["outputs"]) == 1
    assert data["outputs"][0]["enterprise_value"] > 0


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
    assert response.json()["year"] == 2026
    period_id = response.json()["id"]

    response = client.post(f"/financial-periods/{period_id}/metrics", json={
        "metric_name": "Revenue",
        "value": 500.0,
        "unit": "Millions"
    })
    assert response.status_code == 201
    assert response.json()["metric_name"] == "Revenue"
