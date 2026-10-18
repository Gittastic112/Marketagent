import hashlib
import math
import re
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import PurePath
from typing import Any
from urllib.parse import urlparse

from fastapi import HTTPException
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import PdfFinancialExtractionResultRead
from app.models import (
    Company,
    CompanySetupWorkflow,
    DocumentAsset,
    FinancialExtractionCandidate,
    RawDocument,
    Source,
)
from app.services.pdf_jobs import PdfJobError, run_pdf_job


MAX_PDF_BYTES = 40 * 1024 * 1024
MAX_PDF_PAGES = 1_000
MAX_FULL_SCAN_PAGES = 500
MAX_TARGETED_PAGES = 75
PDF_EXTRACTION_METHOD = "pdf_targeted_v5"
PDF_SOURCE_NAME = "Manual PDF Filings"
ALLOWED_PDF_MIME_TYPES = {"application/pdf", "application/octet-stream"}
ALLOWED_DOCUMENT_TYPES = {
    "annual_report",
    "quarterly_result",
    "investor_presentation",
    "exchange_announcement",
    "shareholding_pattern",
    "corporate_action",
}

_METRIC_ALIASES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("revenue", "Revenue", ("revenue from operations", "total revenue", "revenue", "sales")),
    ("ebit", "EBIT", ("operating income", "operating profit", "ebit")),
    (
        "net_income",
        "Net income",
        ("profit for the year", "profit for the period", "profit after tax", "net income", "pat"),
    ),
    ("cash", "Cash", ("cash and cash equivalents", "cash equivalents", "cash")),
    ("debt", "Debt", ("total borrowings", "total debt", "borrowings", "debt")),
    ("capex", "Capex", ("capital expenditures", "capital expenditure", "capex")),
    (
        "depreciation",
        "Depreciation and amortization",
        ("depreciation and amortization", "depreciation", "d&a"),
    ),
    (
        "change_in_working_capital",
        "Change in working capital",
        ("change in net working capital", "change in working capital", "nwc change"),
    ),
    (
        "diluted_shares",
        "Diluted shares",
        ("weighted average diluted shares", "diluted shares", "diluted share count"),
    ),
    ("basic_shares", "Basic shares", ("weighted average basic shares", "basic shares")),
    ("lease_liabilities", "Lease liabilities", ("operating lease liabilities", "lease liabilities")),
    (
        "minority_interests",
        "Minority interests",
        ("non-controlling interests", "noncontrolling interests", "minority interests"),
    ),
    ("preferred_stock", "Preferred stock", ("preferred stock",)),
)

_UNIT_PATTERN = re.compile(
    r"\b(?:amounts?|figures?)\s+(?:are\s+)?in\s+"
    r"(?P<currency>USD|INR|EUR|GBP|JPY|CAD|AUD|CHF|CNY|HKD|SGD)"
    r"(?:\s+(?P<scale>thousand|million|billion|crore|lakh))?\b",
    re.IGNORECASE,
)
_YEAR_PATTERN = re.compile(r"\b(?:FY\s*)?(19\d{2}|20\d{2})(?:\s*[-–]\s*(\d{4}|\d{2}))?\b", re.IGNORECASE)
_INDIA_SCALE_PATTERN = re.compile(
    r"(?:₹|`|\brs\.?\b|\binr\b)?\s*(?:amounts?\s+)?(?:are\s+)?in\s+"
    r"(?P<scale>crore|crores|lakh|lakhs)\b",
    re.IGNORECASE,
)
_STATEMENT_VALUE_TOKEN_PATTERN = re.compile(
    r"(?<![\w,./%₹`])(?:[₹`]?\(?[-+]?(?:\d+(?:,\d{2,3})+|\d+)(?:\.\d+)?\)?\*?|[-–—])(?![\w,./%])"
)
_SCALE_PATTERN = re.compile(r"\b(thousands?|millions?|billions?|crores?|lakhs?|000s?)\b", re.IGNORECASE)
_CURRENCY_PATTERN = re.compile(r"\b(USD|INR|EUR|GBP|JPY|CAD|AUD|CHF|CNY|HKD|SGD)\b", re.IGNORECASE)
_STATEMENT_HEADING = re.compile(
    r"^(?:consolidated\s+)?(?:bal\s*ance sheet|statement of profit and loss|profit and loss account|"
    r"cash flow statement|statement of cash flows)", re.IGNORECASE,
)


@dataclass(frozen=True)
class ValidatedPdfUpload:
    filename: str
    mime_type: str
    content: bytes
    sha256: str


@dataclass(frozen=True)
class PdfTableCandidate:
    metric_code: str
    reported_label: str
    value: float
    unit: str | None
    fiscal_year: int
    period_type: str
    source_text: str
    source_page: int
    source_section: str | None
    source_table_name: str
    source_row_label: str
    source_column_label: str
    source_cell_reference: str
    source_locator_json: dict[str, Any]
    extraction_warnings: str | None
    confidence_label: str


@dataclass(frozen=True)
class ParsedPdf:
    raw_text: str
    page_count: int
    table_count: int
    reporting_currency: str | None
    reporting_scale: str | None
    scanned_pages: tuple[int, ...]
    candidates: tuple[PdfTableCandidate, ...]
    warnings: tuple[str, ...]


def ensure_pdf_source(db: Session) -> Source:
    source = db.scalar(select(Source).where(Source.name == PDF_SOURCE_NAME))
    if source is None:
        source = Source(
            name=PDF_SOURCE_NAME,
            source_type="manual_financial_upload",
            base_url=None,
            reliability_score=70,
            active=True,
        )
        db.add(source)
        db.commit()
        db.refresh(source)
    return source


def validate_pdf_upload(filename: str | None, content_type: str | None, content: bytes) -> ValidatedPdfUpload:
    safe_filename = _safe_filename(filename)
    mime_type = (content_type or "").split(";", maxsplit=1)[0].strip().lower()
    if not safe_filename.lower().endswith(".pdf") or mime_type not in ALLOWED_PDF_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")
    if len(content) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF is too large. Maximum size is 40 MB.")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Uploaded file does not have a valid PDF signature.")
    return ValidatedPdfUpload(
        filename=safe_filename,
        mime_type="application/pdf",
        content=content,
        sha256=hashlib.sha256(content).hexdigest(),
    )


