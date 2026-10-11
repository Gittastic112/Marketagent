from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pdfplumber
from PIL import Image

from app.api.dependencies import get_current_user
from app.main import app
from app.models import Company, DocumentAsset, FinancialExtractionCandidate, ProcessingRun, RawDocument
from app.services.pdf_financial_extraction import (
    _consolidate_candidates,
    _statement_line_candidates,
    _parse_pdf_financial_tables,
    parse_pdf_financial_tables,
    parse_pdf_page_ranges,
    validate_pdf_upload,
)
from helpers import response_data


FIXTURE = Path(__file__).parent / "fixtures" / "financial_statement_table.pdf"


def _company(db) -> Company:
    company = Company(
        ticker="PDFCO",
        name="PDF Filing Company",
        market="IN",
        primary_exchange="NSE",
        local_symbol="PDFCO",
        currency="INR",
        country="India",
    )
    db.add(company)
    db.commit()
    return company


def test_parse_pdf_financial_tables_preserves_page_and_cell_geometry() -> None:
    parsed = parse_pdf_financial_tables(FIXTURE.read_bytes())

    assert parsed.page_count == 1
    assert parsed.table_count == 1
    assert parsed.reporting_currency == "INR"
    assert parsed.reporting_scale == "million"
    assert len(parsed.candidates) == 12
    assert parsed.warnings == ()

    revenue_2026 = next(
        candidate
        for candidate in parsed.candidates
        if candidate.metric_code == "revenue" and candidate.fiscal_year == 2026
    )
    assert revenue_2026.value == 1250
    assert revenue_2026.unit == "INR million"
    assert revenue_2026.source_page == 1
    assert revenue_2026.source_table_name == "Consolidated Financial Statements"
    assert revenue_2026.source_row_label == "Revenue"
    assert revenue_2026.source_column_label == "FY2026"
    assert revenue_2026.source_cell_reference == "P1:T1:R2:C3"
    assert revenue_2026.source_locator_json["type"] == "pdf_table_cell"
    assert revenue_2026.source_locator_json["coordinate_system"] == "pdfplumber_top_left_points"
    assert revenue_2026.source_locator_json["cell_bbox"] == {
        "x0": 410.0,
        "top": 130.0,
        "x1": 520.0,
        "bottom": 158.0,
    }
    assert revenue_2026.confidence_label == "high"

    diluted_2026 = next(
        candidate
        for candidate in parsed.candidates
        if candidate.metric_code == "diluted_shares" and candidate.fiscal_year == 2026
    )
    assert diluted_2026.unit == "shares"
    assert diluted_2026.extraction_warnings is None
    assert diluted_2026.confidence_label == "high"

    presentation = parse_pdf_financial_tables(FIXTURE.read_bytes(), period_type="unknown")
    assert {candidate.period_type for candidate in presentation.candidates} == {"unknown"}


def test_parse_pdf_page_ranges_is_bounded_and_normalized() -> None:
    assert parse_pdf_page_ranges(" 465-470, 542, 466 ") == (465, 466, 467, 468, 469, 470, 542)
    assert parse_pdf_page_ranges(None) is None
    assert parse_pdf_page_ranges(" ") is None

    for invalid in ("0", "4-2", "1,a", "1-100"):
        try:
            parse_pdf_page_ranges(invalid, max_targeted_pages=10)
        except Exception as exc:
            assert getattr(exc, "status_code", None) == 422
        else:
            raise AssertionError(f"Invalid page range {invalid!r} must be rejected")


def test_targeted_pdf_scan_preserves_full_physical_page_count() -> None:
    class TwoPagePdf:
        def __init__(self, page):
            self.pages = [page, page]

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    with pdfplumber.open(BytesIO(FIXTURE.read_bytes())) as source_pdf:
        with patch("pdfplumber.open", return_value=TwoPagePdf(source_pdf.pages[0])):
            # This unit stub targets the parser itself. Public calls exercise
            # the isolated worker using the real PDF fixture above.
            parsed = _parse_pdf_financial_tables(FIXTURE.read_bytes(), page_numbers=(2,))

    assert parsed.page_count == 2
    assert parsed.scanned_pages == (2,)
    assert parsed.raw_text.startswith("[Page 2]")


