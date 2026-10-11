"""Read budgets protect against relationship graphs growing behind flat API rows."""
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import event, inspect, select

from app.models import Company, ExposureTag, MarketPrice, Portfolio, PortfolioHolding
from app.models.processing_run import ProcessingRun


@pytest.fixture
def read_graph(db_session):
    company = Company(ticker="BUDGET", name="Query budget", currency="USD")
    company.exposure_tags.append(ExposureTag(name="Technology"))
    portfolio = Portfolio(name="Query budget", base_currency="USD")
    db_session.add_all([company, portfolio])
    db_session.flush()
    db_session.add_all([
        PortfolioHolding(portfolio_id=portfolio.id, company_id=company.id,
                         ticker=company.ticker, quantity=2, average_cost=10,
                         currency="USD", as_of_date=date.today()),
        MarketPrice(company_id=company.id, ticker=company.ticker, price=12,
                    currency="USD", as_of_date=date.today()),
        ProcessingRun(company_id=company.id, run_type="sec_ingestion",
                      source_type="sec", status="success",
                      started_at=datetime.now(timezone.utc)),
    ])
    db_session.commit()
    ids = company.id, portfolio.id
    db_session.expunge_all()  # Do not let fixture-populated identity maps mask reads.
    return ids


@pytest.mark.parametrize("path,budget", [
    ("/companies", 2),
    ("/companies/{company}", 2),
    ("/portfolios", 1),
    ("/portfolio-holdings?portfolio_id={portfolio}", 3),
    ("/portfolios/{portfolio}/valuation", 16),
    ("/portfolios/{portfolio}/risk-return-comparison", 20),
    ("/api/providers/health", 8),
])
def test_flat_reads_do_not_expand_unrelated_graphs(client, db_session, read_graph, path, budget):
    company, portfolio = read_graph
    statements = []

    def record(_connection, _cursor, statement, *_args):
        statements.append(statement)

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", record)
    try:
        response = client.get(path.format(company=company, portfolio=portfolio))
    finally:
        event.remove(engine, "before_cursor_execute", record)
    assert response.status_code == 200, response.text
    assert len(statements) <= budget, f"{len(statements)} queries exceed {budget}"
    if path == "/companies":
        assert response.json()["data"][0]["exposure_tags"][0]["name"] == "Technology"


def test_relationships_remain_available_on_explicit_access(db_session, read_graph):
    company_id, portfolio_id = read_graph
    company = db_session.scalar(select(Company).where(Company.id == company_id))
    portfolio = db_session.get(Portfolio, portfolio_id)
    assert "market_prices" in inspect(company).unloaded
    assert "holdings" in inspect(portfolio).unloaded
    assert len(company.market_prices) == 1
    assert len(portfolio.holdings) == 1
    assert portfolio.holdings[0].company.id == company_id


def test_valuation_loads_only_the_latest_price_not_the_entire_history(client, db_session, read_graph):
    company, portfolio = read_graph
    db_session.add_all([MarketPrice(company_id=company, ticker="BUDGET", price=10,
                                   as_of_date=date.today() - timedelta(days=offset))
                        for offset in range(1, 101)])
    db_session.commit()
    db_session.expunge_all()
    loaded = []

    def record(price, _context):
        loaded.append(price.id)

    event.listen(MarketPrice, "load", record)
    try:
        response = client.get(f"/portfolios/{portfolio}/valuation")
    finally:
        event.remove(MarketPrice, "load", record)
    assert response.status_code == 200
    assert response.json()["data"]["holdings"][0]["market_price"] == 12
    assert len(loaded) == 1