def validate_pdf_source_url(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    normalized = value.strip()
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise HTTPException(
            status_code=422,
            detail="Official source URL must be HTTP(S) and must not embed credentials.",
        )
    return normalized


def parse_pdf_page_ranges(
    value: str | None,
    *,
    max_targeted_pages: int = MAX_TARGETED_PAGES,
) -> tuple[int, ...] | None:
    if value is None or not value.strip():
        return None
    pages: set[int] = set()
    for item in value.split(","):
        token = item.strip()
        match = re.fullmatch(r"(\d+)(?:\s*-\s*(\d+))?", token)
        if match is None:
            raise HTTPException(status_code=422, detail="Page ranges must look like 465-470, 542.")
        start = int(match.group(1))
        end = int(match.group(2) or start)
        if start < 1 or end < start:
            raise HTTPException(status_code=422, detail="Page ranges must contain positive ascending pages.")
        if end - start + 1 > max_targeted_pages:
            raise HTTPException(status_code=422, detail=f"Select at most {max_targeted_pages} pages.")
        pages.update(range(start, end + 1))
        if len(pages) > max_targeted_pages:
            raise HTTPException(
                status_code=422,
                detail=f"Targeted extraction is limited to {max_targeted_pages} pages per upload.",
            )
    return tuple(sorted(pages))


def parse_pdf_financial_tables(
    content: bytes,
    *,
    page_numbers: tuple[int, ...] | None = None,
    period_type: str = "annual",
) -> ParsedPdf:
    try:
        payload = run_pdf_job("financial", content, {"page_numbers": page_numbers, "period_type": period_type})
        return TypeAdapter(ParsedPdf).validate_python(payload)
    except PdfJobError as error:
        raise HTTPException(error.status_code, str(error)) from None
    except ValidationError:
        raise HTTPException(422, "PDF parser returned an invalid result.") from None


def _parse_pdf_financial_tables(
    content: bytes,
    *,
    page_numbers: tuple[int, ...] | None = None,
    period_type: str = "annual",
) -> ParsedPdf:
    try:
        import pdfplumber

        with pdfplumber.open(BytesIO(content)) as pdf:
            total_page_count = len(pdf.pages)
            if total_page_count > MAX_PDF_PAGES:
                raise HTTPException(
                    status_code=413,
                    detail=f"PDF has too many pages. Maximum supported page count is {MAX_PDF_PAGES}.",
                )
            if page_numbers is None and total_page_count > MAX_FULL_SCAN_PAGES:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Reports above {MAX_FULL_SCAN_PAGES} pages require targeted page ranges. "
                        "Select the consolidated statements and relevant notes."
                    ),
                )

            scanned_pages = page_numbers or tuple(range(1, total_page_count + 1))
            if len(scanned_pages) > MAX_TARGETED_PAGES and page_numbers is not None:
                raise HTTPException(
                    status_code=422,
                    detail=f"Targeted extraction is limited to {MAX_TARGETED_PAGES} pages per upload.",
                )
            if any(page_number < 1 or page_number > total_page_count for page_number in scanned_pages):
                raise HTTPException(status_code=422, detail="A targeted page is outside the PDF page count.")

            page_texts: list[str] = []
            extracted: list[PdfTableCandidate] = []
            warnings: set[str] = set()
            table_count = 0
            reporting_currency: str | None = None
            reporting_scale: str | None = None
            if page_numbers is not None:
                warnings.add("targeted_page_scan")

            for page_number in scanned_pages:
                page = pdf.pages[page_number - 1]
                page_text = page.extract_text() or ""
                page_texts.append(f"[Page {page_number}]\n{page_text.strip()}".rstrip())
                page_currency, page_scale, _ = _page_reporting_unit(page, page_text)
                reporting_currency = reporting_currency or page_currency
                reporting_scale = reporting_scale or page_scale
                regions = _statement_regions(page)
                if len(regions) > 1:
                    warnings.add("facing_page_regions")
                inherited_section = None
                page_table_number = 0
                for region_number, region in enumerate(regions, start=1):
                    region_text = region.extract_text() or ""
                    region_currency, region_scale, unit_evidence = _page_reporting_unit(region, region_text)
                    section = _page_section(region_text)
                    has_heading = any(_STATEMENT_HEADING.match(line.strip()) for line in region_text.splitlines())
                    if not has_heading and len(regions) > 1 and inherited_section:
                        section = inherited_section
                    if has_heading:
                        inherited_section = section
                    tables = region.find_tables()
                    table_count += len(tables)
                    extracted.extend(
                        _statement_line_candidates(
                            page_text=region_text,
                            page_number=page_number,
                            section=section,
                            currency=region_currency,
                            scale=region_scale,
                            page_width=float(page.width),
                            page_height=float(page.height),
                            page=region,
                            region_number=region_number if len(regions) > 1 else None,
                            warnings=warnings,
                            unit_evidence=unit_evidence,
                            period_type=period_type,
                        )
                    )
                    for table in tables:
                        page_table_number += 1
                        matrix = table.extract()
                        if not matrix:
                            continue
                        extracted.extend(
                            _table_candidates(
                                matrix=matrix, rows=table.rows, table_bbox=table.bbox,
                                page_number=page_number, page_width=float(page.width),
                                page_height=float(page.height), table_number=page_table_number,
                                section=section, currency=region_currency, scale=region_scale,
                                period_type=period_type, page_text=region_text,
                                region_number=region_number if len(regions) > 1 else None,
                                unit_evidence=unit_evidence,
                            )
                        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Unable to parse the uploaded PDF.") from exc

    if not any(text.partition("\n")[2].strip() for text in page_texts):
        warnings.add("no_extractable_text")
    if table_count == 0:
        warnings.add("no_tables_detected")
    extracted = _consolidate_candidates(extracted)
    if not extracted:
        warnings.add("no_supported_financial_cells_detected")
    if reporting_currency is None:
        warnings.add("reporting_currency_missing")
    if reporting_scale is None:
        warnings.add("reporting_scale_missing")

    return ParsedPdf(
        raw_text="\n\n".join(page_texts),
        page_count=total_page_count,
        table_count=table_count,
        reporting_currency=reporting_currency,
        reporting_scale=reporting_scale,
        scanned_pages=tuple(scanned_pages),
        candidates=tuple(extracted),
        warnings=tuple(sorted(warnings)),
    )


def ingest_pdf_financials(
    db: Session,
    *,
    company: Company,
    source: Source,
    upload: ValidatedPdfUpload,
    parsed: ParsedPdf,
    document_type: str,
    title: str | None,
    published_at: datetime | None,
    source_url: str | None = None,
) -> PdfFinancialExtractionResultRead:
    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(status_code=422, detail="Unsupported filing document type.")

    content_hash = f"pdf-filing:{company.id}:{upload.sha256}"
    if db.scalar(select(RawDocument.id).where(RawDocument.content_hash == content_hash)) is not None:
        raise HTTPException(status_code=409, detail="This PDF has already been uploaded for the company.")

    raw_document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type=document_type,
        title=(title or upload.filename).strip()[:500] or upload.filename,
        url=source_url,
        published_at=published_at,
        raw_text=parsed.raw_text,
        raw_payload_json={
            "source_kind": "pdf_filing_upload",
            "original_filename": upload.filename,
            "mime_type": upload.mime_type,
            "file_size_bytes": len(upload.content),
            "sha256": upload.sha256,
            "parser": PDF_EXTRACTION_METHOD,
            "page_count": parsed.page_count,
            "reporting_currency": parsed.reporting_currency,
            "reporting_scale": parsed.reporting_scale,
            "source_url": source_url,
            "publication_date_basis": "provided" if published_at is not None else "unknown",
            "extraction_scope": "targeted_pages" if len(parsed.scanned_pages) < parsed.page_count else "full_document",
            "scanned_pages": list(parsed.scanned_pages),
            "warnings": list(parsed.warnings),
        },
        content_hash=content_hash,
    )
    db.add(raw_document)
    db.flush()

    asset = DocumentAsset(
        raw_document_id=raw_document.id,
        original_filename=upload.filename,
        mime_type=upload.mime_type,
        size_bytes=len(upload.content),
        sha256=upload.sha256,
        page_count=parsed.page_count,
        content=upload.content,
    )
    db.add(asset)

    candidates = [
        FinancialExtractionCandidate(
            company_id=company.id,
            raw_document_id=raw_document.id,
            metric_code=item.metric_code,
            reported_label=item.reported_label,
            value=item.value,
            unit=item.unit,
            fiscal_year=item.fiscal_year,
            period_type=item.period_type,
            source_text=item.source_text,
            source_line_number=None,
            source_page=item.source_page,
            source_section=item.source_section,
            source_table_name=item.source_table_name,
            source_row_label=item.source_row_label,
            source_column_label=item.source_column_label,
            source_cell_reference=item.source_cell_reference,
            source_locator_json=item.source_locator_json,
            extraction_warnings=item.extraction_warnings,
            extraction_method=PDF_EXTRACTION_METHOD,
            confidence_label=item.confidence_label,
            review_status="needs_review",
        )
        for item in parsed.candidates
    ]
    db.add_all(candidates)

    workflow = db.scalar(
        select(CompanySetupWorkflow).where(CompanySetupWorkflow.company_id == company.id)
    )
    if workflow is not None:
        workflow.filing_status = "complete"
        if candidates:
            workflow.financial_extraction_status = "needs_review"
            workflow.current_step = "financial_review"

    db.commit()
    db.refresh(asset)
    for candidate in candidates:
        db.refresh(candidate)

    return PdfFinancialExtractionResultRead(
        raw_document_id=raw_document.id,
        asset=asset,
        page_count=parsed.page_count,
        scanned_page_count=len(parsed.scanned_pages),
        scanned_pages=list(parsed.scanned_pages),
        table_count=parsed.table_count,
        created_count=len(candidates),
        skipped_existing_count=0,
        warnings=list(parsed.warnings),
        candidates=candidates,
    )


