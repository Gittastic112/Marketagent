"""Seed deterministic Mock Data used only by the isolated browser test stack."""

from datetime import UTC, date, datetime, timedelta
from copy import deepcopy
from hashlib import sha256
import json

from app.db.session import SessionLocal
from app.models import (
    AiOutput,
    BriefSource,
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
    PortfolioCashBalance,
    PortfolioTransaction,
    RawDocument,
    Source,
    User,
    ValuationModel,
)
from app.services.portfolio_analytics import record_daily_snapshot
from app.models.market_price import CompanyMarketData
from app.models.financial import FinancialMetric, FinancialStatementPeriod


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
            cash_flow_currency=company.currency,
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
    # Explicit opening funding and purchases reconcile to both current balances.
    # Historical snapshots must be produced by the same replay path as the UI.
    for company, kind, quantity, price in [(usd_company, "deposit", 1010, 0),
        (usd_company, "buy", 10, 95), (eur_company, "deposit", 375, 0), (eur_company, "buy", 5, 75)]:
        db.add(PortfolioTransaction(portfolio_id=portfolio.id, company_id=company.id if kind == "buy" else None,
            ticker=company.ticker if kind == "buy" else "CASH", transaction_type=kind, quantity=quantity,
            price=price, fees=0, currency=company.currency, transaction_date=START_DATE,
            notes="Mock Data recorded activity for isolated browser workflow verification."))
    db.add_all([PortfolioCashBalance(portfolio_id=portfolio.id, currency="USD", amount=60, as_of_date=START_DATE),
        PortfolioCashBalance(portfolio_id=portfolio.id, currency="EUR", amount=0, as_of_date=START_DATE)])

    _trusted_mock_dcf(db, usd_company, 125)
    _trusted_mock_dcf(db, eur_company, 105)

    db.flush()
    for snapshot_date in (START_DATE, END_DATE):
        snapshot = record_daily_snapshot(db, portfolio.id, snapshot_date)
        assert snapshot.calculation_status == "complete", snapshot.payload_json["replay_basis"]
        snapshot.payload_json = {**snapshot.payload_json, "claim_type": "Mock Data"}


def _ensure_private_comparison_fixture(db) -> None:
    company = _company(db, ticker="BRIEFCMP", market="US", exchange="NASDAQ", currency="USD", country="United States")
    for period, direction in [("FY2025", "increase"), ("FY2026", "decrease")]:
        text = f"Mock Data {period} USD consolidated revenue has an {direction} hypothesis for browser testing."
        digest = sha256(text.encode()).hexdigest()
        if db.query(BriefSource).filter_by(user_id=E2E_USER_ID, identity_hash=digest).first():
            continue
        source = BriefSource(user_id=E2E_USER_ID, company_id=company.id,
            title=f"Mock Data {period} comparison source", source_kind="text", content_text=text,
            source_sha256=digest, identity_hash=digest, as_of_date=START_DATE, analysis_status="complete",
            extraction_json={"text_sha256": digest, "character_count": len(text), "warnings": ["Mock Data browser fixture"]})
        db.add(source)
        db.flush()
        marker = f"brief_source:{source.id}"
        analysis = {"source_marker": f"[source_id:{marker}]", "summary": "Mock Data comparison only.",
            "findings": [{"title": f"Mock Data {period} hypothesis", "importance": "high", "confidence": "low",
                "importance_reason": "Inspect the stated reporting period before interpreting the direction.", "quote": text,
                "valuation_inputs": [{"field": "starting_revenue", "direction": direction,
                    "reason": "Mock Data hypothesis, not a numeric input.",
                    "comparison_context": {"period": period, "currency": "USD", "economic_scope": "consolidated"}}]}]}
        output = AiOutput(user_id=E2E_USER_ID, reference_type="brief_source", reference_id=source.id,
            provider_name="e2e_mock_fixture", model_name="fixture-model", prompt_version="brief-source-v3",
            input_hash=digest, source_ids_json=[marker], output_text=json.dumps(analysis), confidence_label="low",
            is_mock=True, human_review_status="pending", citation_validation_status="valid",
            citations_json=[{"source_id": marker, "status": "valid", "quote": text, "start_char": 0, "end_char": len(text)}])
        db.add(output)
        db.flush()
        source.ai_output_id = output.id
        display = deepcopy(analysis)
        finding = display["findings"][0]
        finding.update(start_char=0, end_char=len(text), page=None)
        finding["valuation_inputs"][0].update(label="Base-year revenue",
            review_href=f"/companies/{company.id}/valuation/draft#starting_revenue")
        source.analysis_json = display


def _ensure_ai_review_fixture(db) -> None:
    digest = sha256(b"Mock Data citation-versus-interpretation browser fixture").hexdigest()
    if db.query(RawDocument).filter_by(content_hash=digest).first():
        return
    source = Source(name="Mock Data interpretation fixture", source_type="manual")
    db.add(source)
    db.flush()
    document = RawDocument(source_id=source.id, document_type="manual_note",
        title="Mock Data citation does not prove interpretation", content_hash=digest,
        raw_text="Mock Data: Revenue increased 12% in FY2025.")
    db.add(document)
    db.flush()
    marker = f"raw_document:{document.id}"
    db.add(AiOutput(user_id=E2E_USER_ID, raw_document_id=document.id,
        reference_type="raw_document", reference_id=document.id, provider_name="e2e_mock_fixture",
        model_name="Mock Data fixture", prompt_version="fixture-v1", input_hash=digest,
        source_scope="raw_document_text", transmission_scope="none", source_ids_json=[marker],
        output_text=f"Revenue increased 21% in FY2026. [source_id:{marker}]", is_mock=True,
        confidence_label="test_fixture", human_review_status="pending",
        limitations="Mock Data adversarial output: the number and fiscal period are deliberately incorrect."))


