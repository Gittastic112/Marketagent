import csv
from datetime import date, datetime, timezone
from io import StringIO

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.main import app
from app.models import (
    Company,
    Event,
    MarketPrice,
    Portfolio,
    PortfolioHolding,
    PortfolioTransaction,
    RawDocument,
    Source,
)
from app.services import data_transfer as data_transfer_service


def use_user(user_id: str) -> None:
    app.dependency_overrides[get_current_user] = lambda: {
        "id": user_id,
        "email": f"{user_id}@example.com",
        "name": user_id,
    }


def upload_csv(client: TestClient, path: str, content: str, *, preview: bool = False):
    suffix = "?preview=true" if preview else ""
    return client.post(
        f"{path}{suffix}",
        files={"file": ("records.csv", content.encode("utf-8"), "text/csv")},
    )


def parse_csv_response(response) -> list[dict[str, str]]:
    return list(csv.DictReader(StringIO(response.text)))


def test_portfolio_exports_are_real_csv_and_owner_scoped(
    client: TestClient,
    db_session: Session,
) -> None:
    owned = Portfolio(
        user_id="admin_user_id_fallback",
        name="Owned",
        base_currency="USD",
    )
    foreign = Portfolio(user_id="other-user", name="Foreign", base_currency="USD")
    db_session.add_all([owned, foreign])
    db_session.flush()
    db_session.add_all(
        [
            PortfolioHolding(
                portfolio_id=owned.id,
                ticker="=OWN",
                quantity=1,
                average_cost=10,
                currency="USD",
                as_of_date=date(2026, 7, 25),
            ),
            PortfolioHolding(
                portfolio_id=foreign.id,
                ticker="HIDE",
                quantity=2,
                average_cost=20,
                currency="USD",
                as_of_date=date(2026, 7, 25),
            ),
            PortfolioTransaction(
                portfolio_id=owned.id,
                ticker="OWN",
                transaction_type="buy",
                quantity=1,
                price=10,
                fees=0,
                currency="USD",
                transaction_date=date(2026, 7, 25),
                notes="@unsafe",
            ),
            PortfolioTransaction(
                portfolio_id=foreign.id,
                ticker="HIDE",
                transaction_type="buy",
                quantity=2,
                price=20,
                fees=0,
                currency="USD",
                transaction_date=date(2026, 7, 25),
            ),
        ]
    )
    db_session.commit()

    holding_response = client.get("/export/portfolio-holdings")
    transaction_response = client.get("/export/portfolio-transactions")

    assert holding_response.status_code == 200
    assert holding_response.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=portfolio_holdings.csv" == holding_response.headers[
        "content-disposition"
    ]
    assert parse_csv_response(holding_response) == [
        {
            "portfolio_id": str(owned.id),
            "company_id": "",
            "ticker": "'=OWN",
            "quantity": "1.000000",
            "average_cost": "10.000000",
            "currency": "USD",
            "as_of_date": "2026-07-25",
        }
    ]
    assert parse_csv_response(transaction_response)[0]["notes"] == "'@unsafe"
    assert "HIDE" not in transaction_response.text


def test_shared_exports_use_real_model_fields_and_escape_formulas(
    client: TestClient,
    db_session: Session,
) -> None:
    company = Company(
        ticker="SAFE",
        name="Safe Corp",
        market="US",
        primary_exchange="NYSE",
        local_symbol="SAFE",
    )
    source = Source(name="=SEC", source_type="filing")
    db_session.add_all([company, source])
    db_session.flush()
    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="10-K",
        title="Annual filing",
        url="https://example.com/filing",
        published_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        content_hash="hash-1",
    )
    price = MarketPrice(
        company_id=company.id,
        ticker="SAFE",
        price=12.5,
        currency="USD",
        as_of_date=date(2026, 7, 25),
    )
    db_session.add_all([document, price])
    db_session.flush()
    db_session.add(
        Event(
            company_id=company.id,
            raw_document_id=document.id,
            event_type="filing",
            information_speed="medium",
            title="+Changed outlook",
            description="@Source detail",
            event_time=datetime(2026, 7, 2, tzinfo=timezone.utc),
            credibility_score=80,
            impact_score=70,
        )
    )
    db_session.commit()

    raw_rows = parse_csv_response(client.get("/export/raw-documents"))
    market_rows = parse_csv_response(client.get("/export/market-prices"))
    event_rows = parse_csv_response(client.get("/export/events"))

    assert raw_rows[0]["source_name"] == "'=SEC"
    assert raw_rows[0]["source_type"] == "filing"
    assert market_rows[0]["source_name"] == "manual"
    assert event_rows[0]["title"] == "'+Changed outlook"
    assert event_rows[0]["description"] == "'@Source detail"
    assert event_rows[0]["event_type"] == "filing"


