from datetime import date

from sqlalchemy import select

from app.models import Alert, Company, DcfAssumptionSet, DcfOutput, MarketPrice, Portfolio, PortfolioHolding, User, ValuationModel
from app.services.valuation_alert_service import check_price_valuation_divergence


def test_divergence_is_owner_scoped_and_links_only_owned_portfolios(db):
    company = Company(ticker="OWN", name="Mock Data", currency="USD")
    db.add_all([company, User(id="other-owner", email="other@example.invalid")]);db.flush()
    for user_id, intrinsic in [("admin_user_id_fallback", 150), ("other-owner", 200)]:
        portfolio=Portfolio(name="Mock Data", user_id=user_id)
        model=ValuationModel(company_id=company.id, name="Mock Data", model_type="fcff_dcf", user_id=user_id)
        db.add_all([portfolio,model]);db.flush()
        assumption=DcfAssumptionSet(valuation_model_id=model.id,scenario="Base",cash_flow_currency="USD")
        db.add(assumption);db.flush()
        db.add_all([DcfOutput(assumption_set_id=assumption.id,intrinsic_value_per_share=intrinsic,model_quality_score=90,warnings_json=[]),
            PortfolioHolding(portfolio_id=portfolio.id,company_id=company.id,ticker="OWN",quantity=1,average_cost=100,currency="USD",as_of_date=date.today())])
    db.add(MarketPrice(company_id=company.id,ticker="OWN",price=100,currency="USD",as_of_date=date.today()))
    db.commit()
    alerts=check_price_valuation_divergence(db,company.id,user_id="admin_user_id_fallback")
    assert len(alerts)==1 and alerts[0].user_id=="admin_user_id_fallback"
    assert "150.00" in alerts[0].summary and "200.00" not in alerts[0].summary
    assert all(impact.portfolio.user_id=="admin_user_id_fallback" for impact in alerts[0].portfolio_impacts)
    assert len(alerts[0].portfolio_impacts)==1
    assert check_price_valuation_divergence(db,company.id,user_id="admin_user_id_fallback")==[]
    assert len(check_price_valuation_divergence(db,company.id,user_id="other-owner"))==1
    assert db.query(Alert).count()==2


def test_divergence_without_owner_cannot_read_private_models(db):
    assert check_price_valuation_divergence(db,1)==[]
