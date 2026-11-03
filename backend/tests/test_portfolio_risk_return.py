from datetime import UTC, date, datetime, timedelta

import pytest

from app.models import (
    Company,
    DcfAssumptionSet,
    DcfOutput,
    FxRateObservation,
    MarketPrice,
    Portfolio,
    PortfolioHolding,
    ValuationModel,
)
from app.services.portfolio_risk_return import calculate_portfolio_risk_return


AS_OF = date(2026, 8, 9)


def _company(ticker: str) -> Company:
    return Company(
        ticker=ticker,
        name=f"{ticker} Company",
        market="US",
        primary_exchange="NASDAQ",
        local_symbol=ticker,
        currency="USD",
    )


def _add_price_series(db, company: Company, values: list[float], currency: str = "USD") -> None:
    for offset, value in enumerate(values):
        db.add(
            MarketPrice(
                company_id=company.id,
                ticker=company.ticker,
                price=value,
                currency=currency,
                as_of_date=date(2026, 8, 5 + offset),
                provider_name="test",
            )
        )


def _add_dated_price_series(
    db,
    company: Company,
    values: list[float],
    *,
    start_date: date,
    currency: str,
) -> None:
    for offset, value in enumerate(values):
        db.add(
            MarketPrice(
                company_id=company.id,
                ticker=company.ticker,
                price=value,
                currency=currency,
                as_of_date=start_date + timedelta(days=offset),
                provider_name="e2e_mock_fixture",
                warnings_json=["Mock Data used only for deterministic portfolio validation."],
            )
        )


def test_risk_model_reconciles_component_risk_to_portfolio_volatility(db):
    first = _company("AAA")
    second = _company("BBB")
    portfolio = Portfolio(name="Risk", base_currency="USD")
    db.add_all([first, second, portfolio])
    db.flush()
    db.add_all(
        [
            PortfolioHolding(portfolio_id=portfolio.id, company_id=first.id, ticker="AAA", quantity=6, average_cost=100, currency="USD", as_of_date=AS_OF),
            PortfolioHolding(portfolio_id=portfolio.id, company_id=second.id, ticker="BBB", quantity=4, average_cost=100, currency="USD", as_of_date=AS_OF),
        ]
    )
    _add_price_series(db, first, [100, 102, 101, 104, 106])
    _add_price_series(db, second, [100, 99, 101, 100, 103])
    db.commit()

    result = calculate_portfolio_risk_return(db, portfolio.id, AS_OF, lookback_days=30, min_observations=3)

    assert result["risk_calculation_status"] == "partial"
    assert "NO_RECORDED_ACTIVITY" in result["blockers"]
    assert result["portfolio_volatility_annualized"] > 0
    components = [row["component_risk"] for row in result["holdings"]]
    assert sum(value for value in components if value is not None) == pytest.approx(
        result["portfolio_volatility_annualized"]
    )
    assert result["risk_reconciliation_error"] == pytest.approx(0, abs=1e-12)
    assert all(row["aligned_observation_count"] == 4 for row in result["holdings"])


def test_risk_model_reports_insufficient_history_without_inventing_values(db):
    company = _company("SHORT")
    portfolio = Portfolio(name="Short history", base_currency="USD")
    db.add_all([company, portfolio])
    db.flush()
    db.add(PortfolioHolding(portfolio_id=portfolio.id, company_id=company.id, ticker="SHORT", quantity=1, average_cost=10, currency="USD", as_of_date=AS_OF))
    _add_price_series(db, company, [10, 11])
    db.commit()

    result = calculate_portfolio_risk_return(db, portfolio.id, AS_OF, lookback_days=30, min_observations=3)

    assert result["risk_calculation_status"] == "not_available"
    assert result["portfolio_volatility_annualized"] is None
    assert "SHORT has 1 return observations; 3 are required." in result["blockers"]


def test_risk_model_uses_dated_fx_and_exposes_source_ids(db):
    company = _company("EURCO")
    portfolio = Portfolio(name="FX Risk", base_currency="USD")
    db.add_all([company, portfolio])
    db.flush()
    db.add(PortfolioHolding(portfolio_id=portfolio.id, company_id=company.id, ticker="EURCO", quantity=1, average_cost=90, currency="EUR", as_of_date=AS_OF))
    _add_price_series(db, company, [90, 91, 93, 92, 95], currency="EUR")
    for offset, rate in enumerate([1.10, 1.11, 1.09, 1.12, 1.13]):
        db.add(FxRateObservation(base_currency="EUR", quote_currency="USD", rate=rate, as_of_date=date(2026, 8, 5 + offset), provider_name="test"))
    db.commit()

    result = calculate_portfolio_risk_return(db, portfolio.id, AS_OF, lookback_days=30, min_observations=3)

    assert result["risk_calculation_status"] == "partial"
    assert len(result["source_fx_observation_ids"]) == 5
    assert len(result["holdings"][0]["source_fx_observation_ids"]) == 5


