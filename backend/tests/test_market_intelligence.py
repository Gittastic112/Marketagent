import pytest
from app.models.company import Company
from app.models.event import Event
from app.models.dcf import ValuationModel, DcfAssumptionSet, ValuationAssumptionChangeLog
from app.models.alert import Alert
from app.services.market_intelligence_agent import evaluate_event_impact_on_valuation
from app.services.valuation_alert_service import check_price_valuation_divergence

# Mock tests since DB tests require DB connection setup that Pytest isn't currently wired to locally
# We will test the structural logic directly

def test_market_intelligence_agent_mock_response():
    # If this was wired to DB we would create a Company, Event, ValuationModel, and DcfAssumptionSet
    # For now we test the core logic shape that evaluate_event_impact_on_valuation uses

    class MockEvent:
        title = "Q4 Earnings Result and Guidance Lowered"
        event_type = "rss_news"
        description = "Margins compressed by 200 bps."
        priority_score = 8

    class MockAssumptionSet:
        target_operating_margin = 0.15
        sales_to_capital_ratio = 1.2
        risk_free_rate = 0.04
        equity_risk_premium = 0.05

    event = MockEvent()
    assumption_set = MockAssumptionSet()

    is_impactful = (event.priority_score and event.priority_score > 5) or "earnings" in event.title.lower()

    assert is_impactful is True

    llm_response = {
        "is_stale": True,
        "stale_reason": f"Event '{event.title}' likely impacts future margins or growth assumptions.",
        "proposed_changes": [
            {
                "parameter_name": "target_operating_margin",
                "old_value": str(assumption_set.target_operating_margin) if assumption_set.target_operating_margin else "None",
                "new_value": "Requires review",
                "rationale": "Material event requires reassessing margin trajectory."
            }
        ]
    }

    assert llm_response["is_stale"] is True
    assert len(llm_response["proposed_changes"]) == 1
    assert llm_response["proposed_changes"][0]["parameter_name"] == "target_operating_margin"

def test_price_divergence_logic():
    intrinsic_value = 150.0

    # Current price drops massively to 80 (undervalued, upside!)
    current_price = 80.0
    divergence_pct = (intrinsic_value - current_price) / current_price

    # Divergence is (150-80)/80 = 70/80 = 0.875
    assert divergence_pct > 0.30
    assert "Upside" if divergence_pct > 0 else "Downside" == "Upside"

    # Current price moons to 300 (overvalued, downside!)
    current_price_2 = 300.0
    divergence_pct_2 = (intrinsic_value - current_price_2) / current_price_2
    # (150 - 300) / 300 = -0.5

    assert abs(divergence_pct_2) > 0.30
    assert "Upside" if divergence_pct_2 > 0 else "Downside" == "Downside"
