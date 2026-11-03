"""Bound list rendering without changing the legacy full-history API contract."""
from datetime import date, timedelta

import pytest
from sqlalchemy import event

from app.models import Company, MarketPrice


@pytest.fixture
def price_history(db_session):
    companies = [Company(ticker="MOCKPAGEA", name="Mock Data price page A"),
                 Company(ticker="MOCKPAGEB", name="Mock Data price page B")]
    db_session.add_all(companies)
    db_session.flush()
    company_ids = [company.id for company in companies]
    prices = [MarketPrice(
        company_id=company_ids[index % 2], ticker="MOCK" if index % 3 else "OTHER",
        price=index + 1, currency="USD", as_of_date=date(2026, 10, 12) - timedelta(days=index % 4),
    ) for index in range(150)]
    db_session.add_all(prices)
    db_session.flush()
    rows = [{"id": row.id, "company_id": row.company_id, "ticker": row.ticker, "date": row.as_of_date}
            for row in prices]
    db_session.commit()
    db_session.expunge_all()  # Cached fixture rows must not mask unbounded loading.
    return sorted(rows, key=lambda row: (row["date"], row["id"]), reverse=True), company_ids


def test_pagination_has_deterministic_nonoverlapping_date_and_id_order(client, price_history):
    rows, _ = price_history
    first = client.get("/market-prices?limit=17&offset=0")
    second = client.get("/market-prices?limit=17&offset=17")
    assert first.status_code == second.status_code == 200
    first_ids = [row["id"] for row in first.json()["data"]]
    second_ids = [row["id"] for row in second.json()["data"]]
    assert first_ids == [row["id"] for row in rows[:17]]
    assert second_ids == [row["id"] for row in rows[17:34]]
    assert not set(first_ids) & set(second_ids)
    # A page boundary within one date must still have a stable ID tie-breaker.
    assert rows[16]["date"] == rows[17]["date"]


@pytest.mark.parametrize("filter_kind", ["ticker", "company", "both"])
def test_filters_are_applied_before_pagination(client, price_history, filter_kind):
    rows, company_ids = price_history
    params = {"limit": 5, "offset": 3}
    if filter_kind in ("ticker", "both"):
        params["ticker"] = "mock"
        rows = [row for row in rows if row["ticker"] == "MOCK"]
    if filter_kind in ("company", "both"):
        params["company_id"] = company_ids[0]
        rows = [row for row in rows if row["company_id"] == company_ids[0]]
    response = client.get("/market-prices", params=params)
    assert response.status_code == 200, response.text
    assert [row["id"] for row in response.json()["data"]] == [row["id"] for row in rows[3:8]]


def test_omitted_limit_preserves_legacy_full_history(client, price_history):
    rows, _ = price_history
    response = client.get("/market-prices")
    assert response.status_code == 200, response.text
    assert [row["id"] for row in response.json()["data"]] == [row["id"] for row in rows]
    assert len(response.json()["data"]) == 150


def test_offset_beyond_history_returns_an_empty_page(client, price_history):
    response = client.get("/market-prices?limit=200&offset=100000")
    assert response.status_code == 200, response.text
    assert response.json()["data"] == []


@pytest.mark.parametrize("query", [
    "limit=0", "limit=-1", "limit=201", "limit=not-an-integer", "offset=-1", "offset=100001",
])
def test_invalid_pagination_bounds_are_rejected(client, query):
    response = client.get("/market-prices?" + query)
    assert response.status_code == 422, response.text


def test_populated_history_materializes_only_the_sql_limited_rows(client, db_session, price_history):
    rows, _ = price_history
    loaded = []
    statements = []

    def record_load(row, _context):
        loaded.append(row.id)

    def record_sql(_connection, _cursor, statement, *_args):
        statements.append(statement)

    engine = db_session.get_bind()
    event.listen(MarketPrice, "load", record_load)
    event.listen(engine, "before_cursor_execute", record_sql)
    try:
        response = client.get("/market-prices?limit=51&offset=50")
    finally:
        event.remove(MarketPrice, "load", record_load)
        event.remove(engine, "before_cursor_execute", record_sql)
    assert response.status_code == 200, response.text
    assert [row["id"] for row in response.json()["data"]] == [row["id"] for row in rows[50:101]]
    assert len(loaded) == 51
    price_queries = [statement for statement in statements if "FROM market_prices" in statement]
    assert len(price_queries) == 1
    assert "LIMIT" in price_queries[0] and "OFFSET" in price_queries[0]
