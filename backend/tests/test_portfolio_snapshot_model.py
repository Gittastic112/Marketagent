from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Portfolio, PortfolioSnapshot


def test_snapshot_records_completeness_and_is_unique_per_portfolio_date():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        portfolio = Portfolio(name="Snapshot Test", base_currency="USD")
        snapshot = PortfolioSnapshot(
            portfolio=portfolio,
            snapshot_date=date(2026, 8, 9),
            total_portfolio_value=1250,
            base_currency="USD",
            calculation_status="complete",
            holdings_count=2,
            priced_holdings_count=2,
            missing_price_tickers_json=[],
            missing_fx_pairs_json=[],
        )
        db.add(snapshot)
        db.commit()

        assert snapshot.calculation_status == "complete"
        assert snapshot.total_portfolio_value == 1250

        db.add(
            PortfolioSnapshot(
                portfolio_id=portfolio.id,
                snapshot_date=date(2026, 8, 9),
            )
        )
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
        else:
            raise AssertionError("duplicate daily snapshot should violate the database constraint")
