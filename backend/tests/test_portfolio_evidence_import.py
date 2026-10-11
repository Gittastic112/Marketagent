from __future__ import annotations

import hashlib
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.main import app
from app.models import (
    Company,
    FxRateObservation,
    MarketPrice,
    Portfolio,
    PortfolioBenchmarkConfig,
    PortfolioHolding,
    ProcessingRun,
    User,
)
from app.services import portfolio_evidence_import as evidence_service


HEADERS = (
    "record_type,ticker,price,currency,base_currency,quote_currency,rate,"
    "as_of_date,provider_name,provider_symbol,source_url,source_timestamp,price_type\n"
)


def price_row(
    ticker: str = "ACME",
    price: str = "101.25",
    *,
    provider: str = "Example Exchange",
    source_url: str = "https://example.com/acme-history",
    source_timestamp: str = "2026-08-21T21:00:00Z",
    price_type: str = "adjusted_close",
    as_of_date: str = "2026-08-21",
    currency: str = "USD",
) -> str:
    return (
        f"market_price,{ticker},{price},{currency},,,,{as_of_date},{provider},"
        f"{ticker},{source_url},{source_timestamp},{price_type}\n"
    )


def fx_row(
    rate: str = "0.01145",
    *,
    base: str = "INR",
    quote: str = "USD",
    provider: str = "Example Central Bank",
    as_of_date: str = "2026-08-21",
) -> str:
    return (
        f"fx_rate,,,,{base},{quote},{rate},{as_of_date},{provider},{base}{quote},"
        f"https://example.com/fx,{as_of_date}T21:00:00Z,\n"
    )


def upload(client: TestClient, path: str, content: str, *, expected_hash: str | None = None):
    data = {"expected_sha256": expected_hash} if expected_hash is not None else None
    return client.post(
        path,
        data=data,
        files={"file": ("evidence.csv", content.encode(), "text/csv")},
    )


def bundle_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def build_portfolio(db: Session, *, user_id: str = "admin_user_id_fallback") -> Portfolio:
    acme = Company(ticker="ACME", name="Acme", market="US", currency="USD")
    infy = Company(ticker="INFY", name="Infosys", market="IN", currency="INR")
    spy = Company(ticker="SPY", name="SPY ETF", market="US", currency="USD", is_etf=True)
    portfolio = Portfolio(user_id=user_id, name="Real portfolio", base_currency="USD")
    db.add_all([acme, infy, spy, portfolio])
    db.flush()
    db.add_all(
        [
            PortfolioHolding(
                portfolio_id=portfolio.id,
                company_id=acme.id,
                ticker="ACME",
                quantity=2,
                average_cost=90,
                currency="USD",
                as_of_date=date(2026, 8, 1),
            ),
            PortfolioHolding(
                portfolio_id=portfolio.id,
                company_id=infy.id,
                ticker="INFY",
                quantity=3,
                average_cost=1400,
                currency="INR",
                as_of_date=date(2026, 8, 1),
            ),
            PortfolioBenchmarkConfig(
                portfolio_id=portfolio.id,
                ticker="SPY",
                currency="USD",
                provider_name="Example Exchange",
                provider_symbol="SPY",
                effective_from=date(2026, 8, 1),
                active=True,
            ),
        ]
    )
    db.commit()
    return portfolio


def test_template_is_owned_and_contains_no_real_or_mock_values(client: TestClient, db: Session) -> None:
    portfolio = build_portfolio(db)
    response = client.get(f"/portfolios/{portfolio.id}/evidence-bundle/template")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.text.startswith(HEADERS)
    assert "HELD_TICKER" in response.text
    assert "Mock Data" not in response.text


def test_template_rejects_cross_owner_access(client: TestClient, db: Session) -> None:
    db.add(User(id="other", email="other@example.com", name="Other"))
    db.commit()
    portfolio = build_portfolio(db, user_id="other")
    response = client.get(f"/portfolios/{portfolio.id}/evidence-bundle/template")
    assert response.status_code == 404


