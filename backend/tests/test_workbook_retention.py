"""Mock Data uploads; byte retention is checked without touching installation data."""
import hashlib
from io import BytesIO

import openpyxl
from sqlalchemy import select

from app.models import Company, DocumentAsset, FinancialExtractionCandidate, RawDocument


MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def upload_fixture(db):
    company = Company(ticker="BOOK", name="Mock Data workbook", currency="INR")
    db.add(company); db.commit()
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Data Sheet"
    sheet["B2"] = "Mar 2026"; sheet["A3"] = "Sales"; sheet["B3"] = 1250
    buffer = BytesIO(); workbook.save(buffer); workbook.close()
    return company, buffer.getvalue()


def upload(client, company, content):
    return client.post(f"/api/companies/{company.id}/fundamentals/screener",
        files={"file": ("Mock Data workbook.xlsx", content, MIME)})


def test_workbook_is_retained_once_and_download_has_original_bytes(client, db):
    company, content = upload_fixture(db)
    assert upload(client, company, content).status_code == 201
    document = db.scalar(select(RawDocument).where(RawDocument.company_id == company.id))
    asset = db.scalar(select(DocumentAsset).where(DocumentAsset.raw_document_id == document.id))
    assert asset is not None
    assert asset.content == content and asset.sha256 == hashlib.sha256(content).hexdigest()
    assert asset.page_count == 0 and asset.size_bytes == len(content)
    response = client.get(f"/api/raw-documents/{document.id}/asset/content")
    assert response.status_code == 200 and response.content == content
    assert response.headers["content-type"] == MIME
    assert response.headers["content-disposition"].startswith("attachment;")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert client.get(f"/api/raw-documents/{document.id}/asset/pages/1.png").status_code == 415
    assert upload(client, company, content).status_code == 409
    assert db.query(DocumentAsset).count() == 1 and db.query(FinancialExtractionCandidate).count() == 1


def test_identical_legacy_reupload_restores_only_missing_original_asset(client, db):
    company, content = upload_fixture(db)
    assert upload(client, company, content).status_code == 201
    document = db.scalar(select(RawDocument).where(RawDocument.company_id == company.id))
    asset = db.scalar(select(DocumentAsset).where(DocumentAsset.raw_document_id == document.id))
    if asset is not None:  # Model an older upload whose temporary workbook was deleted.
        db.delete(asset); db.commit()
    candidate = db.query(FinancialExtractionCandidate).one()
    before = (candidate.id, candidate.value, candidate.unit, candidate.review_status, candidate.source_locator_json, candidate.updated_at)
    response = upload(client, company, content)
    assert response.status_code == 201 and response.json()["data"]["status"] == "original_restored"
    assert response.json()["data"]["extracted_count"] == 0
    db.expire_all()
    assert db.query(DocumentAsset).one().content == content
    assert (candidate.id, candidate.value, candidate.unit, candidate.review_status, candidate.source_locator_json, candidate.updated_at) == before
    other = Company(ticker="OTHERBOOK", name="Mock Data other", currency="INR")
    db.add(other); db.commit()
    assert upload(client, other, content).status_code == 409
    assert db.query(DocumentAsset).count() == 1
