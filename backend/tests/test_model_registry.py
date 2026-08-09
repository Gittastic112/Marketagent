from app.db.base import Base
from app import models  # noqa: F401 - importing models should populate Base.metadata


def test_agentic_intelligence_models_are_registered_for_alembic():
    assert "decision_logs" in Base.metadata.tables
    assert "evidence_ledger" in Base.metadata.tables
    assert "variant_perception" in Base.metadata.tables
    assert "portfolio_benchmark_configs" in Base.metadata.tables
    assert "fx_rate_observations" in Base.metadata.tables
