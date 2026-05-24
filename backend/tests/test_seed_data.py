from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Company, Source
from app.services.seed_data import seed_sample_data


def test_seed_sample_data_is_idempotent() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        first_result = seed_sample_data(session)
        second_result = seed_sample_data(session)

        companies = list(session.scalars(select(Company).order_by(Company.ticker)))
        sources = list(session.scalars(select(Source).order_by(Source.name)))

    assert first_result == {"companies_created": 3, "sources_created": 3}
    assert second_result == {"companies_created": 0, "sources_created": 0}
    assert [company.ticker for company in companies] == ["AAPL", "MSFT", "NVDA"]
    assert [source.name for source in sources] == ["Manual Research", "RSS Feed", "SEC EDGAR"]