def test_india_statement_rows_preserve_attribution_and_sum_debt_components() -> None:
    balance_sheet = """
Consolidated Balance Sheet
as at March 31, 2025
INR in crore
Particulars Notes As at March 31, 2025 As at March 31, 2024
Cash and Cash Equivalents 11 3,406.32 1,575.73
Non-Controlling Interests 2,537.95 1,598.23
Borrowings 14 35,830.68 37,662.93
Borrowings 18 9,979.35 8,616.30
Lease Liabilities 15 5,389.61 2,953.28
Lease Liabilities 15 254.56 71.20
""".strip()
    rows = _statement_line_candidates(
        page_text=balance_sheet,
        page_number=465,
        section="Consolidated Balance Sheet",
        currency="INR",
        scale="crore",
        page_width=1000,
        page_height=1400,
        page=None,
    )
    candidates = _consolidate_candidates(rows)

    debt_2025 = next(item for item in candidates if item.metric_code == "debt" and item.fiscal_year == 2025)
    assert debt_2025.value == 45_810.03
    assert debt_2025.source_locator_json["type"] == "pdf_reported_component_sum"
    assert len(debt_2025.source_locator_json["components"]) == 2
    assert debt_2025.extraction_warnings == "derived_sum_of_reported_components;review_required"

    leases_2025 = next(
        item for item in candidates if item.metric_code == "lease_liabilities" and item.fiscal_year == 2025
    )
    assert leases_2025.value == 5_644.17
    assert next(
        item for item in candidates if item.metric_code == "minority_interests" and item.fiscal_year == 2025
    ).value == 2_537.95

    profit_and_loss = """
Consolidated Statement of Profit and Loss
for the year ended March 31, 2025
INR in crore
Particulars Notes For the year ended March 31, 2025 For the year ended March 31, 2024
Revenue from Operations 21 30,475.33 26,710.56
Profit for the Year 11,061.26 8,103.99
Equity holders of the parent 11,092.31 8,110.64
Non-controlling interests (31.05) (6.65)
Weighted average number of equity shares in calculating basic and 2,16,01,38,945 2,16,01,38,945
diluted EPS
""".strip()
    pnl_candidates = _statement_line_candidates(
        page_text=profit_and_loss,
        page_number=466,
        section="Consolidated Statement of Profit and Loss",
        currency="INR",
        scale="crore",
        page_width=1000,
        page_height=1400,
        page=None,
    )

    assert next(item for item in pnl_candidates if item.metric_code == "net_income").value == 11_061.26
    assert next(item for item in pnl_candidates if item.metric_code == "net_income_parent").value == 11_092.31
    assert next(item for item in pnl_candidates if item.metric_code == "net_income_nci").value == -31.05
    diluted = next(item for item in pnl_candidates if item.metric_code == "diluted_shares")
    assert diluted.value == 2_160_138_945
    assert diluted.unit == "shares"


def test_validate_pdf_upload_sanitizes_filename_and_rejects_signature_spoof() -> None:
    upload = validate_pdf_upload(
        "..\\unsafe\r\nname.pdf",
        "application/pdf",
        FIXTURE.read_bytes(),
    )
    assert upload.filename == "unsafename.pdf"

    try:
        validate_pdf_upload("fake.pdf", "application/pdf", b"not a pdf")
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 400
        assert "signature" in str(getattr(exc, "detail", "")).lower()
    else:
        raise AssertionError("A spoofed PDF signature must be rejected")