def test_portfolio_import_preview_enforces_ownership_without_writing(
    client: TestClient,
    db_session: Session,
) -> None:
    foreign = Portfolio(user_id="other-user", name="Foreign", base_currency="USD")
    db_session.add(foreign)
    db_session.commit()
    content = (
        "portfolio_id,ticker,quantity,average_cost,currency,as_of_date\n"
        f"{foreign.id},HIDE,2,20,USD,2026-07-25\n"
    )

    response = upload_csv(
        client,
        "/import/portfolio-holdings",
        content,
        preview=True,
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["valid_count"] == 0
    assert payload["error_count"] == 1
    assert payload["rows"][0]["errors"][0]["field"] == "portfolio_id"
    assert db_session.query(PortfolioHolding).count() == 0


def test_transaction_import_is_transactional_and_rejects_invalid_rows(
    client: TestClient,
    db_session: Session,
) -> None:
    portfolio = Portfolio(
        user_id="admin_user_id_fallback",
        name="Import",
        base_currency="USD",
    )
    db_session.add(portfolio)
    db_session.commit()
    content = (
        "portfolio_id,ticker,transaction_type,quantity,price,fees,currency,transaction_date,notes\n"
        f"{portfolio.id},GOOD,buy,2,10,0,USD,2026-07-25,valid\n"
        f"{portfolio.id},BAD,trade,2,10,0,USD,2026-07-25,invalid type\n"
    )

    response = upload_csv(client, "/import/portfolio-transactions", content)

    assert response.status_code == 400
    assert db_session.query(PortfolioTransaction).count() == 0
    assert db_session.query(PortfolioHolding).count() == 0


def test_transaction_import_applies_all_valid_rows_atomically(
    client: TestClient,
    db_session: Session,
) -> None:
    portfolio = Portfolio(
        user_id="admin_user_id_fallback",
        name="Import",
        base_currency="USD",
    )
    db_session.add(portfolio)
    db_session.commit()
    content = (
        "portfolio_id,ticker,transaction_type,quantity,price,fees,currency,transaction_date,notes\n"
        f"{portfolio.id},GOOD,buy,2,10,1,USD,2026-07-25,first\n"
        f"{portfolio.id},GOOD,buy,1,13,0,USD,2026-07-26,second\n"
    )

    response = upload_csv(client, "/import/portfolio-transactions", content)

    assert response.status_code == 200
    assert response.json()["data"]["imported_count"] == 2
    assert db_session.query(PortfolioTransaction).count() == 2
    holding = db_session.query(PortfolioHolding).one()
    assert float(holding.quantity) == 3


def test_csv_import_rejects_oversized_files_and_row_counts(
    client: TestClient,
    monkeypatch,
) -> None:
    oversized = "ticker,price,currency,as_of_date\n" + (
        "A,1,USD,2026-07-25\n" * 10
    )
    monkeypatch.setattr(data_transfer_service, "MAX_CSV_BYTES", 60)
    response = upload_csv(client, "/import/market-prices", oversized)
    assert response.status_code == 413

    monkeypatch.setattr(data_transfer_service, "MAX_CSV_BYTES", 1024)
    monkeypatch.setattr(data_transfer_service, "MAX_CSV_ROWS", 1)
    too_many_rows = (
        "ticker,price,currency,as_of_date\n"
        "A,1,USD,2026-07-25\n"
        "B,2,USD,2026-07-25\n"
    )
    response = upload_csv(client, "/import/market-prices", too_many_rows)
    assert response.status_code == 400


def test_market_price_import_uses_supported_fields_and_detects_duplicates(
    client: TestClient,
    db_session: Session,
) -> None:
    content = (
        "ticker,price,currency,as_of_date,source_name\n"
        "SAFE,12.5,USD,2026-07-25,manual\n"
    )

    first = upload_csv(client, "/import/market-prices", content)
    second = upload_csv(client, "/import/market-prices", content)

    assert first.status_code == 200
    assert second.status_code == 400
    stored = db_session.query(MarketPrice).one()
    assert stored.ticker == "SAFE"
    assert not hasattr(stored, "source_name")