def test_expected_return_is_a_trust_gated_dcf_valuation_gap(db):
    company = _company("DCF")
    portfolio = Portfolio(name="Expected return", base_currency="USD")
    db.add_all([company, portfolio])
    db.flush()
    db.add(PortfolioHolding(portfolio_id=portfolio.id, company_id=company.id, ticker="DCF", quantity=1, average_cost=100, currency="USD", as_of_date=AS_OF))
    _add_price_series(db, company, [96, 98, 99, 101, 100])
    model = ValuationModel(company_id=company.id, name="DCF", model_type="fcff_dcf")
    db.add(model)
    db.flush()
    assumptions = DcfAssumptionSet(valuation_model_id=model.id, scenario="Base", is_stale=False, cash_flow_currency="USD")
    db.add(assumptions)
    db.flush()
    output = DcfOutput(
        assumption_set_id=assumptions.id,
        intrinsic_value_per_share=120,
        current_market_price=100,
        model_quality_score=85,
        warnings_json=[],
        created_at=datetime(2026, 8, 9, 12, tzinfo=UTC),
    )
    db.add(output)
    db.commit()

    result = calculate_portfolio_risk_return(db, portfolio.id, AS_OF, lookback_days=30, min_observations=3)

    row = result["holdings"][0]
    assert row["expected_return_decimal"] == pytest.approx(0.20)
    assert row["expected_return_kind"] == "dcf_valuation_gap_not_annualized"
    assert row["expected_return_claim_type"] == "Estimate"
    assert row["source_dcf_output_id"] == output.id
    assert result["portfolio_expected_return_decimal"] == pytest.approx(0.20)
    assert result["expected_return_calculation_status"] == "partial"

    stale = calculate_portfolio_risk_return(db, portfolio.id, AS_OF + timedelta(days=6), lookback_days=30, min_observations=3)
    assert stale["risk_calculation_status"] == "partial"
    assert stale["holdings"][0]["price_age_days"] == 6
    assert stale["holdings"][0]["is_stale_price"] is True
    assert stale["holdings"][0]["latest_market_price_as_of"] == AS_OF
    assert stale["holdings"][0]["expected_return_decimal"] is None
    assert stale["portfolio_expected_return_decimal"] is None
    assert stale["portfolio_volatility_annualized"] is not None


def test_risk_internal_call_is_bound_to_portfolio_owner(db):
    company = _company("PRIVATE")
    portfolio = Portfolio(user_id="owner", name="Private risk", base_currency="USD")
    db.add_all([company, portfolio])
    db.flush()
    db.add(PortfolioHolding(portfolio_id=portfolio.id, company_id=company.id, ticker="PRIVATE", quantity=1, average_cost=100, currency="USD", as_of_date=AS_OF))
    _add_price_series(db, company, [96, 98, 99, 101, 100])
    model = ValuationModel(user_id="other-owner", company_id=company.id, name="Not ours", model_type="fcff_dcf")
    db.add(model)
    db.flush()
    assumptions = DcfAssumptionSet(valuation_model_id=model.id, scenario="Base", is_stale=False)
    db.add(assumptions)
    db.flush()
    db.add(DcfOutput(assumption_set_id=assumptions.id, intrinsic_value_per_share=999,
                     model_quality_score=90, warnings_json=[], created_at=datetime(2026, 8, 9, 12, tzinfo=UTC)))
    db.commit()
    result = calculate_portfolio_risk_return(db, portfolio.id, AS_OF, lookback_days=30, min_observations=3)
    assert result["source_dcf_output_ids"] == []
    assert result["holdings"][0]["expected_return_decimal"] is None
    with pytest.raises(ValueError, match="not found"):
        calculate_portfolio_risk_return(db, portfolio.id, AS_OF, user_id="other-owner")


def test_expected_return_rejects_stale_or_low_quality_dcf_output(db):
    company = _company("STALE")
    portfolio = Portfolio(name="Untrusted DCF", base_currency="USD")
    db.add_all([company, portfolio])
    db.flush()
    db.add(PortfolioHolding(portfolio_id=portfolio.id, company_id=company.id, ticker="STALE", quantity=1, average_cost=100, currency="USD", as_of_date=AS_OF))
    _add_price_series(db, company, [96, 98, 99, 101, 100])
    model = ValuationModel(company_id=company.id, name="DCF", model_type="fcff_dcf")
    db.add(model)
    db.flush()
    assumptions = DcfAssumptionSet(valuation_model_id=model.id, scenario="Base", is_stale=True, stale_reason="New filing")
    db.add(assumptions)
    db.flush()
    db.add(DcfOutput(
        assumption_set_id=assumptions.id,
        intrinsic_value_per_share=130,
        model_quality_score=40,
        warnings_json=[],
        created_at=datetime(2026, 8, 9, 12, tzinfo=UTC),
    ))
    db.commit()

    result = calculate_portfolio_risk_return(db, portfolio.id, AS_OF, lookback_days=30, min_observations=3)

    row = result["holdings"][0]
    assert row["expected_return_decimal"] is None
    assert row["expected_return_claim_type"] == "Unavailable"
    assert result["expected_return_calculation_status"] == "not_available"
    assert any("stale" in warning.lower() for warning in row["warnings"])


