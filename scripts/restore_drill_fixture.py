import argparse
import hashlib
import os
import time
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select

from app.db.session import SessionLocal, engine
from app.models.brief_source import BriefSource
from app.models.brief_review import BriefComparisonReview
from app.models.company import Company
from app.models.document_asset import DocumentAsset
from app.models.raw_document import RawDocument
from app.models.source import Source
from app.models.user import User
from app.models.portfolio import Portfolio, PortfolioHolding, PortfolioTransaction


FIXTURE_USER_ID = "restore-drill-user"
FIXTURE_SOURCE_NAME = "Restore Drill Source"
FIXTURE_CONTENT_HASH = "restore-drill-raw-document-v1"
FIXTURE_ASSET = b"%PDF-1.4\nrestore-drill-binary\n%%EOF\n"
PRIVATE_ASSET = b"%PDF-1.4\nMock Data private research PDF\x00\xff\n%%EOF\n"
PRIVATE_TEXT = "Mock Data: revenue growth requires review; no factual claim is certified."


def assert_disposable_target() -> None:
    if (os.environ.get("RESTORE_DRILL_DISPOSABLE") != "1"
        or os.environ.get("APP_ENV") != "test"
        or engine.url.host != "postgres-e2e" or engine.url.database != "marketintel_e2e"):
        raise RuntimeError("Restore fixtures require an explicitly marked disposable test database")


def seed() -> None:
    assert_disposable_target()
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.id == FIXTURE_USER_ID)) is not None:
            raise RuntimeError("Restore drill fixture already exists")
        user = User(
            id=FIXTURE_USER_ID,
            email="restore-drill@example.invalid",
            name="Restore Drill",
        )
        source = Source(
            name=FIXTURE_SOURCE_NAME,
            source_type="manual_filing",
            reliability_score=100,
        )
        company = Company(
            ticker="DRILL",
            name="Restore Drill Corp",
            market="US",
            primary_exchange="TEST",
            local_symbol="DRILL",
            country="United States",
            currency="USD",
        )
        db.add_all([user, source, company])
        db.flush()
        document = RawDocument(
            company_id=company.id,
            source_id=source.id,
            document_type="restore_drill_pdf",
            title="Restore drill document",
            raw_text="Restore drill source text.",
            content_hash=FIXTURE_CONTENT_HASH,
        )
        db.add(document)
        db.flush()
        db.add(
            DocumentAsset(
                raw_document_id=document.id,
                original_filename="restore-drill.pdf",
                mime_type="application/pdf",
                size_bytes=len(FIXTURE_ASSET),
                sha256=hashlib.sha256(FIXTURE_ASSET).hexdigest(),
                page_count=1,
                content=FIXTURE_ASSET,
            )
        )
        private = BriefSource(user_id=user.id, company_id=company.id,
            title="Mock Data private recovery source", source_kind="pdf", as_of_date=date(2026, 1, 1),
            identity_hash=hashlib.sha256(PRIVATE_TEXT.encode()).hexdigest(),
            source_sha256=hashlib.sha256(PRIVATE_ASSET).hexdigest(), content_text=PRIVATE_TEXT,
            pdf_bytes=PRIVATE_ASSET, extraction_json={"claim_type": "Mock Data", "page_spans": [{"page": 1, "start_char": 0, "end_char": len(PRIVATE_TEXT)}]},
            analysis_json={"claim_type": "Mock Data", "findings": [{"quote": PRIVATE_TEXT, "review_status": "pending"}]})
        portfolio = Portfolio(user_id=user.id, name="Mock Data recovery portfolio", base_currency="USD")
        db.add_all([private, portfolio])
        db.flush()
        db.add_all([
            BriefComparisonReview(user_id=user.id, company_id=company.id, field="revenue_growth_years_json",
                include_mock=True, version=1, evidence_hash=hashlib.sha256(PRIVATE_TEXT.encode()).hexdigest(),
                disposition="follow_up", notes="Mock Data recovery relationship only, not approved evidence.",
                evidence_json={"claim_type": "Mock Data", "source_id": private.id, "source_sha256": private.source_sha256}),
            PortfolioHolding(portfolio_id=portfolio.id, company_id=company.id, ticker="DRILL", quantity=Decimal("3"),
                average_cost=Decimal("25"), currency="USD", as_of_date=date(2026, 1, 1)),
            PortfolioTransaction(portfolio_id=portfolio.id, company_id=company.id, ticker="DRILL", transaction_type="buy",
                quantity=Decimal("3"), price=Decimal("25"), fees=Decimal("1"), currency="USD", transaction_date=date(2026, 1, 1),
                notes="Mock Data restore drill"),
        ])
        db.commit()


