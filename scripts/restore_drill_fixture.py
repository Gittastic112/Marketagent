import argparse
import hashlib

from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.company import Company
from app.models.document_asset import DocumentAsset
from app.models.raw_document import RawDocument
from app.models.source import Source
from app.models.user import User


FIXTURE_USER_ID = "restore-drill-user"
FIXTURE_SOURCE_NAME = "Restore Drill Source"
FIXTURE_CONTENT_HASH = "restore-drill-raw-document-v1"
FIXTURE_ASSET = b"%PDF-1.4\nrestore-drill-binary\n%%EOF\n"


def seed() -> None:
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
        db.commit()


def clear() -> None:
    with SessionLocal() as db:
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("seed", "clear", "verify"))
    args = parser.parse_args()
    {"seed": seed, "clear": clear, "verify": verify}[args.action]()
    print(f"Restore drill fixture {args.action} passed.")


if __name__ == "__main__":
    main()
