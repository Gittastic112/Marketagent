import hashlib
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime
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
PDF_EXTRACTION_METHOD = "pdf_targeted_v3"
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
    r"(?<![\w,./%])(?:\(?[-+]?(?:\d+(?:,\d{2,3})+|\d+)(?:\.\d+)?\)?\*?|[-–—])(?![\w,./%])"
)
_SCALE_PATTERN = re.compile(r"\b(thousands?|millions?|billions?|crores?|lakhs?|000s)\b", re.IGNORECASE)
_CURRENCY_PATTERN = re.compile(r"\b(USD|INR|EUR|GBP|JPY|CAD|AUD|CHF|CNY|HKD|SGD)\b", re.IGNORECASE)
_STATEMENT_HEADING = re.compile(
    r"^(?:consolidated\s+)?(?:balance sheet|statement of profit and loss|profit and loss account|"
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
                page_currency, page_scale = _reporting_unit(page_text)
                reporting_currency = reporting_currency or page_currency
                reporting_scale = reporting_scale or page_scale
                regions = _statement_regions(page)
                if len(regions) > 1:
                    warnings.add("facing_page_regions")
                inherited_section = None
                page_table_number = 0
                for region_number, region in enumerate(regions, start=1):
                    region_text = region.extract_text() or ""
                    region_currency, region_scale = _reporting_unit(region_text)
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
        published_at=published_at or datetime.now(UTC),
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


def _page_section(text: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if _STATEMENT_HEADING.match(line):
            return line[:255]
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
) -> list[PdfTableCandidate]:
    years = _statement_years(page_text)
    if not years:
        return []
    lines = _stitch_statement_lines(page_text.splitlines())
    candidates: list[PdfTableCandidate] = []
    attribution = "profit"
    liability_scope = None
    row_occurrences: dict[str, int] = {}
    for line_number, source_line in enumerate(lines, start=1):
        normalized_line = source_line.lower()
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
        parsed_row = _statement_row_values(source_line, len(years), page_text)
        if parsed_row is None:
            possible_label = re.split(r"\s+(?=[\d(])", source_line, maxsplit=1)[0]
            if warnings is not None and _metric_for_statement_line(possible_label, section):
                warnings.add("ambiguous_statement_row_skipped")
            continue
        source_label, value_tokens = parsed_row
        metric = _metric_for_statement_line(source_label, section, liability_scope=liability_scope)
        if metric is None:
            continue
        metric_code, reported_label, source_row_label = metric
        if metric_code == "net_income" and source_label.lower() == "profit after tax" and re.search(r"share of profit.*associate", page_text, re.I):
            metric_code, reported_label = "profit_after_tax_before_associates", "Profit after tax before associates"
        if attribution != "profit" and metric_code in {"net_income_parent", "net_income_nci"}:
            continue
        occurrence = row_occurrences.get(source_line, 0)
        row_occurrences[source_line] = occurrence + 1
        row_bbox = _row_bbox(page, source_line, occurrence=occurrence)

        for value_index, (fiscal_year, value_token) in enumerate(zip(years, value_tokens, strict=True), start=1):
            value = _number(value_token.rstrip("*"))
            if value is None:
                continue
            unit = _candidate_unit(metric_code, currency, scale, source_label=source_label, page_text=page_text)
            item_warnings = _candidate_warnings(metric_code, unit)
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
                    source_text=source_line.strip(),
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
    matches = list(_STATEMENT_VALUE_TOKEN_PATTERN.finditer(cleaned))
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


def _stitch_statement_lines(lines: list[str]) -> list[str]:
    stitched: list[str] = []
    index = 0
    while index < len(lines):
        line = re.sub(r"\s+", " ", lines[index]).strip()
        next_line = re.sub(r"\s+", " ", lines[index + 1]).strip() if index + 1 < len(lines) else ""
        if (
            line.lower().startswith("weighted average number of equity shares")
            and "diluted" not in line.lower()
            and next_line.lower().startswith("diluted")
        ):
            values = list(_STATEMENT_VALUE_TOKEN_PATTERN.finditer(line))
            start = values[0].start() if values else len(line)
            stitched.append(f"{line[:start].rstrip()} {next_line} {line[start:]}")
            index += 2
            continue
        stitched.append(line)
        index += 1
    return stitched


def _metric_for_statement_line(
    source_line: str,
    section: str | None,
    *,
    liability_scope: str | None = None,
) -> tuple[str, str, str] | None:
    normalized = re.sub(r"\s+", " ", source_line.strip().lower())
    normalized = normalized.replace("–", "-").replace("‑", "-")
    normalized = re.sub(r"^(?:[-•]\s+|[a-z]\)\s+)", "", normalized)
    normalized = re.sub(r"\s*\(['‘]?nci['’]?\)\s*$", "", normalized)
    normalized = re.sub(r"\s*\((?:in )?(?:thousands?|millions?|billions?|actuals?|numbers?)\)\s*$", "", normalized)
    section_lower = (section or "").lower()
    profit_statement = "profit and loss" in section_lower

    if normalized.startswith("weighted average number of equity shares"):
        if "diluted" in normalized:
            return "diluted_shares", "Diluted shares", source_line
        if "basic" in normalized:
            return "basic_shares", "Basic shares", source_line
        return None
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
            matches = page.search(re.escape(value), regex=True, case=True)
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


def _candidate_unit(metric_code: str, currency: str | None, scale: str | None, *, source_label: str = "", page_text: str = "") -> str | None:
    if metric_code in {"basic_shares", "diluted_shares"}:
        explicit = _SCALE_PATTERN.search(source_label)
        if not explicit:
            explicit = re.search(r"\bshares?\s+(?:are\s+)?(?:in\s+)?(thousands?|millions?|billions?)\b", page_text, re.I)
        if explicit:
            return f"shares {explicit.group(1).lower().rstrip('s')}"
        if re.search(r"\bnumber of\b|\bactuals?\b", source_label, re.I):
            return "shares"
        return None
    if currency is None:
        return None
    return f"{currency} {scale}".strip() if scale else currency


def _candidate_warnings(metric_code: str, unit: str | None) -> list[str]:
    result = [] if unit else ["reporting_unit_missing"]
    if metric_code in {"borrowings", "current_borrowings", "noncurrent_borrowings", "bills_discounted", "cash_and_balances_with_rbi", "profit_after_tax_before_associates", "group_profit"} or metric_code.startswith("cash_flow_"):
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