def test_expected_return_does_not_add_currency_noise_when_price_is_missing(db):
    company = _company("NOPRICE")
    portfolio = Portfolio(name="No price", base_currency="USD")
    db.add_all([company, portfolio])
    db.flush()
    db.add(PortfolioHolding(
        portfolio_id=portfolio.id,
        company_id=company.id,
        ticker="NOPRICE",
        quantity=1,
        average_cost=100,
        currency="USD",
        as_of_date=AS_OF,
    ))
    model = ValuationModel(company_id=company.id, name="DCF", model_type="fcff_dcf")
    db.add(model)
    db.flush()
    assumptions = DcfAssumptionSet(valuation_model_id=model.id, scenario="Base", is_stale=False)
    db.add(assumptions)
    db.flush()
    db.add(DcfOutput(
        assumption_set_id=assumptions.id,
        intrinsic_value_per_share=120,
        model_quality_score=85,
        warnings_json=[],
        created_at=datetime(2026, 8, 9, 12, tzinfo=UTC),
    ))
    db.commit()

    result = calculate_portfolio_risk_return(
        db,
        portfolio.id,
        AS_OF,
        lookback_days=30,
        min_observations=3,
    )

    warnings = result["holdings"][0]["warnings"]
    assert "No positive source-backed market price is available for comparison." in warnings
    assert not any("currency" in warning.lower() for warning in warnings)


def test_multicurrency_runtime_gate_has_complete_risk_and_dcf_coverage(db):
    start = date(2026, 7, 20)
    as_of = start + timedelta(days=21)
    usd_company = _company("E2EUSD")
    eur_company = _company("E2EEUR")
    eur_company.market = "DE"
    eur_company.primary_exchange = "XETRA"
    eur_company.currency = "EUR"
    portfolio = Portfolio(
        name="Mock Data Multi-Currency Portfolio",
        base_currency="USD",
        description="Mock Data used only for deterministic portfolio validation.",
    )
    db.add_all([usd_company, eur_company, portfolio])
    db.flush()
    db.add_all([
        PortfolioHolding(
            portfolio_id=portfolio.id,
            company_id=usd_company.id,
            ticker=usd_company.ticker,
            quantity=10,
            average_cost=95,
            currency="USD",
            as_of_date=start,
        ),
        PortfolioHolding(
            portfolio_id=portfolio.id,
            company_id=eur_company.id,
            ticker=eur_company.ticker,
            quantity=5,
            average_cost=75,
            currency="EUR",
            as_of_date=start,
        ),
    ])
    usd_prices = [100 + offset * 0.45 + (offset % 3) * 0.1 for offset in range(22)]
    eur_prices = [80 + offset * 0.35 + (offset % 4) * 0.08 for offset in range(22)]
    _add_dated_price_series(db, usd_company, usd_prices, start_date=start, currency="USD")
    _add_dated_price_series(db, eur_company, eur_prices, start_date=start, currency="EUR")
    for offset in range(22):
        db.add(FxRateObservation(
            base_currency="EUR",
            quote_currency="USD",
            rate=1.10 + offset * 0.002,
            as_of_date=start + timedelta(days=offset),
            provider_name="e2e_mock_fixture",
            source_url="https://example.invalid/mock-data/eur-usd",
        ))
    for company, intrinsic_value in ((usd_company, 125), (eur_company, 105)):
        model = ValuationModel(
            company_id=company.id,
            name=f"{company.ticker} Mock Data Base DCF",
            model_type="fcff_dcf",
        )
        db.add(model)
        db.flush()
        assumptions = DcfAssumptionSet(
            valuation_model_id=model.id,
            scenario="Base",
            is_stale=False,
            cash_flow_currency=company.currency,
        )
        db.add(assumptions)
        db.flush()
        db.add(DcfOutput(
            assumption_set_id=assumptions.id,
            intrinsic_value_per_share=intrinsic_value,
            model_quality_score=90,
            warnings_json=[],
            created_at=datetime.combine(as_of, datetime.min.time(), tzinfo=UTC),
        ))
    db.commit()

    result = calculate_portfolio_risk_return(
        db,
        portfolio.id,
        as_of,
        lookback_days=30,
        min_observations=20,
    )

    assert result["calculation_status"] == "partial"
    assert result["risk_calculation_status"] == "partial"
    assert result["expected_return_calculation_status"] == "partial"
    assert "NO_RECORDED_ACTIVITY" in result["blockers"]
    assert result["risk_covered_weight_percent"] == pytest.approx(100)
    assert result["expected_return_coverage_percent"] == pytest.approx(100)
    assert result["risk_reconciliation_error"] == pytest.approx(0, abs=1e-12)
    assert len(result["source_market_price_ids"]) == 44
    assert len(result["source_fx_observation_ids"]) == 22
    assert len(result["source_dcf_output_ids"]) == 2
    assert result["contains_mock_data"] is True
    assert all(row["aligned_observation_count"] == 21 for row in result["holdings"])
    assert all(row["expected_return_claim_type"] == "Estimate" for row in result["holdings"])
