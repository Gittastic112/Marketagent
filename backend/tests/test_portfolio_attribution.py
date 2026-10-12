from collections.abc import Generator
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.api.schemas import PortfolioAttributionRead
from app.models import MarketPrice, Portfolio, PortfolioHolding, PortfolioTransaction
from app.services.portfolio_attribution_engine import PortfolioAttributionEngine
from app.services.portfolio_valuation import calculate_portfolio_valuation


def _session() -> Generator[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


def test_valuation_does_not_invent_fx_or_opportunity_cost() -> None:
    with next(_session()) as db:
        portfolio = Portfolio(name="Truth Portfolio", base_currency="USD")
        holding = PortfolioHolding(
            portfolio=portfolio,
            ticker="TEST",
            quantity=10,
            average_cost=100,
            currency="USD",
            as_of_date=date(2026, 8, 1),
        )
        db.add_all(
            [
                portfolio,
                holding,
                MarketPrice(
                    ticker="TEST",
                    price=110,
                    currency="USD",
                    as_of_date=date(2026, 8, 8),
                ),
            ]
        )
        db.commit()

        valuation = calculate_portfolio_valuation(db, portfolio.id, date(2026, 8, 8))
        valued_holding = valuation["holdings"][0]

        assert valued_holding["fx_impact"] is None
        assert valued_holding["opportunity_cost"] is None
        assert valued_holding["opportunity_cost_percent"] is None


def test_attribution_reports_recorded_activity_by_currency() -> None:
    with next(_session()) as db:
        portfolio = Portfolio(name="Activity Portfolio", base_currency="USD")
        holding = PortfolioHolding(
            portfolio=portfolio,
            ticker="TEST",
            quantity=10,
            average_cost=100,
            currency="USD",
            as_of_date=date(2026, 8, 1),
        )
        db.add_all(
            [
                portfolio,
                holding,
                MarketPrice(
                    ticker="TEST",
                    price=120,
                    currency="USD",
                    as_of_date=date(2026, 8, 8),
                ),
            ]
        )
        db.flush()
        db.add_all(
            [
                PortfolioTransaction(
                    portfolio_id=portfolio.id,
                    ticker="TEST",
                    transaction_type="buy",
                    quantity=4,
                    price=100,
                    fees=2,
                    currency="USD",
                    transaction_date=date(2026, 8, 2),
                ),
                PortfolioTransaction(
                    portfolio_id=portfolio.id,
                    ticker="TEST",
                    transaction_type="sell",
                    quantity=1,
                    price=125,
                    fees=1,
                    currency="USD",
                    transaction_date=date(2026, 8, 3),
                ),
                PortfolioTransaction(
                    portfolio_id=portfolio.id,
                    ticker="TEST",
                    transaction_type="dividend",
                    quantity=10,
                    price=2,
                    fees=0,
                    currency="USD",
                    transaction_date=date(2026, 8, 4),
                ),
                PortfolioTransaction(
                    portfolio_id=portfolio.id,
                    ticker="CASH",
                    transaction_type="deposit",
                    quantity=500,
                    price=0,
                    fees=0,
                    currency="USD",
                    transaction_date=date(2026, 8, 5),
                ),
                PortfolioTransaction(
                    portfolio_id=portfolio.id,
                    ticker="CASH",
                    transaction_type="withdrawal",
                    quantity=75,
                    price=0,
                    fees=0,
                    currency="USD",
                    transaction_date=date(2026, 8, 6),
                ),
                PortfolioTransaction(
                    portfolio_id=portfolio.id,
                    ticker="CASH",
                    transaction_type="fee",
                    quantity=5,
                    price=0,
                    fees=0,
                    currency="USD",
                    transaction_date=date(2026, 8, 7),
                ),
            ]
        )
        db.commit()

        attribution = PortfolioAttributionEngine.decompose_performance(
            db,
            portfolio.id,
            date(2026, 8, 8),
        )

        assert attribution["calculation_status"] == "partial"
        # This fixture's opening positions/cash are not recorded or reconciled.
        assert attribution["total_unrealized_pnl"] is None
        assert attribution["components"]["price_movement"] is None
        assert attribution["components"]["fx_impact"] is None
        assert attribution["opportunity_cost"] is None

        activity = attribution["activity_by_currency"]["USD"]
        assert activity == {
            "purchases": 400,
            "sales": 125,
            "dividends": 10,
            "deposits": 500,
            "withdrawals": 75,
            "fees": 8,
            "taxes": 0,
            "net_position_cash_flow": -275,
            "net_external_cash_flow": 425,
        }
        assert any("historical fx" in warning.lower() for warning in attribution["warnings"])
        assert any("benchmark" in warning for warning in attribution["warnings"])
        PortfolioAttributionRead.model_validate(attribution)


def test_cross_currency_attribution_blocks_aggregate_price_movement() -> None:
    with next(_session()) as db:
        portfolio = Portfolio(name="Mixed Currency", base_currency="USD")
        holding = PortfolioHolding(
            portfolio=portfolio,
            ticker="INRTEST",
            quantity=2,
            average_cost=100,
            currency="INR",
            as_of_date=date(2026, 8, 1),
        )
        db.add_all(
            [
                portfolio,
                holding,
                MarketPrice(
                    ticker="INRTEST",
                    price=120,
                    currency="INR",
                    as_of_date=date(2026, 8, 8),
                ),
            ]
        )
        db.commit()

        attribution = PortfolioAttributionEngine.decompose_performance(
            db,
            portfolio.id,
            date(2026, 8, 8),
        )

        assert attribution["total_unrealized_pnl"] is None
        assert attribution["components"]["price_movement"] is None
        assert any("portfolio base currency" in warning for warning in attribution["warnings"])
