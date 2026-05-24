from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, Source


SAMPLE_COMPANIES = [
    {"ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology", "exchange": "NASDAQ"},
    {"ticker": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "exchange": "NASDAQ"},
    {"ticker": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", "exchange": "NASDAQ"},
]

SAMPLE_SOURCES = [
    {"name": "Manual Research", "source_type": "manual", "reliability_score": 80},
    {"name": "RSS Feed", "source_type": "news", "reliability_score": 60},
    {"name": "SEC EDGAR", "source_type": "filing", "base_url": "https://www.sec.gov", "reliability_score": 95},
]


def seed_sample_data(db: Session) -> dict[str, int]:
    companies_created = 0
    sources_created = 0

    for company_data in SAMPLE_COMPANIES:
        existing = db.scalar(select(Company).where(Company.ticker == company_data["ticker"]))
        if existing is None:
            db.add(Company(**company_data))
            companies_created += 1

    for source_data in SAMPLE_SOURCES:
        existing = db.scalar(select(Source).where(Source.name == source_data["name"]))
        if existing is None:
            db.add(Source(**source_data))
            sources_created += 1

    db.commit()

    return {"companies_created": companies_created, "sources_created": sources_created}
