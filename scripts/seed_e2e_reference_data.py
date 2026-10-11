"""Seed deterministic Mock Data used only by the isolated browser test stack."""

from datetime import UTC, date, datetime, timedelta

from app.db.session import SessionLocal
from app.models import (
    Company,
    DamodaranDatasetFile,
    DamodaranMarginBenchmark,
    DcfAssumptionSet,
    DcfOutput,
    FxRateObservation,
    MarketPrice,
    Portfolio,
    PortfolioBenchmarkConfig,
    PortfolioHolding,
    PortfolioSnapshot,
    PortfolioTransaction,
    User,
    ValuationModel,
)


DATASET_CODE = "e2e_margin_fixture"
E2E_USER_ID = "local-user"
PORTFOLIO_NAME = "Mock Data Multi-Currency Portfolio"
START_DATE = date(2026, 7, 20)
END_DATE = START_DATE + timedelta(days=21)


def _ensure_margin_fixture(db) -> None:
    existing = db.query(DamodaranDatasetFile).filter_by(dataset_code=DATASET_CODE).first()
    if existing is not None:
        return

    dataset = DamodaranDatasetFile(
        uploaded_filename="mock-data-e2e-margin-fixture.xlsx",
        dataset_code=DATASET_CODE,
        country="United States",
        region="E2E",
        source_file_type="xlsx",
        notes="Mock Data used only for isolated browser workflow verification.",
    )
    db.add(dataset)
    db.flush()
    db.add_all(
        [
            DamodaranMarginBenchmark(
                dataset_file_id=dataset.id,
                industry_name="Software (System & Application)",
                country="United States",
                number_of_firms=10,
                ebit_margin=0.20,
            ),
            DamodaranMarginBenchmark(
                dataset_file_id=dataset.id,
                industry_name="Semiconductor",
                country="United States",
                number_of_firms=10,
                ebit_margin=0.18,
            ),
        ]
    )


def _company(db, *, ticker: str, market: str, exchange: str, currency: str, country: str) -> Company:
    existing = db.query(Company).filter_by(
        market=market,
        primary_exchange=exchange,
        local_symbol=ticker,
    ).first()
    if existing is not None:
        return existing
    company = Company(
        ticker=ticker,
        local_symbol=ticker,
        name=f"{ticker} Mock Data Company",
        market=market,
        primary_exchange=exchange,
        exchange=exchange,
        country=country,
        region="E2E",
        currency=currency,
        sector="Mock Data Technology",
        industry="Mock Data Software",
        asset_type="Equity",
        active=True,
    )
    db.add(company)
    db.flush()
    return company


def _price_series(db, company: Company, values: list[float], currency: str) -> list[MarketPrice]:
    rows: list[MarketPrice] = []
    for offset, value in enumerate(values):
        as_of = START_DATE + timedelta(days=offset)
        existing = db.query(MarketPrice).filter_by(
            company_id=company.id,
            as_of_date=as_of,
            provider_name="e2e_mock_fixture",
        ).first()
        if existing is not None:
            rows.append(existing)
            continue
        row = MarketPrice(
            company_id=company.id,
            ticker=company.ticker,
            price=value,
            currency=currency,
            as_of_date=as_of,
            provider_name="e2e_mock_fixture",
            price_type="Mock Data",
            adjustment_state="not_applicable",
            warnings_json=["Mock Data used only for isolated browser workflow verification."],
        )
        db.add(row)
        rows.append(row)
    db.flush()
    return rows


def _trusted_mock_dcf(db, company: Company, intrinsic_value: float) -> DcfOutput:
    model = db.query(ValuationModel).filter_by(
        user_id=E2E_USER_ID,
        company_id=company.id,
        name=f"{company.ticker} Mock Data Base DCF",
    ).first()
    if model is None:
        model = ValuationModel(
            user_id=E2E_USER_ID,
            company_id=company.id,
            name=f"{company.ticker} Mock Data Base DCF",
            description="Mock Data used only for isolated browser workflow verification.",
            model_type="fcff_dcf",
        )
        db.add(model)
        db.flush()
    assumptions = db.query(DcfAssumptionSet).filter_by(
        valuation_model_id=model.id,
        scenario="Base",
    ).first()
    if assumptions is None:
        assumptions = DcfAssumptionSet(
            valuation_model_id=model.id,
            scenario="Base",
            is_stale=False,
        )
        db.add(assumptions)
        db.flush()
    output = db.query(DcfOutput).filter_by(assumption_set_id=assumptions.id).first()
    if output is None:
        output = DcfOutput(
            assumption_set_id=assumptions.id,
            intrinsic_value_per_share=intrinsic_value,
            model_quality_score=90,
            warnings_json=[],
            created_at=datetime.combine(END_DATE, datetime.min.time(), tzinfo=UTC),
        )
        db.add(output)
        db.flush()
    return output


def _snapshot_holding(
    holding: PortfolioHolding,
    company: Company,
    price: MarketPrice,
    fx_rate: float,
) -> dict:
    market_value_local = float(holding.quantity) * float(price.price)
    return {
        "holding_id": holding.id,
        "company_id": company.id,
        "ticker": company.ticker,
        "quantity": float(holding.quantity),
        "currency": holding.currency,
        "market_price": float(price.price),
        "market_price_id": price.id,
        "market_price_date": price.as_of_date.isoformat(),
        "market_fx_rate_to_base": fx_rate,
        "market_value_local": market_value_local,
        "market_value_base": market_value_local * fx_rate,
        "is_stale_price": False,
        "market_fx_is_stale": False,
        "cost_fx_is_stale": False,
    }


