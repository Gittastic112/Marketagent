import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.company import Company
from app.models.dcf import ValuationModel, DcfAssumptionSet
from app.services.dcf import calculate_dcf
from app.services.memo_writer import ValuationMemoAgent


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_full_valuation_and_memo_cycle(db_session, monkeypatch):
    # Ensure we use MockAIProvider
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "1")

    # 1. Setup Data
    company = Company(name="Test Corp", ticker="TEST")
    db_session.add(company)
    db_session.commit()

    valuation = ValuationModel(company_id=company.id, name="Test Valuation", model_type="dcf")
    db_session.add(valuation)
    db_session.commit()

    assumption_set = DcfAssumptionSet(
        valuation_model_id=valuation.id,
        scenario="Base",
        starting_revenue=1000.0,
        current_operating_margin=0.10,
        target_operating_margin=0.15,
        tax_rate=0.25,
        sales_to_capital_ratio=2.0,
        revenue_growth_years_json={"1": 0.10, "2": 0.10},
        projection_years_count=2,
        wacc_start=0.10,
        wacc_terminal=0.08,
        terminal_growth_rate=0.02,
        terminal_roic=0.10,
        cash=100.0,
        debt=200.0,
        diluted_shares=100.0,
        current_market_price=10.0
    )
    db_session.add(assumption_set)
    db_session.commit()

    # 2. Run DCF Math
    output, projection_years, _ = calculate_dcf(assumption_set)

    assert output is not None
    assert output.enterprise_value > 0
    assert output.intrinsic_value_per_share > 0

    # 3. Generate Memo (Integration with Mocked AI)
    memo_agent = ValuationMemoAgent(db=db_session)
    memo = memo_agent.generate_memo(
        company=company,
        valuation=valuation,
        assumption_set=assumption_set,
        output=output
    )

    # Mock provider returns "Mock AI output" by default, or similar.
    assert memo is not None
    assert len(memo) > 0

    # Check that AiOutput was saved
    from app.models.ai import AiOutput
    ai_outputs = db_session.query(AiOutput).all()
    assert len(ai_outputs) == 1
    assert ai_outputs[0].reference_type == "dcf_assumption_set"
    assert ai_outputs[0].reference_id == assumption_set.id
    assert ai_outputs[0].provider_name == "mock"
    assert ai_outputs[0].is_mock is True
    assert ai_outputs[0].execution_status == "success"
    assert ai_outputs[0].transmission_scope == "none"