def test_pdf_upload_persists_asset_candidates_and_processing_run(client, db) -> None:
    company = _company(db)

    response = client.post(
        f"/api/companies/{company.id}/filings/pdf",
        files={"file": ("financials.pdf", FIXTURE.read_bytes(), "application/pdf")},
        data={
            "document_type": "annual_report",
            "title": "FY2026 Annual Report",
            "published_at": "2026-05-31T00:00:00Z",
            "source_url": "https://exchange.example/filings/fy2026.pdf",
            "page_ranges": "1",
        },
    )

    assert response.status_code == 201
    result = response_data(response)
    assert result["page_count"] == 1
    assert result["scanned_page_count"] == 1
    assert result["scanned_pages"] == [1]
    assert result["table_count"] == 1
    assert result["created_count"] == 12
    assert result["warnings"] == ["targeted_page_scan"]
    assert "content" not in result["asset"]

    document = db.get(RawDocument, result["raw_document_id"])
    assert document is not None
    assert document.raw_payload_json["source_kind"] == "pdf_filing_upload"
    assert document.url == "https://exchange.example/filings/fy2026.pdf"
    assert document.raw_payload_json["extraction_scope"] == "full_document"
    assert document.raw_payload_json["scanned_pages"] == [1]
    assert "[Page 1]" in document.raw_text
    asset = db.get(DocumentAsset, result["asset"]["id"])
    assert asset is not None
    assert asset.content == FIXTURE.read_bytes()
    assert db.query(FinancialExtractionCandidate).filter_by(raw_document_id=document.id).count() == 12

    metadata = client.get(f"/api/raw-documents/{document.id}/asset")
    assert metadata.status_code == 200
    assert "content" not in response_data(metadata)

    streamed = client.get(f"/api/raw-documents/{document.id}/asset/content")
    assert streamed.status_code == 200
    assert streamed.content == FIXTURE.read_bytes()
    assert streamed.headers["content-type"] == "application/pdf"
    assert streamed.headers["cache-control"] == "private, no-store"
    assert streamed.headers["x-content-type-options"] == "nosniff"

    rendered = client.get(
        f"/api/raw-documents/{document.id}/asset/pages/1.png?scale=1"
    )
    assert rendered.status_code == 200
    assert rendered.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert rendered.headers["content-type"] == "image/png"
    assert rendered.headers["cache-control"] == "private, no-store"
    assert rendered.headers["x-content-type-options"] == "nosniff"
    with Image.open(BytesIO(rendered.content)) as image:
        assert image.width > 0
        assert image.height > 0

    assert client.get(
        f"/api/raw-documents/{document.id}/asset/pages/2.png"
    ).status_code == 404
    assert client.get(
        f"/api/raw-documents/{document.id}/asset/pages/1.png?scale=3"
    ).status_code == 422

    run = db.query(ProcessingRun).filter_by(company_id=company.id, run_type="pdf_filing_upload").one()
    assert run.status == "success"
    assert run.fetched_count == 1
    assert run.created_count == 12
    assert run.metadata_json["raw_document_id"] == document.id
    assert run.metadata_json["page_count"] == 1
    assert run.metadata_json["scanned_page_count"] == 1
    assert run.metadata_json["source_url"] == "https://exchange.example/filings/fy2026.pdf"


def test_pdf_upload_records_duplicate_without_creating_second_document(client, db) -> None:
    company = _company(db)
    upload = {
        "files": {"file": ("financials.pdf", FIXTURE.read_bytes(), "application/pdf")},
        "data": {"document_type": "annual_report"},
    }

    assert client.post(f"/api/companies/{company.id}/filings/pdf", **upload).status_code == 201
    duplicate = client.post(f"/api/companies/{company.id}/filings/pdf", **upload)

    assert duplicate.status_code == 409
    assert db.query(RawDocument).filter(RawDocument.content_hash.like("pdf-filing:%")).count() == 1
    runs = db.query(ProcessingRun).filter_by(
        company_id=company.id,
        run_type="pdf_filing_upload",
    ).order_by(ProcessingRun.id).all()
    assert [run.status for run in runs] == ["success", "success"]
    assert runs[-1].skipped_duplicate_count == 1


def test_pdf_upload_records_invalid_file_failure_without_persisting_document(client, db) -> None:
    company = _company(db)

    response = client.post(
        f"/api/companies/{company.id}/filings/pdf",
        files={"file": ("spoofed.pdf", b"not a pdf", "application/pdf")},
        data={"document_type": "annual_report"},
    )

    assert response.status_code == 400
    assert db.query(DocumentAsset).count() == 0
    run = db.query(ProcessingRun).filter_by(company_id=company.id, run_type="pdf_filing_upload").one()
    assert run.status == "failed"
    assert run.error_count == 1


def test_pdf_asset_routes_require_an_authenticated_session(client) -> None:
    authenticated_override = app.dependency_overrides.pop(get_current_user)
    try:
        metadata = client.get("/api/raw-documents/1/asset")
        content = client.get("/api/raw-documents/1/asset/content")
        rendered = client.get("/api/raw-documents/1/asset/pages/1.png")
    finally:
        app.dependency_overrides[get_current_user] = authenticated_override

    assert metadata.status_code == 401
    assert content.status_code == 401
    assert rendered.status_code == 401