def test_preview_reports_scope_hash_counts_and_no_writes(client: TestClient, db: Session) -> None:
    portfolio = build_portfolio(db)
    content = HEADERS + price_row() + fx_row()
    response = upload(client, f"/portfolios/{portfolio.id}/evidence-bundle/preview", content)
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["content_sha256"] == bundle_hash(content)
    assert payload["create_count"] == 2
    assert payload["error_count"] == 0
    assert payload["can_apply"] is True
    assert payload["claim_type"] == "Fact"
    assert payload["contains_mock_data"] is False
    assert payload["scope"]["holding_tickers"] == ["ACME", "INFY"]
    assert payload["scope"]["benchmark_ticker"] == "SPY"
    assert payload["scope"]["allowed_fx_pairs"] == ["INR/USD", "USD/INR"]
    assert db.query(MarketPrice).count() == 0
    assert db.query(FxRateObservation).count() == 0
    assert db.query(ProcessingRun).count() == 0


def test_apply_is_atomic_and_links_rows_to_completed_run(client: TestClient, db: Session) -> None:
    portfolio = build_portfolio(db)
    content = HEADERS + price_row() + fx_row()
    response = upload(
        client,
        f"/portfolios/{portfolio.id}/evidence-bundle/apply",
        content,
        expected_hash=bundle_hash(content),
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["created_count"] == 2
    assert payload["market_prices_created"] == 1
    assert payload["fx_rates_created"] == 1
    run = db.get(ProcessingRun, payload["processing_run_id"])
    assert run.status == "completed"
    assert run.metadata_json["content_sha256"] == bundle_hash(content)
    price = db.query(MarketPrice).one()
    fx = db.query(FxRateObservation).one()
    assert price.import_run_id == run.id == fx.import_run_id
    assert price.source_url == "https://example.com/acme-history"
    assert price.claim_type == fx.claim_type == "Fact"


def test_apply_rejects_changed_file_and_audits_failure(client: TestClient, db: Session) -> None:
    portfolio = build_portfolio(db)
    previewed = HEADERS + price_row(price="100")
    changed = HEADERS + price_row(price="101")
    response = upload(
        client,
        f"/portfolios/{portfolio.id}/evidence-bundle/apply",
        changed,
        expected_hash=bundle_hash(previewed),
    )
    assert response.status_code == 409
    assert db.query(MarketPrice).count() == 0
    run = db.query(ProcessingRun).one()
    assert run.status == "failed"
    assert run.error_details_json == {"code": "PREVIEW_HASH_MISMATCH"}
    assert run.metadata_json["content_sha256"] == bundle_hash(changed)
    assert run.fetched_count == 1


def test_apply_revalidates_and_rolls_back_every_row_on_error(client: TestClient, db: Session) -> None:
    portfolio = build_portfolio(db)
    content = HEADERS + price_row() + fx_row(rate="-1")
    response = upload(
        client,
        f"/portfolios/{portfolio.id}/evidence-bundle/apply",
        content,
        expected_hash=bundle_hash(content),
    )
    assert response.status_code == 400
    assert db.query(MarketPrice).count() == 0
    assert db.query(FxRateObservation).count() == 0
    run = db.query(ProcessingRun).one()
    assert run.status == "failed"
    assert run.error_count == 1


def test_exact_stored_duplicates_are_skipped_idempotently(client: TestClient, db: Session) -> None:
    portfolio = build_portfolio(db)
    content = HEADERS + price_row() + fx_row()
    path = f"/portfolios/{portfolio.id}/evidence-bundle/apply"
    first = upload(client, path, content, expected_hash=bundle_hash(content))
    second = upload(client, path, content, expected_hash=bundle_hash(content))
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["data"]["created_count"] == 0
    assert second.json()["data"]["skipped_duplicate_count"] == 2
    assert db.query(MarketPrice).count() == 1
    assert db.query(FxRateObservation).count() == 1


def test_stored_fact_conflict_blocks_preview(client: TestClient, db: Session) -> None:
    portfolio = build_portfolio(db)
    first = HEADERS + price_row(price="100")
    upload(
        client,
        f"/portfolios/{portfolio.id}/evidence-bundle/apply",
        first,
        expected_hash=bundle_hash(first),
    )
    conflict = HEADERS + price_row(price="200")
    response = upload(client, f"/portfolios/{portfolio.id}/evidence-bundle/preview", conflict)
    payload = response.json()["data"]
    assert payload["can_apply"] is False
    assert payload["error_count"] == 1
    assert payload["rows"][0]["errors"][0]["field"] == "conflict"


def test_exact_in_file_duplicate_is_a_skip(client: TestClient, db: Session) -> None:
    portfolio = build_portfolio(db)
    row = price_row()
    response = upload(
        client,
        f"/portfolios/{portfolio.id}/evidence-bundle/preview",
        HEADERS + row + row,
    )
    payload = response.json()["data"]
    assert payload["create_count"] == 1
    assert payload["skip_count"] == 1
    assert payload["error_count"] == 0


def test_in_file_conflict_is_an_error(client: TestClient, db: Session) -> None:
    portfolio = build_portfolio(db)
    content = HEADERS + price_row(price="100") + price_row(price="200")
    payload = upload(
        client,
        f"/portfolios/{portfolio.id}/evidence-bundle/preview",
        content,
    ).json()["data"]
    assert payload["error_count"] == 1
    assert payload["can_apply"] is False
    assert "Conflicts with row 2" in payload["rows"][1]["message"]


def test_preview_rejects_unscoped_ticker_and_fx_pair(client: TestClient, db: Session) -> None:
    portfolio = build_portfolio(db)
    content = HEADERS + price_row(ticker="NOPE") + fx_row(base="EUR", quote="USD")
    payload = upload(
        client,
        f"/portfolios/{portfolio.id}/evidence-bundle/preview",
        content,
    ).json()["data"]
    assert payload["error_count"] == 2
    fields = {error["field"] for row in payload["rows"] for error in row["errors"]}
    assert {"ticker", "base_currency"}.issubset(fields)


def test_preview_requires_linked_company_for_holding(client: TestClient, db: Session) -> None:
    portfolio = build_portfolio(db)
    holding = db.query(PortfolioHolding).filter_by(ticker="ACME").one()
    holding.company_id = None
    db.commit()
    payload = upload(
        client,
        f"/portfolios/{portfolio.id}/evidence-bundle/preview",
        HEADERS + price_row(),
    ).json()["data"]
    assert payload["error_count"] == 1
    assert "linked company" in payload["rows"][0]["message"]


def test_preview_rejects_generic_mock_or_untraceable_sources(client: TestClient, db: Session) -> None:
    portfolio = build_portfolio(db)
    content = HEADERS + price_row(provider="manual", source_url="") + price_row(
        ticker="INFY",
        currency="INR",
        provider="Mock Data provider",
        source_url="http://localhost/history",
    )
    payload = upload(
        client,
        f"/portfolios/{portfolio.id}/evidence-bundle/preview",
        content,
    ).json()["data"]
    assert payload["error_count"] == 2
    messages = [error["message"] for row in payload["rows"] for error in row["errors"]]
    assert any("actual exchange" in message for message in messages)
    assert any("source URL is required" in message for message in messages)
    assert any("Mock Data" in message for message in messages)
    assert any("Localhost" in message for message in messages)


def test_preview_rejects_bad_dates_decimals_currency_and_unused_fields(client: TestClient, db: Session) -> None:
    portfolio = build_portfolio(db)
    broken = (
        "market_price,ACME,NaN,US,INR,,1,2099-01-01,Example Exchange,ACME,"
        "https://example.com,2026-08-20,close\n"
    )
    payload = upload(
        client,
        f"/portfolios/{portfolio.id}/evidence-bundle/preview",
        HEADERS + broken,
    ).json()["data"]
    fields = {error["field"] for error in payload["rows"][0]["errors"]}
    assert {"price", "currency", "base_currency", "rate", "as_of_date", "source_timestamp"}.issubset(fields)


def test_reader_rejects_duplicate_headers_bad_encoding_size_and_row_limit(
    client: TestClient,
    db: Session,
    monkeypatch,
) -> None:
    portfolio = build_portfolio(db)
    path = f"/portfolios/{portfolio.id}/evidence-bundle/preview"
    duplicate_headers = HEADERS.replace("ticker,price", "ticker,ticker") + price_row()
    assert upload(client, path, duplicate_headers).status_code == 400
    bad_encoding = client.post(
        path,
        files={"file": ("evidence.csv", b"\xff\xfe", "text/csv")},
    )
    assert bad_encoding.status_code == 400
    monkeypatch.setattr(evidence_service, "MAX_EVIDENCE_BYTES", 30)
    assert upload(client, path, HEADERS + price_row()).status_code == 413
    monkeypatch.setattr(evidence_service, "MAX_EVIDENCE_BYTES", 20_000)
    monkeypatch.setattr(evidence_service, "MAX_EVIDENCE_ROWS", 1)
    assert upload(client, path, HEADERS + price_row() + fx_row()).status_code == 400