def _ensure_company_currency_fixture(db) -> None:
    company = _company(db, ticker="E2EINR", market="IN", exchange="NSE", currency="INR", country="India")
    if db.query(CompanyMarketData).filter_by(company_id=company.id).first() is None:
        db.add(CompanyMarketData(company_id=company.id, currency="INR", current_price=1250,
            change_percent=0, market_cap=1250000000, pe_ratio=0, provider_name="Mock Data provider",
            provider_symbol="E2EINR.NS", price_type="quote", delay_minutes=None,
            source_timestamp=datetime(2026, 9, 30, 10, tzinfo=UTC),
            observed_at=datetime(2026, 10, 1, 10, tzinfo=UTC),
            warnings_json=["Mock Data used only for isolated browser verification."]))
    if db.query(FinancialStatementPeriod).filter_by(company_id=company.id).first() is None:
        period = FinancialStatementPeriod(company_id=company.id, period_type="annual", year=2026,
            report_date=date(2026, 5, 31), currency="INR", currency_source="manual", currency_confidence="user_asserted")
        db.add(period)
        db.flush()
        db.add_all([FinancialMetric(period_id=period.id, metric_name=name, value=value, unit=unit)
            for name, value, unit in [("Revenue", 1250, "INR million"), ("Net Income", 0, "INR million"),
                ("EPS (Basic)", 3.5, "INR/share"), ("Total Assets", 600, None)]])


def _ensure_peer_receipt_recovery_fixtures(db) -> None:
    from sqlalchemy import select
    from app.models import PeerValuationSet
    from app.schemas.peer_valuation import PeerValuationSetCreate, PeerValuationSetReview
    from app.services.peer_valuation_sets import (
        PeerValuationSetService, calculate_peer_diagnostics,
        peer_set_members, peer_set_response, peer_set_target_context,
    )

    # Existing seed module supplies date, timedelta, Company and E2E_USER_ID.
    if db.get_bind().url.database != "marketintel_e2e":
        raise RuntimeError("Receipt recovery fixtures require the isolated marketintel_e2e database")
    company = db.scalar(select(Company).where(Company.ticker == "E2EUSD"))
    if company is None or "Mock Data" not in company.name:
        raise RuntimeError("Receipt recovery requires the isolated Mock Data company fixture")
    for state in ("missing", "stale"):
        name = f"Mock Data {state} receipt recovery"
        existing = db.scalar(select(PeerValuationSet).where(
            PeerValuationSet.user_id == E2E_USER_ID, PeerValuationSet.name == name))
        if existing is not None:
            continue  # Never overwrite completed review evidence during a repeated seed.
        payload = PeerValuationSetCreate.model_validate({
            "companyId": company.id, "name": name,
            "notes": "Mock Data: synthetic disposable browser fixture, not genuine reviewed company evidence.",
            "members": [{"identifier": f"RECOVERY{state.upper()}{index}", "included": True,
                "multiples": {"pe": 10 + index}, "sourceName": "Synthetic browser test source",
                "sourceUrl": f"https://example.invalid/receipt-fixture/{state}/{index}",
                "sourceAsOf": date.today().isoformat(), "currency": "USD", "claimType": "Source Summary",
                "notes": "Mock Data only; no external source was fetched."} for index in (1, 2, 3)],
        })
        created = PeerValuationSetService.create_set(db, user_id=E2E_USER_ID, payload=payload)
        view = peer_set_response(created)
        reviewed = PeerValuationSetService.review_set(db, peer_set_id=created.id, user_id=E2E_USER_ID,
            payload=PeerValuationSetReview(acknowledged=True,expectedVersion=created.version,
                expectedDiagnosticsSha256=view["diagnostics"]["acknowledgementSha256"],
                acknowledgedWarningCodes=view["diagnostics"]["warningCodes"]))
        if state == "missing":
            reviewed.review_diagnostics_sha256 = None
            reviewed.review_warning_codes_json = None
            reviewed.review_diagnostics_as_of = None
        else:
            past = calculate_peer_diagnostics(peer_set_members(reviewed),
                target_context=peer_set_target_context(reviewed),as_of=date.today()-timedelta(days=1))
            reviewed.review_diagnostics_sha256 = past["acknowledgementSha256"]
            reviewed.review_warning_codes_json = past["warningCodes"]
            reviewed.review_diagnostics_as_of = date.fromisoformat(past["asOf"])
        db.commit()


def main() -> None:
    with SessionLocal() as db:
        _ensure_margin_fixture(db)
        _ensure_portfolio_fixture(db)
        _ensure_peer_receipt_recovery_fixtures(db)
        _ensure_private_comparison_fixture(db)
        _ensure_ai_review_fixture(db)
        _ensure_company_currency_fixture(db)
        db.commit()


if __name__ == "__main__":
    main()
