"""Independent Mock Data cases for dated risk and saved-currency comparisons."""
from datetime import UTC, date, datetime, timedelta
from math import sqrt

import pytest
from sqlalchemy import select

from app.models import Company, DcfAssumptionSet, DcfOutput, FxRateObservation, MarketPrice, Portfolio, PortfolioHolding, ValuationModel
from app.services import portfolio_risk_return
from app.services.portfolio_risk_return import calculate_portfolio_risk_return
from app.services.portfolio_valuation import calculate_portfolio_valuation


AS_OF = date(2026, 8, 9)


def _case(db):
    portfolio = Portfolio(name="Mock Data risk reference", base_currency="USD")
    companies = [Company(ticker=ticker, name="Mock Data", currency="USD") for ticker in ("PAIR1", "PAIR2")]
    db.add_all([portfolio, *companies])
    db.flush()
    # Equal final prices give exact 60/40 weights. The return vectors are
    # [10%, -10%, 20%] and [-10%, 20%, 10%], with correlation -0.5.
    for company, quantity, prices in zip(companies, [3, 2], [[100, 110, 99, 118.8], [100, 90, 108, 118.8]], strict=True):
        db.add(PortfolioHolding(portfolio_id=portfolio.id, company_id=company.id,
            ticker=company.ticker, quantity=quantity, average_cost=100, currency="USD", as_of_date=AS_OF))
        for offset, price in enumerate(prices):
            db.add(MarketPrice(company_id=company.id, ticker=company.ticker, price=price,
                currency="USD", as_of_date=AS_OF - timedelta(days=3 - offset), provider_name="mock_reference"))
    db.commit()
    return portfolio, companies


def test_marginal_risk_matches_independent_two_asset_reference(db):
    portfolio, _ = _case(db)
    result = calculate_portfolio_risk_return(db, portfolio.id, AS_OF, min_observations=2)
    # Sample variances are 7/300, covariance -7/600. With 252 periods,
    # w' covariance w = 1.6464 and covariance-with-portfolio = [2.352, .588].
    volatility = sqrt(1.6464)
    assert result["portfolio_volatility_annualized"] == pytest.approx(volatility)
    for row, weight, covariance in zip(result["holdings"], [.6, .4], [2.352, .588], strict=True):
        assert row["portfolio_weight_decimal"] == pytest.approx(weight)
        assert row["marginal_volatility"] == pytest.approx(covariance / volatility)
        assert row["component_risk"] == pytest.approx(weight * covariance / volatility)
        assert row["marginal_volatility_for_one_percent"] == pytest.approx(.01 * covariance / volatility)
    assert result["risk_reconciliation_error"] == pytest.approx(0, abs=1e-12)


def test_returns_with_different_start_dates_are_not_aligned(db):
    portfolio, companies = _case(db)
    missing = db.scalar(select(MarketPrice).where(MarketPrice.company_id == companies[1].id,
        MarketPrice.as_of_date == AS_OF - timedelta(days=2)))
    db.delete(missing)
    db.commit()
    result = calculate_portfolio_risk_return(db, portfolio.id, AS_OF, min_observations=2)
    assert result["portfolio_volatility_annualized"] is None
    assert result["risk_calculation_status"] == "not_available"
    assert any("Only 1 aligned return" in item for item in result["blockers"])


def test_missing_interior_fx_does_not_join_nonadjacent_observations(db):
    portfolio, companies = _case(db)
    price = db.scalar(select(MarketPrice).where(MarketPrice.company_id == companies[1].id,
        MarketPrice.as_of_date == AS_OF - timedelta(days=2)))
    price.currency = "EUR"  # No EUR/USD observation exists for this record.
    db.commit()
    result = calculate_portfolio_risk_return(db, portfolio.id, AS_OF, min_observations=2)
    second = result["holdings"][1]
    assert second["observation_count"] == 1
    assert second["marginal_volatility"] is None
    assert any("Missing FX" in warning for warning in second["warnings"])
    assert result["risk_calculation_status"] == "partial"


def test_stale_fx_keeps_current_risk_partial(db, monkeypatch):
    class RecordedDate(date):
        @classmethod
        def today(cls):
            return AS_OF

    monkeypatch.setattr(portfolio_risk_return, "date", RecordedDate)
    portfolio, _ = _case(db)
    for price in db.scalars(select(MarketPrice)):
        price.currency = "EUR"
    db.add(FxRateObservation(base_currency="EUR", quote_currency="USD", rate=1.1,
        as_of_date=AS_OF - timedelta(days=20), provider_name="mock_reference"))
    db.commit()
    result = calculate_portfolio_risk_return(db, portfolio.id, min_observations=2)
    assert result["risk_calculation_status"] == "partial"
    assert result["portfolio_volatility_annualized"] is not None
    assert any("stale price/FX" in warning for warning in result["warnings"])


@pytest.mark.parametrize("consumer", ["risk", "valuation"])
@pytest.mark.parametrize("currency,quality,intrinsic,available", [
    ("USD", 85, 142.56, True),
    ("EUR", 85, 142.56, False),
    (None, 85, 142.56, False),
    ("USD", float("inf"), 142.56, False),
    ("USD", 85, float("inf"), False),
])
def test_dcf_comparison_requires_explicit_saved_currency_and_finite_values(db, consumer, currency, quality, intrinsic, available):
    portfolio, companies = _case(db)
    recorded_at = datetime(2026, 8, 9, 12, tzinfo=UTC)
    model = ValuationModel(company_id=companies[0].id, name="Mock Data")
    db.add(model)
    db.flush()
    saved = DcfAssumptionSet(valuation_model_id=model.id, scenario="Base", cash_flow_currency=currency,
        created_at=recorded_at)
    db.add(saved)
    db.flush()
    output = DcfOutput(assumption_set_id=saved.id, intrinsic_value_per_share=intrinsic,
        model_quality_score=quality, warnings_json=[], created_at=recorded_at)
    db.add(output)
    db.commit()
    if consumer == "risk":
        result = calculate_portfolio_risk_return(db, portfolio.id, AS_OF, min_observations=2)
        gap = result["holdings"][0]["expected_return_decimal"]
    else:
        result = calculate_portfolio_valuation(db, portfolio.id, AS_OF)
        gap = result["holdings"][0]["expected_return"]
    if available:
        assert gap == pytest.approx(.2)
    else:
        assert gap is None
    # Neither consumer changes the saved result or its input basis.
    db.refresh(saved)
    db.refresh(output)
    assert saved.cash_flow_currency == currency
    assert output.intrinsic_value_per_share == intrinsic


def test_portfolio_overview_withholds_gap_for_stale_price(db):
    portfolio, companies = _case(db)
    model = ValuationModel(company_id=companies[0].id, name="Mock Data")
    db.add(model)
    db.flush()
    saved = DcfAssumptionSet(valuation_model_id=model.id, scenario="Base", cash_flow_currency="USD",
        created_at=datetime(2026, 8, 9, tzinfo=UTC))
    db.add(saved)
    db.flush()
    db.add(DcfOutput(assumption_set_id=saved.id, intrinsic_value_per_share=142.56,
        model_quality_score=85, warnings_json=[], created_at=datetime(2026, 8, 9, tzinfo=UTC)))
    db.commit()
    row = calculate_portfolio_valuation(db, portfolio.id, AS_OF + timedelta(days=8))["holdings"][0]
    assert row["is_stale_price"] is True
    assert row["expected_return"] is None
    assert row["intrinsic_value"] == pytest.approx(142.56)