def clear() -> None:
    assert_disposable_target()
    with SessionLocal() as db:
        portfolio_ids = select(Portfolio.id).where(Portfolio.user_id == FIXTURE_USER_ID)
        db.execute(delete(PortfolioHolding).where(PortfolioHolding.portfolio_id.in_(portfolio_ids)))
        db.execute(delete(PortfolioTransaction).where(PortfolioTransaction.portfolio_id.in_(portfolio_ids)))
        db.execute(delete(Portfolio).where(Portfolio.user_id == FIXTURE_USER_ID))
        db.execute(delete(BriefComparisonReview).where(BriefComparisonReview.user_id == FIXTURE_USER_ID))
        db.execute(delete(BriefSource).where(BriefSource.user_id == FIXTURE_USER_ID))
        document = db.scalar(
            select(RawDocument).where(RawDocument.content_hash == FIXTURE_CONTENT_HASH)
        )
        if document is not None:
            db.delete(document)
        company = db.scalar(select(Company).where(Company.local_symbol == "DRILL"))
        if company is not None:
            db.delete(company)
        source = db.scalar(select(Source).where(Source.name == FIXTURE_SOURCE_NAME))
        if source is not None:
            db.delete(source)
        db.execute(delete(User).where(User.id == FIXTURE_USER_ID))
        db.commit()


def verify() -> None:
    assert_disposable_target()
    expected_sha = hashlib.sha256(FIXTURE_ASSET).hexdigest()
    with SessionLocal() as db:
        document = db.scalar(
            select(RawDocument).where(RawDocument.content_hash == FIXTURE_CONTENT_HASH)
        )
        if document is None or document.raw_text != "Restore drill source text.":
            raise RuntimeError("Restored document metadata/text does not match")
        asset = db.scalar(
            select(DocumentAsset).where(DocumentAsset.raw_document_id == document.id)
        )
        if asset is None:
            raise RuntimeError("Restored document asset is missing")
        if asset.content != FIXTURE_ASSET or asset.sha256 != expected_sha:
            raise RuntimeError("Restored document asset bytes do not match")
        private = db.scalar(select(BriefSource).where(BriefSource.user_id == FIXTURE_USER_ID))
        review = db.scalar(select(BriefComparisonReview).where(BriefComparisonReview.user_id == FIXTURE_USER_ID))
        portfolio = db.scalar(select(Portfolio).where(Portfolio.user_id == FIXTURE_USER_ID))
        if (private is None or private.pdf_bytes != PRIVATE_ASSET or private.content_text != PRIVATE_TEXT
            or private.source_sha256 != hashlib.sha256(PRIVATE_ASSET).hexdigest()
            or private.analysis_json["findings"][0]["quote"] != PRIVATE_TEXT):
            raise RuntimeError("Private source bytes, source text or finding did not survive restore")
        if (review is None or review.company_id != private.company_id
            or review.evidence_json["source_id"] != private.id
            or review.evidence_json["source_sha256"] != private.source_sha256):
            raise RuntimeError("Analyst receipt relationship did not survive restore")
        if portfolio is None or len(portfolio.holdings) != 1 or len(portfolio.transactions) != 1:
            raise RuntimeError("Portfolio history did not survive restore")
        if (portfolio.holdings[0].company_id != private.company_id
            or portfolio.transactions[0].company_id != private.company_id
            or portfolio.transactions[0].fees != Decimal("1.000000")):
            raise RuntimeError("Portfolio evidence relationship did not survive restore")


def write() -> None:
    """Create committed Mock Data during pg_dump and manifest collection."""
    assert_disposable_target()
    for number in range(100):
        with SessionLocal() as db:
            db.add(Source(name=f"Mock Data concurrent recovery writer {number}", source_type="manual"))
            db.commit()
        time.sleep(0.1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("seed", "clear", "verify", "write"))
    args = parser.parse_args()
    {"seed": seed, "clear": clear, "verify": verify, "write": write}[args.action]()
    print(f"Restore drill fixture {args.action} passed.")


if __name__ == "__main__":
    main()
