from datetime import UTC, date, datetime, timedelta

from app.models import (
    Company,
    DcfAssumptionSet,
    DcfOutput,
    FxRateObservation,
    MarketPrice,
    Portfolio,
    PortfolioBenchmarkConfig,
    PortfolioHolding,
    PortfolioCashBalance,
    PortfolioTransaction,
    PortfolioSnapshot,
    User,
    ValuationModel,
)
from app.services.portfolio_real_input_readiness import audit_portfolio_real_input_readiness
from app.services.portfolio_analytics import record_daily_snapshot


START = date(2026, 7, 20)
END = START + timedelta(days=21)


def _complete_snapshot(
    portfolio_id: int,
    holding_id: int,
    snapshot_date: date,
    price_id: int,
    fx_id: int,
) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        portfolio_id=portfolio_id,
        snapshot_date=snapshot_date,
        total_market_value=500,
        total_cost_basis=450,
        total_cash=50,
        total_portfolio_value=550,
        base_currency="USD",
        calculation_status="complete",
        holdings_count=1,
        priced_holdings_count=1,
        missing_price_tickers_json=[],
        missing_fx_pairs_json=[],
        payload_json={
            "holdings": [
                {
                    "holding_id": holding_id,
                    "ticker": "REALFX",
                    "market_price_id": price_id,
                    "market_price_provider": "manual_verified",
                    "market_fx_observation_id": fx_id,
                }
            ]
        },
    )


def _real_input_portfolio(db) -> tuple[Portfolio, list[MarketPrice]]:
    holding_company = Company(
        ticker="REALFX",
        local_symbol="REALFX",
        name="Real Foreign Holding",
        market="DE",
        primary_exchange="XETRA",
        currency="EUR",
    )
    benchmark_company = Company(
        ticker="REALBMK",
        local_symbol="REALBMK",
        name="Real Benchmark",
        market="US",
        primary_exchange="NYSE",
        currency="USD",
    )
    portfolio = Portfolio(
        name="Source Labeled Portfolio",
        base_currency="USD",
        description="Manually verified portfolio inputs.",
    )
    db.add_all([holding_company, benchmark_company, portfolio])
    db.flush()
    holding = PortfolioHolding(
        portfolio_id=portfolio.id,
        company_id=holding_company.id,
        ticker=holding_company.ticker,
        quantity=5,
        average_cost=75,
        currency="EUR",
        as_of_date=START,
    )
    db.add(holding)
    db.flush()

    prices: list[MarketPrice] = []
    fx_rows: list[FxRateObservation] = []
    for offset in range(22):
        observation_date = START + timedelta(days=offset)
        price = MarketPrice(
            company_id=holding_company.id,
            ticker=holding_company.ticker,
            price=80 + offset,
            currency="EUR",
            as_of_date=observation_date,
            provider_name="manual_verified",
            price_type="manual_close",
            source_timestamp=datetime.combine(observation_date, datetime.min.time(), tzinfo=UTC),
        )
        fx = FxRateObservation(
            base_currency="EUR",
            quote_currency="USD",
            rate=1.10 + offset * 0.001,
            as_of_date=observation_date,
            provider_name="manual_verified",
            provider_symbol="EURUSD",
            source_url="https://data.example.com/eur-usd",
            source_timestamp=datetime.combine(observation_date, datetime.min.time(), tzinfo=UTC),
        )
        db.add_all([price, fx])
        prices.append(price)
        fx_rows.append(fx)

    benchmark_prices = []
    for observation_date, value in ((START, 100), (END, 112)):
        price = MarketPrice(
            company_id=benchmark_company.id,
            ticker=benchmark_company.ticker,
            price=value,
            currency="USD",
            as_of_date=observation_date,
            provider_name="manual_verified",
            price_type="manual_close",
            source_timestamp=datetime.combine(observation_date, datetime.min.time(), tzinfo=UTC),
        )
        db.add(price)
        benchmark_prices.append(price)
    db.flush()

    db.add_all(
        [
            PortfolioBenchmarkConfig(
                portfolio_id=portfolio.id,
                benchmark_company_id=benchmark_company.id,
                ticker=benchmark_company.ticker,
                currency="USD",
                provider_name="manual_verified",
                provider_symbol=benchmark_company.ticker,
                effective_from=START,
                active=True,
                notes="User-selected price-return benchmark.",
            ),
            PortfolioTransaction(portfolio_id=portfolio.id, ticker="CASH", transaction_type="deposit", quantity=425, price=0, fees=0, currency="EUR", transaction_date=START),
            PortfolioTransaction(portfolio_id=portfolio.id, company_id=holding_company.id, ticker=holding_company.ticker, transaction_type="buy", quantity=5, price=75, fees=0, currency="EUR", transaction_date=START),
            PortfolioCashBalance(portfolio_id=portfolio.id, currency="EUR", amount=50, as_of_date=START),
        ]
    )

    model = ValuationModel(
        company_id=holding_company.id,
        name="Reviewed Base DCF",
        description="Reviewed user valuation.",
        model_type="fcff_dcf",
    )
    db.add(model)
    db.flush()
    assumptions = DcfAssumptionSet(
        valuation_model_id=model.id,
        scenario="Base",
        is_stale=False,
        cash_flow_currency=holding_company.currency,
    )
    db.add(assumptions)
    db.flush()
    db.add(
        DcfOutput(
            assumption_set_id=assumptions.id,
            intrinsic_value_per_share=125,
            model_quality_score=90,
            warnings_json=[],
            created_at=datetime.combine(END, datetime.min.time(), tzinfo=UTC),
        )
    )
    db.commit()
    # Isolated simulated inputs exercise the readiness contract, not genuine-input acceptance.
    record_daily_snapshot(db, portfolio.id, START)
    record_daily_snapshot(db, portfolio.id, END)
    return portfolio, prices