def _safe_filename(filename: str | None) -> str:
    normalized = (filename or "filing.pdf").replace("\\", "/").replace("\x00", "")
    normalized = re.sub(r"[\x00-\x1f\x7f]", "", normalized)
    basename = PurePath(normalized).name.strip()
    if not basename:
        return "filing.pdf"
    return basename[:255]


def _reporting_unit(text: str) -> tuple[str | None, str | None]:
    # Read unit declarations, not incidental amounts in note prose. Some Indian
    # PDFs encode the rupee glyph as a backtick. An unreadable Latin-letter glyph
    # or an Indian numbering scale alone is not sufficient currency evidence.
    lines = text.splitlines()[:20]
    for line in lines:
        scale_match = _SCALE_PATTERN.search(line)
        if not scale_match or not re.search(r"\bin\b|\bamounts?\b|omitted|^\s*\([`₹]", line, re.I):
            continue
        scale = scale_match.group(1).lower().rstrip("s")
        scale = "thousand" if scale == "000" else scale
        currency_match = _CURRENCY_PATTERN.search(line)
        if currency_match:
            return currency_match.group(1).upper(), scale
        if re.search(r"Indian Rupees?|\bRs\.?|[₹`]|\bINR\b", line, re.I):
            return "INR", scale
        if "omitted" in line.lower() and any(re.fullmatch(r"\s*[`₹](?:\s+[`₹])*\s*", item) for item in lines):
            return "INR", scale
        return None, scale
    match = _UNIT_PATTERN.search(text)
    return (match.group("currency").upper(), None) if match else (None, None)


def _statement_regions(page: Any) -> list[Any]:
    """Split demonstrated facing pages, never a landscape table just for being wide."""
    if page.width < page.height * 1.2:
        return [page]
    mid = float(page.width) / 2
    # A real gutter must remain empty through the statement body.
    if any(char["x0"] < mid + 6 and char["x1"] > mid - 6
           and page.height * .12 < char["top"] < page.height * .9
           and char.get("text", "").strip() for char in page.chars):
        return [page]
    regions = [page.crop((0, 0, mid, page.height)), page.crop((mid, 0, page.width, page.height))]
    texts = [region.extract_text() or "" for region in regions]
    if not all(_reporting_unit(text)[1] for text in texts):
        return [page]
    folios = []
    for region in regions:
        folios.append({int(word["text"]) for word in region.extract_words()
                       if word["top"] > page.height * .92 and re.fullmatch(r"\d{1,4}", word["text"])})
    consecutive_folios = any(left + 1 in folios[1] for left in folios[0])
    years = [_statement_years(text) for text in texts]
    repeated_headers = len(years[0]) >= 2 and years[0] == years[1]
    return regions if consecutive_folios or repeated_headers else [page]


def _page_reporting_unit(page: Any, text: str) -> tuple[str | None, str | None, dict | None]:
    """Recognize observed embedded symbol encodings; never treat a bare C/I/J as INR."""
    currency, scale = _reporting_unit(text)
    if currency or not scale:
        return currency, scale, None
    header = "\n".join(text.splitlines()[:20])
    tokens = set(re.findall(r"(?<!\w)([CIJ])(?=\s+in\b)|^\s*([CIJ])(?:\s+[CIJ])*\s*$", header, re.M))
    glyphs = {part for token in tokens for part in token if part}
    if not glyphs:
        return currency, scale, None
    embedded = _embedded_rupee_fonts(page)
    symbols = [{key: char[key] for key in ("text", "fontname", "x0", "x1", "top", "bottom")}
               for char in page.chars if char.get("fontname") in embedded and char.get("text") in glyphs
               and char["top"] < page.height * .25]
    if not symbols:
        return currency, scale, None
    return "INR", scale, {"basis": "embedded_rupee_symbol_font", "currency": "INR",
                          "scale": scale, "symbols": symbols, "review_required": True}


def _embedded_rupee_fonts(page: Any) -> set[str]:
    from pdfminer.pdftypes import resolve1
    from pdfminer.psparser import literal_name

    embedded = set()
    for font in resolve1(page.page_obj.resources.get("Font", {})).values():
        font = resolve1(font)
        name = literal_name(font.get("BaseFont"))
        if not isinstance(name, str) or re.sub(r"^[A-Z]{6}\+", "", name) != "ITFRupee":
            continue
        descendants = resolve1(font.get("DescendantFonts", []))
        details = resolve1(descendants[0]) if descendants else font
        descriptor = resolve1(details.get("FontDescriptor", {}))
        if any(descriptor.get(key) is not None for key in ("FontFile", "FontFile2", "FontFile3")):
            embedded.add(name)
    return embedded


