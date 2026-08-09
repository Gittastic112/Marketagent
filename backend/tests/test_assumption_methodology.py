import pytest
from app.services.assumption_methodology import AssumptionMethodologyService

def test_fallback_methods(db_session):
    # For a country with no DB records, it should use the fallback methods
    methods = AssumptionMethodologyService.get_available_methods(db_session, "equity_risk_premium", "India")

    assert len(methods) >= 4  # 3 fallbacks + user_custom
    method_keys = [m["method_key"] for m in methods]

    assert "damodaran_implied_erp" in method_keys
    assert "mature_market_plus_crp" in method_keys
    assert "sovereign_spread" in method_keys
    assert "user_custom" in method_keys

def test_default_method(db_session):
    default = AssumptionMethodologyService.get_default_method(db_session, "equity_risk_premium", "India")

    assert default is not None
    assert default["method_key"] == "damodaran_implied_erp"
    assert default["is_default"] is True

def test_build_pack(db_session):
    pack = AssumptionMethodologyService.build_country_assumption_pack(db_session, "India")

    assert "equity_risk_premium" in pack
    assert "risk_free_rate" in pack
    assert "beta" in pack

    assert pack["equity_risk_premium"]["default_method"] == "damodaran_implied_erp"
    assert pack["risk_free_rate"]["default_method"] == "current_government_bond"
    assert pack["beta"]["default_method"] == "user_custom"  # Since no fallback is defined for beta, it falls back to custom