def test_real_input_readiness_passes_complete_source_labeled_portfolio(db) -> None:
    portfolio, _ = _real_input_portfolio(db)

    report = audit_portfolio_real_input_readiness(
        db,
        portfolio.id,
        user_id=portfolio.user_id,
        min_observations=20,
    )

    assert report["certification_status"] == "ready"
    assert report["claim_type"] == "Calculation"
    assert report["contains_mock_data"] is False
    assert report["start_date"] == START
    assert report["end_date"] == END
    assert report["blockers"] == []
    assert all(check["status"] == "passed" for check in report["checks"])
    assert len(report["source_snapshot_ids"]) == 2
    assert len(report["source_market_price_ids"]) == 24
    assert len(report["source_fx_observation_ids"]) == 22
    assert len(report["source_dcf_output_ids"]) == 1


def test_real_input_readiness_rejects_mock_contamination(db) -> None:
    portfolio, prices = _real_input_portfolio(db)
    prices[0].provider_name = "e2e_mock_fixture"
    prices[0].price_type = "Mock Data"
    db.commit()

    report = audit_portfolio_real_input_readiness(
        db,
        portfolio.id,
        user_id=portfolio.user_id,
    )

    assert report["certification_status"] == "blocked"
    assert report["contains_mock_data"] is True
    mock_check = next(check for check in report["checks"] if check["code"] == "no_mock_data")
    assert mock_check["status"] == "blocked"
    assert "Mock Data" in mock_check["message"]


def test_real_input_readiness_reports_actionable_empty_portfolio_blockers(db) -> None:
    portfolio = Portfolio(name="Empty", base_currency="USD")
    db.add(portfolio)
    db.commit()

    report = audit_portfolio_real_input_readiness(
        db,
        portfolio.id,
        user_id=portfolio.user_id,
    )

    assert report["certification_status"] == "blocked"
    assert report["start_date"] is None
    assert report["end_date"] is None
    assert "Add at least one positive-quantity holding." in report["blockers"]
    assert "Capture at least two complete point-in-time snapshots." in report["blockers"]
    assert report["source_market_price_ids"] == []


def test_real_input_readiness_endpoint_is_owned_and_source_labeled(client, db) -> None:
    portfolio, _ = _real_input_portfolio(db)

    response = client.get(f"/portfolios/{portfolio.id}/real-input-readiness")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data"]["certification_status"] == "ready"
    assert body["data"]["contains_mock_data"] is False
    assert body["meta"]["source"] == "persisted_portfolio_inputs"
    assert body["meta"]["is_mock"] is False
    assert body["meta"]["is_stale"] is False
    assert body["meta"]["confidence"] == "high"


def test_real_input_readiness_endpoint_returns_blockers_without_partial_or_stale_labels(client, db) -> None:
    portfolio = Portfolio(name="Needs setup", base_currency="USD")
    db.add(portfolio)
    db.commit()

    response = client.get(f"/portfolios/{portfolio.id}/real-input-readiness")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data"]["certification_status"] == "blocked"
    assert body["data"]["blockers"]
    assert body["meta"]["is_stale"] is False
    assert body["meta"]["status"] == "success"


def test_real_input_readiness_endpoint_rejects_cross_owner_access(client, db) -> None:
    other = User(id="other-readiness-user", email="other-readiness@example.com", name="Other")
    private = Portfolio(user_id=other.id, name="Private inputs", base_currency="USD")
    db.add_all([other, private])
    db.commit()

    response = client.get(f"/portfolios/{private.id}/real-input-readiness")

    assert response.status_code == 404