def _eps_rupee_symbols(page: Any | None, line: str) -> tuple[str, dict | None]:
    """Repair observed EPS glyphs only with physical embedded-font evidence."""
    glyphs = set(re.findall(r"(?<!\w)([CHIJ])(?=[\d)])", line))
    if page is None or not glyphs:
        return line, None
    matches = page.search(re.escape(line).replace(r"\ ", r"\s+"), regex=True, case=True)
    if len(matches) != 1:
        return line, None
    symbols = [char for char in matches[0].get("chars", []) if char.get("text") in glyphs]
    embedded = _embedded_rupee_fonts(page)
    if len(symbols) != sum(line.count(glyph) for glyph in glyphs) or any(
            char.get("fontname") not in embedded for char in symbols):
        return line, None
    evidence = {"basis": "embedded_rupee_symbol_font", "currency": "INR", "unit": "INR/share",
                "symbols": [{key: char[key] for key in ("text", "fontname", "x0", "x1", "top", "bottom")}
                            for char in symbols], "review_required": True}
    return re.sub(r"(?<!\w)[CHIJ](?=[\d)])", "₹", line), evidence


def _without_margin_number(page: Any | None, line: str, page_text: str, years: tuple[int, ...]) -> tuple[str, dict | None]:
    """Ignore a repeated navigation number only outside proven year columns."""
    suffix = re.search(r" (\d{2})$", line)
    if page is None or suffix is None:
        return line, None
    trimmed = line[:suffix.start()]
    parsed = _statement_row_values(trimmed, len(years), page_text)
    if parsed is None:
        return line, None
    header = next((value for value in page_text.splitlines()[:80]
        if tuple(dict.fromkeys(_end_year(m) for m in _YEAR_PATTERN.finditer(value))) == years), None)
    if header is None:
        return line, None
    headers = page.search(re.escape(header).replace(r"\ ", r"\s+"), regex=True, case=True)
    rows = page.search(re.escape(trimmed).replace(r"\ ", r"\s+"), regex=True, case=True)
    if len(headers) != 1 or len(rows) != 1:
        return line, None
    header_box, row_box = headers[0], rows[0]
    columns = []
    for year in years:
        matches = [match for match in page.search(rf"\b{year}\b", regex=True)
                   if abs(match['top'] - header_box['top']) < 3
                   and header_box['x0'] <= match['x0'] < match['x1'] <= header_box['x1']]
        if len(matches) != 1:
            return line, None
        columns.append(matches[0]['x1'])
    if abs(header_box['x1']-columns[-1]) > 3:
        return line, None
    if columns != sorted(columns) or any(right-left < 25 for left, right in zip(columns, columns[1:])):
        return line, None
    words = page.extract_words()
    for value, right in zip(parsed[1], columns, strict=True):
        matches = [word for word in words if word['text'] == value and abs(word['x1']-right) <= 12
                   and abs(word['top']-row_box['top']) < 3]
        if len(matches) != 1:
            return line, None
    left, _, right, _ = page.bbox
    margin = [word for word in words if re.fullmatch(r"\d{2}", word['text'])
              and word['x0'] > max(columns[-1]+15, left+(right-left)*.94)
              and word['top'] > header_box['bottom']]
    target = [word for word in margin if word['text'] == suffix.group(1)
              and row_box['top']-3 <= word['top'] <= row_box['bottom']]
    if len(target) != 1:
        return line, None
    chosen = target[0]
    aligned = sorted((word for word in margin if abs(word['x0']-chosen['x0']) < 4
                      and abs(word['height']-chosen['height']) < 1), key=lambda w: w['top'])
    numbers = [int(word['text']) for word in aligned]
    if len(numbers) < 3 or numbers != list(range(numbers[0], numbers[0]+len(numbers))):
        return line, None
    if any(b['top']-a['top'] < chosen['height']*2 for a,b in zip(aligned,aligned[1:])):
        return line, None
    return trimmed, {**{key:chosen[key] for key in ('text','x0','x1','top','bottom')},
        'basis':'repeated_right_margin_outside_year_columns', 'year_column_right_edges':columns,
        'review_required':True}