def _ensure_portfolio_fixture(db) -> None:
    if db.get(User, E2E_USER_ID) is None:
        db.add(User(id=E2E_USER_ID, email="local-user@local.invalid", name="E2E Local User"))
        db.flush()
    existing = db.query(Portfolio).filter_by(user_id=E2E_USER_ID, name=PORTFOLIO_NAME).first()
    if existing is not None:
        return

    usd_company = _company(
        db,
        ticker="E2EUSD",
        market="US",
        exchange="NASDAQ",
        currency="USD",
        country="United States",
    )
    eur_company = _company(
        db,
        ticker="E2EEUR",
        market="DE",
        exchange="XETRA",
        currency="EUR",
        country="Germany",
    )
    benchmark_company = _company(
        db,
        ticker="E2EBMK",
        market="US",
        exchange="NYSE",
        currency="USD",
        country="United States",
    )
    portfolio = Portfolio(
        user_id=E2E_USER_ID,
        name=PORTFOLIO_NAME,
        base_currency="USD",
        description="Mock Data used only for isolated browser workflow verification.",
    )
    db.add(portfolio)
    db.flush()
    usd_holding = PortfolioHolding(
        portfolio_id=portfolio.id,
        company_id=usd_company.id,
        ticker=usd_company.ticker,
        quantity=10,
        average_cost=95,
        currency="USD",
        as_of_date=START_DATE,
    )
    eur_holding = PortfolioHolding(
        portfolio_id=portfolio.id,
        company_id=eur_company.id,
        ticker=eur_company.ticker,
        quantity=5,
        average_cost=75,
        currency="EUR",
        as_of_date=START_DATE,
    )
    db.add_all([usd_holding, eur_holding])
    db.flush()

    usd_values = [100 + offset * 0.45 + (offset % 3) * 0.10 for offset in range(22)]
    eur_values = [80 + offset * 0.35 + (offset % 4) * 0.08 for offset in range(22)]
    benchmark_values = [100 + offset * 0.30 + (offset % 5) * 0.05 for offset in range(22)]
    usd_prices = _price_series(db, usd_company, usd_values, "USD")
    eur_prices = _price_series(db, eur_company, eur_values, "EUR")
    benchmark_prices = _price_series(db, benchmark_company, benchmark_values, "USD")

    fx_rows: list[FxRateObservation] = []
    for offset in range(22):
        as_of = START_DATE + timedelta(days=offset)
        row = FxRateObservation(
            base_currency="EUR",
            quote_currency="USD",
            rate=1.10 + offset * 0.002,
            as_of_date=as_of,
            provider_name="e2e_mock_fixture",
            provider_symbol="EURUSD",
            source_url="https://example.invalid/mock-data/eur-usd",
            source_timestamp=datetime.combine(as_of, datetime.min.time(), tzinfo=UTC),
        )
        db.add(row)
        fx_rows.append(row)
    db.flush()

    db.add(PortfolioBenchmarkConfig(
        portfolio_id=portfolio.id,
        benchmark_company_id=benchmark_company.id,
        ticker=benchmark_company.ticker,
        currency="USD",
        provider_name="e2e_mock_fixture",
        provider_symbol=benchmark_company.ticker,
        effective_from=START_DATE,
        notes="Mock Data used only for isolated browser workflow verification.",
        active=True,
    ))
    db.add(PortfolioTransaction(
        portfolio_id=portfolio.id,
        ticker="CASH",
        transaction_type="deposit",
        quantity=1500,
        price=0,
        fees=0,
        currency="USD",
        transaction_date=START_DATE - timedelta(days=1),
        notes="Mock Data initial funding for isolated browser workflow verification.",
    ))

    _trusted_mock_dcf(db, usd_company, 125)
    _trusted_mock_dcf(db, eur_company, 105)

    for snapshot_date, price_index in ((START_DATE, 0), (END_DATE, 21)):
        eur_fx = float(fx_rows[price_index].rate)
        holdings = [
            _snapshot_holding(usd_holding, usd_company, usd_prices[price_index], 1.0),
            _snapshot_holding(eur_holding, eur_company, eur_prices[price_index], eur_fx),
        ]
        market_value = sum(item["market_value_base"] for item in holdings)
        cash = 60.0
        db.add(PortfolioSnapshot(
            portfolio_id=portfolio.id,
            snapshot_date=snapshot_date,
            total_market_value=market_value,
            total_cost_basis=1325,
            total_cash=cash,
            total_portfolio_value=market_value + cash,
            base_currency="USD",
            calculation_status="complete",
            holdings_count=2,
            priced_holdings_count=2,
            missing_price_tickers_json=[],
            missing_fx_pairs_json=[],
            payload_json={
                "claim_type": "Mock Data",
                "holdings": holdings,
                "source_market_price_ids": [item["market_price_id"] for item in holdings],
                "source_fx_observation_ids": [fx_rows[price_index].id],
                "benchmark_market_price_id": benchmark_prices[price_index].id,
            },
        ))


def main() -> None:
    with SessionLocal() as db:
        _ensure_margin_fixture(db)
        _ensure_portfolio_fixture(db)
        db.commit()


if __name__ == "__main__":
    main()