def _page_section(text: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if _STATEMENT_HEADING.match(line):
            return re.sub(r"\bbal\s+ance\b", "Balance", line, flags=re.I)[:255]
    for cleaned in lines:
        if _UNIT_PATTERN.search(cleaned) or _INDIA_SCALE_PATTERN.search(cleaned):
            continue
        return cleaned[:255]
    return None


def _statement_line_candidates(
    *,
    page_text: str,
    page_number: int,
    section: str | None,
    currency: str | None,
    scale: str | None,
    page_width: float,
    page_height: float,
    page: Any | None,
    period_type: str = "annual",
    region_number: int | None = None,
    warnings: set[str] | None = None,
    unit_evidence: dict | None = None,
) -> list[PdfTableCandidate]:
    years = _statement_years(page_text)
    if not years:
        return []
    lines = _stitch_statement_lines(page_text.splitlines(), len(years))
    candidates: list[PdfTableCandidate] = []
    attribution = "profit"
    liability_scope = None
    statement_block = None
    eps_context = False
    share_context = False
    share_scale = None
    share_scale_line = 0
    row_occurrences: dict[str, int] = {}
    for line_number, (source_line, original_line) in enumerate(lines, start=1):
        normalized_line = source_line.lower()
        if re.fullmatch(r"\((?:in )?['‘]?000s?\)", normalized_line):
            share_scale, share_scale_line = "thousand", line_number
        elif re.match(r"\d+\.\s+\D", source_line) or line_number - share_scale_line > 8:
            share_scale = None
        block = re.sub(r"^(?:[iv]+[. ]+)\s*", "", normalized_line).strip()
        blocks = {"capital and liabilities": "liabilities", "assets": "assets",
                  "income": "income", "expenditure": "expenses", "expenses": "expenses",
                  "profit": "profit", "profit/(loss)": "profit", "appropriations": "appropriations",
                  "appropriations/transfers": "appropriations"}
        if block in blocks:
            statement_block = blocks[block]
        if re.search(r"earnings per (?:equity )?share", normalized_line) and not re.search(r"weighted|computed|dividing", normalized_line):
            eps_context = True
            share_context = False
        if re.match(r"weighted average number of equity shares used as denominator$", normalized_line):
            share_context = True
        if re.match(r"(?:other|total) comprehensive income", normalized_line):
            attribution = "comprehensive"
        elif re.match(r"(?:net )?profit.*attributable to", normalized_line):
            attribution = "profit"
            # This is the group total repeated as an attribution heading.
            if re.search(r"attributable to\s*:", normalized_line):
                continue
        if normalized_line in {"non-current liabilities", "non current liabilities", "non‑current liabilities"}:
            liability_scope = "noncurrent"
        elif normalized_line == "current liabilities":
            liability_scope = "current"
        elif normalized_line in {"assets", "equity", "current assets", "non-current assets"}:
            liability_scope = None
        row_unit_evidence = None
        margin_evidence = None
        if eps_context:
            source_line, row_unit_evidence = _eps_rupee_symbols(page, source_line)
        parsed_row = _statement_row_values(source_line, len(years), page_text)
        if parsed_row is None and "cash flow" in (section or "").lower():
            source_line, margin_evidence = _without_margin_number(page, source_line, page_text, years)
            if margin_evidence:
                parsed_row = _statement_row_values(source_line, len(years), page_text)
        if parsed_row is None:
            possible_label = re.split(r"\s+(?=[\d(])", source_line, maxsplit=1)[0]
            if warnings is not None and _metric_for_statement_line(possible_label, section):
                warnings.add("ambiguous_statement_row_skipped")
            continue
        source_label, value_tokens = parsed_row
        metric = _metric_for_statement_line(source_label, section, liability_scope=liability_scope,
            statement_block=statement_block, eps_context=eps_context, share_context=share_context)
        if metric is None:
            continue
        metric_code, reported_label, source_row_label = metric
        if metric_code == "net_income" and source_label.lower() == "profit after tax" and re.search(r"share of profit.*associate", page_text, re.I):
            metric_code, reported_label = "profit_after_tax_before_associates", "Profit after tax before associates"
        if attribution != "profit" and metric_code in {"net_income_parent", "net_income_nci"}:
            continue
        occurrence = row_occurrences.get(original_line, 0)
        row_occurrences[original_line] = occurrence + 1
        row_bbox = _row_bbox(page, source_line if margin_evidence else original_line, occurrence=occurrence)

        prefixed = any(token.startswith(("₹", "`")) for token in value_tokens)
        unit = _candidate_unit(metric_code, currency, scale, source_label=source_label, page_text=page_text,
                               share_context=share_context, share_scale=share_scale)
        if prefixed:
            if metric_code not in {"basic_eps", "diluted_eps"} or unit not in {None, "INR/share"}:
                if warnings is not None:
                    warnings.add("conflicting_or_unsupported_value_currency")
                continue
            unit = "INR/share"
        applied_unit_evidence = row_unit_evidence or unit_evidence

        for value_index, (fiscal_year, value_token) in enumerate(zip(years, value_tokens, strict=True), start=1):
            value = _number(value_token.rstrip("*").lstrip("₹`"))
            if value is None:
                continue
            item_warnings = _candidate_warnings(metric_code, unit)
            if applied_unit_evidence and not metric_code.endswith("shares"):
                item_warnings.append("currency_from_embedded_font_requires_review")
            if margin_evidence:
                item_warnings.append("margin_number_excluded_requires_review")
            if row_bbox is None:
                item_warnings.append("row_bounding_box_missing")
            region_ref = f":S{region_number}" if region_number else ""
            cell_reference = f"P{page_number}{region_ref}:L{line_number}:Y{fiscal_year}"
            candidates.append(
                PdfTableCandidate(
                    metric_code=metric_code,
                    reported_label=reported_label,
                    value=value,
                    unit=unit,
                    fiscal_year=fiscal_year,
                    period_type=period_type,
                    source_text=original_line.strip(),
                    source_page=page_number,
                    source_section=section,
                    source_table_name=section or "PDF statement rows",
                    source_row_label=source_row_label,
                    source_column_label=f"FY{fiscal_year}",
                    source_cell_reference=cell_reference,
                    source_locator_json={
                        "type": "pdf_text_row",
                        "page": page_number,
                        "line": line_number,
                        "value_index": value_index,
                        "fiscal_year": fiscal_year,
                        "cell_reference": cell_reference,
                        "coordinate_system": "pdfplumber_top_left_points",
                        "page_width": page_width,
                        "page_height": page_height,
                        "bounding_box": row_bbox,
                        **({"region": region_number} if region_number else {}),
                        **({"share_unit_header": {"scale": share_scale, "line": share_scale_line}}
                           if share_scale and metric_code.endswith("shares") else {}),
                        **({"unit_evidence": applied_unit_evidence} if applied_unit_evidence and not metric_code.endswith("shares") else {}),
                        **({"excluded_margin_number": margin_evidence} if margin_evidence else {}),
                    },
                    extraction_warnings=";".join(item_warnings) or None,
                    confidence_label="high" if not item_warnings else "medium",
                )
            )
    return candidates


def _statement_row_values(line: str, count: int, page_text: str) -> tuple[str, list[str]] | None:
    # Match complete tokens at the end of a row. Never take arbitrary numbers
    # from the opposite printed page, an embedded note, a percentage or prose.
    cleaned = re.sub(r"\(refer\s+note\s+\d+(?:\.\d+)?(?:\([a-z]\))?\)", "", line, flags=re.I).rstrip()
    unit_spans = [match.span() for match in re.finditer(r"\(\s*(?:in\s+)?['‘]?000s?\s*\)", cleaned, re.I)]
    matches = [match for match in _STATEMENT_VALUE_TOKEN_PATTERN.finditer(cleaned)
               if not any(start <= match.start() < end for start, end in unit_spans)]
    suffix = []
    end = len(cleaned)
    for match in reversed(matches):
        if cleaned[match.end():end].strip():
            break
        suffix.insert(0, match)
        end = match.start()
    if len(suffix) < count:
        return None
    extra = suffix[:-count]
    if extra:
        note = cleaned[extra[0].start():extra[-1].end()]
        if not re.search(r"\bnotes?\b|\bschedule", page_text[:1500], re.I) or not re.fullmatch(r"\d{1,2}(?:\.\d{1,2})?(?:\s*\(\d{1,2}\))?", note):
            return None
    label = cleaned[:suffix[0].start()].strip()
    if re.search(r"\bnotes?\b|\bschedule", page_text[:1500], re.I):
        label = re.sub(r"\s+\d{1,2}[A-Z]$", "", label)
    return label, [match.group() for match in suffix[-count:]]


def _statement_years(page_text: str) -> tuple[int, ...]:
    header_lines = page_text.splitlines()[:80]
    for line in header_lines:
        line_lower = line.lower()
        if not any(marker in line_lower for marker in ("particulars", "march 31", "year ended", "as at")):
            continue
        line_years: list[int] = []
        for match in _YEAR_PATTERN.finditer(line):
            year = _end_year(match)
            if year not in line_years:
                line_years.append(year)
        if len(line_years) >= 2:
            return tuple(line_years)

    for line in header_lines:
        line_years: list[int] = []
        for match in _YEAR_PATTERN.finditer(line):
            year = _end_year(match)
            if year not in line_years:
                line_years.append(year)
        if len(line_years) >= 2:
            return tuple(line_years)

    years: list[int] = []
    for line in header_lines:
        if "year ended" not in line.lower() and "as at" not in line.lower():
            continue
        for match in _YEAR_PATTERN.finditer(line):
            year = _end_year(match)
            if year not in years:
                years.append(year)
    return tuple(years)


def _end_year(match: re.Match) -> int:
    start = int(match.group(1))
    end = match.group(2)
    if end is None:
        return start
    result = int(end) if len(end) == 4 else start // 100 * 100 + int(end)
    if result < start:
        result += 100
    # Only consecutive year ranges establish a fiscal-year end. An ISO date
    # such as 2026-03-31 must not turn into FY2103.
    return result if result == start + 1 else start


def _stitch_statement_lines(lines: list[str], value_count: int) -> list[tuple[str, str]]:
    """Join only observed label continuations, keeping original text for geometry."""
    stitched: list[tuple[str, str]] = []
    lines = [re.sub(r"\s+", " ", line).strip() for line in lines]
    index = 0
    while index < len(lines):
        line = lines[index]
        parts = [line]
        supported = line.lower().startswith(("weighted average number of equity shares",
            "consolidated profit/(loss) for the year attributable to the",
            "net profit for the year (before"))
        if supported:
            for following in lines[index + 1:index + 3]:
                continuation = re.match(r"^(?:computation of (?:basic|diluted) eps|diluted eps|"
                    r"share(?:\s|$)|group\s|associates and minority interest\)|minority interest\)|interest\))",
                    following, re.I)
                values_only = re.fullmatch(r"[\d,.()\s]+", following)
                if not continuation and not values_only:
                    break
                parts.append(following)
        original = "\n".join(parts)
        # A wrapped label may follow its values in PDF reading order. Reorder
        # only when exactly one complete value suffix exists across these lines.
        parsed = [_statement_row_values(part, value_count, "") for part in parts]
        populated = [i for i, row in enumerate(parsed) if row is not None]
        if len(parts) > 1 and len(populated) == 1:
            row_index = populated[0]
            label, values = parsed[row_index]
            labels = [label if i == row_index else part for i, part in enumerate(parts)]
            stitched.append((" ".join(labels + values).strip(), original))
        else:
            stitched.extend((part, part) for part in parts)
        index += len(parts)
    return stitched


def _metric_for_statement_line(
    source_line: str,
    section: str | None,
    *,
    liability_scope: str | None = None,
    statement_block: str | None = None,
    eps_context: bool = False,
    share_context: bool = False,
) -> tuple[str, str, str] | None:
    normalized = re.sub(r"\s+", " ", source_line.strip().lower())
    normalized = normalized.replace("–", "-").replace("‑", "-")
    normalized = re.sub(r"^(?:[-•]\s+|[a-z]\)\s+)", "", normalized)
    normalized = re.sub(r"\s*\(['‘]?nci['’]?\)\s*$", "", normalized)
    normalized = re.sub(r"\s*\((?:in )?(?:thousands?|millions?|billions?|actuals?|numbers?)\)\s*$", "", normalized)
    normalized = re.sub(r"\s*[*^]+$", "", normalized).strip()
    section_lower = (section or "").lower()
    profit_statement = "profit and loss" in section_lower

    if normalized.startswith(("weighted average number of equity shares", "weighted average number of shares",
                              "weighted average shares outstanding")):
        if "diluted" in normalized:
            return "diluted_shares", "Diluted shares", source_line
        if "basic" in normalized:
            return "basic_shares", "Basic shares", source_line
        return None
    if share_context and normalized in {"basic eps", "diluted eps"}:
        code = "basic_shares" if normalized.startswith("basic") else "diluted_shares"
        return code, code.replace("_", " ").capitalize(), source_line
    if eps_context and re.fullmatch(r"(?:[12]\) )?(basic|diluted)(?: earnings per share| eps)?(?:\s*\([^)]*\))?\d?", normalized):
        code = "diluted_eps" if "diluted" in normalized else "basic_eps"
        return code, code.replace("_", " ").capitalize(), source_line
    if normalized == "total" and statement_block in {"liabilities", "assets", "income", "expenses"}:
        code = {"liabilities": "total_liabilities_equity", "assets": "total_assets",
                "income": "total_income", "expenses": "total_expenses"}[statement_block]
        return code, code.replace("_", " ").capitalize(), source_line
    if normalized == "deferred payment liabilities" and liability_scope:
        code = "deferred_payment_liabilities_" + liability_scope
        return code, "Deferred payment liabilities: " + liability_scope, source_line
    explicit = {
        "total current assets": "current_assets", "total current liabilities": "current_liabilities",
        "total liabilities": "total_liabilities", "total equity and liabilities": "total_liabilities_equity",
        "total capital and liabilities": "total_liabilities_equity", "total equity": "total_equity_including_nci",
        "equity share capital": "share_capital", "share capital": "share_capital", "other equity": "other_equity",
        "capital": "share_capital", "reserves and surplus": "reserves_surplus", "reserves & surplus": "reserves_surplus",
        "deposits": "deposits", "balances with banks and money at call and short notice": "balances_with_banks",
        "balances with banks and money at call & short notice": "balances_with_banks", "investments": "investments",
        "advances": "advances", "fixed assets": "fixed_assets", "other assets": "other_assets",
        "other liabilities and provisions": "other_liabilities_provisions", "policyholders' funds": "policyholder_funds",
        "goodwill on consolidation": "goodwill", "employees stock options outstanding": "employee_awards",
        "employees stock options / units outstanding": "employee_awards", "employees stock options/units outstanding": "employee_awards",
        "interest earned": "interest_earned", "interest expended": "interest_expended",
        "operating expenses": "operating_expenses", "provisions and contingencies": "provisions_contingencies",
        "other income": "other_income", "total income": "total_income", "total expenses": "total_expenses",
        "total expenditure": "total_expenses", "current tax": "current_tax", "deferred tax": "deferred_tax",
        "value of sales & services (revenue)": "gross_revenue_including_gst", "less: gst recovered": "gst_recovered",
        "exceptional items (net)": "exceptional_items_expense",
        "profit before share of profit / (loss) of associates / joint ventures and tax": "profit_before_associates_tax",
        "share of profit / (loss) of associate and joint ventures": "share_of_associate_profit",
        "share of profit / (loss) of associates and joint ventures": "share_of_associate_profit",
        "add: share of profit in associates": "share_of_associate_profit",
        "add: share in profit of associates": "share_of_associate_profit",
        "consolidated net profit for the year before minority interest": "group_profit",
        "net profit for the year before deducting minority interest": "group_profit",
        "net profit for the year (before share in profit of associates and minority interest)": "profit_before_associates_nci",
        "net profit for the year (before adjustment for share in profit of associates and minority interest)": "profit_before_associates_nci",
        "consolidated net profit for the year attributable to the group": "net_income_parent",
        "consolidated profit/(loss) for the year attributable to the group": "net_income_parent",
        "net profit for the group": "net_income_parent",
        "dividend paid during the year": "dividends", "dividend for the current year": "dividend_appropriation",
    }
    balance_only = {"share_capital", "reserves_surplus", "deposits", "balances_with_banks", "investments",
                    "advances", "fixed_assets", "other_assets", "other_liabilities_provisions", "policyholder_funds", "employee_awards", "goodwill"}
    if normalized in explicit:
        code = explicit[normalized]
        if code in balance_only and "balance sheet" not in section_lower:
            return None
        if "cash flow" in section_lower:
            return None
        return code, code.replace("_", " ").capitalize(), source_line
    if "cash flow" in section_lower:
        flow_label = re.sub(r"\s*\((?:[abc]|a\+b\+c)\)$", "", normalized).strip()
        cash_flows = {
            "net cash flow from operating activities": "operating_cash_flow",
            "net cash generated from operating activities": "operating_cash_flow",
            "net cash used in investing activities": "investing_cash_flow",
            "net cash flow used in investing activities": "investing_cash_flow",
            "net cash used in financing activities": "financing_cash_flow",
            "net cash flow used in financing activities": "financing_cash_flow",
            "net cash flow from / (used in) financing activities": "financing_cash_flow",
            "purchase of property, plant and equipment": "ppe_cash_outflow",
            "purchase of property, plant and equipment and capital work-in-progress": "ppe_cash_outflow",
            "purchase of intangible assets": "intangibles_cash_outflow",
            "purchase of intangible assets and intangible assets under development": "intangibles_cash_outflow",
            "payment towards spectrum": "spectrum_cash_outflow",
            "payment towards spectrum (including deferred payment liability)": "spectrum_cash_outflow",
            "expenditure for property, plant and equipment, spectrum and other intangible assets": "ppe_spectrum_intangibles_cash_outflow",
            "net increase in cash and cash equivalents": "cash_change",
            "net increase in the cash and cash equivalents": "cash_change",
            "net increase in the cash and cash equivalents during the year": "cash_change",
            "effect of exchange rate on the cash and cash equivalents": "cash_fx_effect",
            "opening balance of cash and cash equivalents": "cash_flow_cash_opening",
            "closing balance of cash and cash equivalents": "cash_flow_cash_closing",
        }
        if flow_label in cash_flows:
            code = cash_flows[flow_label]
            return code, code.replace("_", " ").capitalize(), source_line
    if normalized == "cash and balances with reserve bank of india":
        return "cash_and_balances_with_rbi", "Cash and balances with Reserve Bank of India", source_line
    if normalized in {"borrowings", "total borrowings"}:
        code = f"{liability_scope}_borrowings" if liability_scope and normalized == "borrowings" else "borrowings"
        return code, code.replace("_", " ").capitalize(), source_line
    if normalized in {"lease liabilities", "operating lease liabilities"} and liability_scope:
        code = f"{liability_scope}_lease_liabilities"
        return code, code.replace("_", " ").capitalize(), source_line
    if normalized.startswith("cash and cash equivalents") and ("cash flow" in section_lower):
        if re.search(r"\b(?:beginning|opening)\b", normalized):
            return "cash_flow_cash_opening", "Cash flow statement opening cash", source_line
        if re.search(r"\b(?:end|closing)\b", normalized):
            return "cash_flow_cash_closing", "Cash flow statement closing cash", source_line
        return None
    if profit_statement and normalized in {"profit for the year", "profit for the period"}:
        return "group_profit", "Reported group profit", source_line

    contextual_patterns: tuple[tuple[str, str, str], ...] = (
        ("customers' bills discounted", "bills_discounted", "Customers' bills discounted"),
        ("customers’ bills discounted", "bills_discounted", "Customers' bills discounted"),
        ("investments accounted using equity method", "investments_in_associates", "Investments accounted using equity method"),
        ("interest and bank charges", "finance_costs", "Interest and bank charges"),
        ("finance costs", "finance_costs", "Finance costs"),
        ("total tax expense", "tax_expense", "Total tax expense"),
        ("profit before tax", "pre_tax_income", "Profit before tax"),
        ("total equity attributable to equity holders of the parent", "book_equity", "Equity attributable to parent"),
        ("total assets", "total_assets", "Total assets"),
        ("depreciation and amortisation expenses", "depreciation", "Depreciation and amortisation"),
        ("depreciation / amortisation and depletion expense", "depreciation", "Depreciation, amortisation and depletion"),
        ("equity attributable to owners of the parent", "book_equity", "Equity attributable to parent"),
    )
    for prefix, metric_code, reported_label in contextual_patterns:
        if normalized == prefix:
            if "cash flow" in section_lower and metric_code in {"finance_costs", "depreciation", "pre_tax_income"}:
                return f"cash_flow_{metric_code}", f"Cash flow statement: {reported_label}", source_line
            return metric_code, reported_label, source_line

    if profit_statement:
        if normalized == "profit for the year attributable to equity holders of the parent":
            return "net_income_parent", "Net income attributable to parent", "Equity holders of the parent"
        if normalized in {"equity holders of the parent", "owners of the parent", "owners of the company"}:
            return "net_income_parent", "Net income attributable to parent", source_line
    elif normalized.startswith("profit for the year attributable"):
        return None

    if normalized in {"non-controlling interests", "noncontrolling interests", "non-controlling interest", "minority interest", "minority interests", "nci", "less: minority interest", "less : minority interest"}:
        if profit_statement:
            return "net_income_nci", "Net income attributable to NCI", source_line
        return "minority_interests", "Minority interests", source_line

    for metric_code, reported_label, aliases in _METRIC_ALIASES:
        for alias in sorted(aliases, key=len, reverse=True):
            if normalized == alias:
                return metric_code, reported_label, alias
    return None


def _row_bbox(page: Any | None, source_line: str, *, occurrence: int = 0) -> dict[str, float] | None:
    if page is None:
        return None
    search_values = [source_line]
    if " diluted EPS" in source_line:
        search_values.append(source_line.split(" diluted EPS", maxsplit=1)[0])
    matches = []
    for value in search_values:
        try:
            matches = page.search(re.escape(value).replace(r"\ ", r"\s+"), regex=True, case=True)
        except Exception:
            continue
        if matches:
            break
    if len(matches) <= occurrence:
        return None
    match = matches[occurrence]
    required = ("x0", "top", "x1", "bottom")
    if any(key not in match for key in required):
        return None
    return {key: float(match[key]) for key in required}


def _consolidate_candidates(candidates: list[PdfTableCandidate]) -> list[PdfTableCandidate]:
    # Deduplicate only the same physical row read by the text and table paths.
    # Equal values on different rows are separate evidence. Never add apparent
    # debt/lease components without knowing whether they overlap or include totals.
    output: list[PdfTableCandidate] = []
    for candidate in candidates:
        duplicate = next((i for i, other in enumerate(output) if _same_pdf_row(other, candidate)), None)
        if duplicate is None:
            output.append(candidate)
        elif candidate.source_locator_json.get("type") == "pdf_table_cell":
            output[duplicate] = candidate
    return sorted(
        output,
        key=lambda item: (item.source_page, item.fiscal_year, item.metric_code, item.value),
    )


def _same_pdf_row(left: PdfTableCandidate, right: PdfTableCandidate) -> bool:
    if (left.metric_code, left.fiscal_year, left.source_page, left.value, left.unit) != (
        right.metric_code, right.fiscal_year, right.source_page, right.value, right.unit
    ):
        return False
    if left.source_cell_reference == right.source_cell_reference:
        return True
    a, b = left.source_locator_json, right.source_locator_json
    if a.get("type") == b.get("type") or a.get("region") != b.get("region"):
        return False
    aa, bb = a.get("bounding_box") or a.get("cell_bbox"), b.get("bounding_box") or b.get("cell_bbox")
    return bool(aa and bb and max(aa["top"], bb["top"]) < min(aa["bottom"], bb["bottom"])
                and max(aa["x0"], bb["x0"]) < min(aa["x1"], bb["x1"]))


def _table_candidates(
    *,
    matrix: list[list[str | None]],
    rows: list[Any],
    table_bbox: tuple[float, float, float, float],
    page_number: int,
    page_width: float,
    page_height: float,
    table_number: int,
    section: str | None,
    currency: str | None,
    scale: str | None,
    period_type: str = "annual",
    page_text: str = "",
    region_number: int | None = None,
    unit_evidence: dict | None = None,
) -> list[PdfTableCandidate]:
    header_index = _header_row_index(matrix)
    if header_index is None:
        return []
    headers = matrix[header_index]
    table_name = section or f"PDF table {table_number}"
    candidates: list[PdfTableCandidate] = []

    for row_index in range(header_index + 1, len(matrix)):
        row = matrix[row_index]
        if not row:
            continue
        source_label = (row[0] or "").strip()
        metric = _metric_for_statement_line(source_label, section)
        if metric is None:
            continue
        metric_code, reported_label, _ = metric
        # Text rows retain context for attribution and current/noncurrent headings.
        # Table cells alone cannot safely infer that context from merged headings.
        if metric_code in {"borrowings", "lease_liabilities", "net_income_parent", "net_income_nci", "minority_interests", "cash_flow_cash_opening", "cash_flow_cash_closing"} or (metric_code == "net_income" and source_label.lower() == "profit after tax"):
            continue

        for column_index in range(1, min(len(row), len(headers))):
            column_label = (headers[column_index] or "").strip()
            fiscal_year = _fiscal_year(column_label)
            value_text = (row[column_index] or "").strip()
            value = _number(value_text)
            if fiscal_year is None or value is None:
                continue

            unit = _candidate_unit(metric_code, currency, scale, source_label=source_label, page_text=page_text)
            item_warnings = _candidate_warnings(metric_code, unit)
            if unit_evidence and not metric_code.endswith("shares"):
                item_warnings.append("currency_from_embedded_font_requires_review")
            cell_bbox = _cell_bbox(rows, row_index, column_index)
            if cell_bbox is None:
                item_warnings.append("cell_bounding_box_missing")
            cell_reference = (
                f"P{page_number}:T{table_number}:R{row_index + 1}:C{column_index + 1}"
            )
            candidates.append(
                PdfTableCandidate(
                    metric_code=metric_code,
                    reported_label=reported_label,
                    value=value,
                    unit=unit,
                    fiscal_year=fiscal_year,
                    period_type=period_type,
                    source_text=f"{source_label} | {column_label} | {value_text}",
                    source_page=page_number,
                    source_section=section,
                    source_table_name=table_name,
                    source_row_label=source_label,
                    source_column_label=column_label,
                    source_cell_reference=cell_reference,
                    source_locator_json={
                        "type": "pdf_table_cell",
                        "page": page_number,
                        "table": table_number,
                        "row": row_index + 1,
                        "column": column_index + 1,
                        "cell": cell_reference,
                        "coordinate_system": "pdfplumber_top_left_points",
                        "page_width": page_width,
                        "page_height": page_height,
                        "table_bbox": _bbox_dict(table_bbox),
                        "cell_bbox": _bbox_dict(cell_bbox) if cell_bbox else None,
                        **({"region": region_number} if region_number else {}),
                        **({"unit_evidence": unit_evidence} if unit_evidence and not metric_code.endswith("shares") else {}),
                    },
                    extraction_warnings=";".join(item_warnings) or None,
                    confidence_label="high" if not item_warnings else "medium",
                )
            )
    return candidates


def _header_row_index(matrix: list[list[str | None]]) -> int | None:
    for row_index, row in enumerate(matrix[:5]):
        if sum(_fiscal_year(cell or "") is not None for cell in row[1:]) >= 1:
            return row_index
    return None


def _fiscal_year(value: str) -> int | None:
    matches = list(_YEAR_PATTERN.finditer(value))
    return _end_year(matches[0]) if len(matches) == 1 else None


def _number(value: str) -> float | None:
    cleaned = value.strip().replace(",", "")
    if not cleaned or cleaned in {"-", "–", "—", "--", "n/a", "N/A"}:
        return None
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()").strip()
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", cleaned):
        return None
    parsed = float(cleaned)
    if not math.isfinite(parsed):
        return None
    return -parsed if negative else parsed


def _candidate_unit(metric_code: str, currency: str | None, scale: str | None, *, source_label: str = "", page_text: str = "", share_context: bool = False, share_scale: str | None = None) -> str | None:
    if metric_code in {"basic_shares", "diluted_shares"}:
        explicit = _SCALE_PATTERN.search(source_label)
        if not explicit:
            explicit = re.search(r"\bshares?\s+(?:are\s+)?(?:in\s+)?(thousands?|millions?|billions?)\b", page_text, re.I)
        if explicit:
            share_unit = explicit.group(1).lower().rstrip('s')
            return "shares thousand" if share_unit == "000" else f"shares {share_unit}"
        if share_scale:
            return f"shares {share_scale}"
        if share_context or re.search(r"\bnumber of\b|\bactuals?\b", source_label, re.I):
            return "shares"
        return None
    if metric_code in {"basic_eps", "diluted_eps"}:
        explicit_currency = _CURRENCY_PATTERN.search(source_label)
        if explicit_currency:
            return explicit_currency.group(1).upper() + "/share"
        if re.search(r"[₹`]|\bRs\.?", source_label, re.I):
            return "INR/share"
        return currency + "/share" if currency else None
    if currency is None:
        return None
    return f"{currency} {scale}".strip() if scale else currency


def _candidate_warnings(metric_code: str, unit: str | None) -> list[str]:
    result = [] if unit else ["reporting_unit_missing"]
    if metric_code in {"borrowings", "current_borrowings", "noncurrent_borrowings", "bills_discounted", "cash_and_balances_with_rbi", "profit_after_tax_before_associates", "profit_before_associates_nci", "investments", "group_profit"} or metric_code.startswith("cash_flow_"):
        result.append("accounting_scope_requires_review")
    return result


def _cell_bbox(rows: list[Any], row_index: int, column_index: int) -> tuple[float, float, float, float] | None:
    if row_index >= len(rows) or column_index >= len(rows[row_index].cells):
        return None
    cell = rows[row_index].cells[column_index]
    return tuple(float(value) for value in cell) if cell is not None else None


def _bbox_dict(bbox: tuple[float, float, float, float]) -> dict[str, float]:
    return {
        "x0": float(bbox[0]),
        "top": float(bbox[1]),
        "x1": float(bbox[2]),
        "bottom": float(bbox[3]),
    }
