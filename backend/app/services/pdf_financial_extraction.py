import hashlib
import re
from dataclasses import dataclass, replace
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
PDF_EXTRACTION_METHOD = "pdf_targeted_v2"
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
_YEAR_PATTERN = re.compile(r"\b(?:FY\s*)?(19\d{2}|20\d{2})\b", re.IGNORECASE)
_INDIA_SCALE_PATTERN = re.compile(
    r"(?:₹|`|\brs\.?\b|\binr\b)?\s*(?:amounts?\s+)?(?:are\s+)?in\s+"
    r"(?P<scale>crore|crores|lakh|lakhs)\b",
    re.IGNORECASE,
)
_STATEMENT_VALUE_TOKEN_PATTERN = re.compile(
    r"\(?[-+]?(?:\d{1,3}(?:,\d{2,3})+|\d+)(?:\.\d+)?\)?\*?|(?<!\S)-(?!\S)"
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
                section = _page_section(page_text)
                tables = page.find_tables()
                table_count += len(tables)

                extracted.extend(
                    _statement_line_candidates(
                        page_text=page_text,
                        page_number=page_number,
                        section=section,
                        currency=page_currency,
                        scale=page_scale,
                        page_width=float(page.width),
                        page_height=float(page.height),
                        page=page,
                        period_type=period_type,
                    )
                )

                for table_number, table in enumerate(tables, start=1):
                    matrix = table.extract()
                    if not matrix:
                        continue
                    extracted.extend(
                        _table_candidates(
                            matrix=matrix,
                            rows=table.rows,
                            table_bbox=table.bbox,
                            page_number=page_number,
                            page_width=float(page.width),
                            page_height=float(page.height),
                            table_number=table_number,
                            section=section,
                            currency=page_currency,
                            scale=page_scale,
                            period_type=period_type,
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
    match = _UNIT_PATTERN.search(text)
    if match is not None:
        currency = match.group("currency").upper()
        scale = match.group("scale")
        return currency, scale.lower() if scale else None
    india_scale = _INDIA_SCALE_PATTERN.search(text)
    if india_scale is not None:
        return "INR", india_scale.group("scale").lower().rstrip("s")
    return None, None


def _page_section(text: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    preferred_headings = (
        "consolidated balance sheet",
        "consolidated statement of profit and loss",
        "consolidated cash flow statement",
        "notes to the consolidated financial statements",
    )
    for line in lines:
        for heading in preferred_headings:
            if line.lower().startswith(heading):
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
) -> list[PdfTableCandidate]:
    years = _statement_years(page_text)
    if not years:
        return []
    lines = _stitch_statement_lines(page_text.splitlines())
    candidates: list[PdfTableCandidate] = []
    in_other_comprehensive_income = False
    for line_number, source_line in enumerate(lines, start=1):
        if "other comprehensive income" in source_line.lower():
            in_other_comprehensive_income = True
        metric = _metric_for_statement_line(source_line, section)
        if metric is None:
            continue
        metric_code, reported_label, source_row_label = metric
        if in_other_comprehensive_income and metric_code in {"net_income_parent", "net_income_nci"}:
            continue
        value_source_line = re.sub(r"\(refer\s+note\s+\d+\)", "", source_line, flags=re.IGNORECASE)
        value_tokens = _STATEMENT_VALUE_TOKEN_PATTERN.findall(value_source_line)
        if len(value_tokens) < len(years):
            continue
        value_tokens = value_tokens[-len(years):]
        row_bbox = _row_bbox(page, source_line)

        for value_index, (fiscal_year, value_token) in enumerate(zip(years, value_tokens, strict=True), start=1):
            value = _number(value_token.rstrip("*"))
            if value is None:
                continue
            unit = _candidate_unit(metric_code, currency, scale)
            item_warnings = [] if unit else ["reporting_unit_missing"]
            if row_bbox is None:
                item_warnings.append("row_bounding_box_missing")
            cell_reference = f"P{page_number}:L{line_number}:Y{fiscal_year}"
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
                    },
                    extraction_warnings=";".join(item_warnings) or None,
                    confidence_label="high" if not item_warnings else "medium",
                )
            )
    return candidates


def _statement_years(page_text: str) -> tuple[int, ...]:
    header_lines = page_text.splitlines()[:80]
    for line in header_lines:
        line_lower = line.lower()
        if not any(marker in line_lower for marker in ("particulars", "march 31", "year ended", "as at")):
            continue
        line_years: list[int] = []
        for match in _YEAR_PATTERN.finditer(line):
            year = int(match.group(1))
            if year not in line_years:
                line_years.append(year)
        if len(line_years) >= 2:
            return tuple(line_years)

    for line in header_lines:
        line_years: list[int] = []
        for match in _YEAR_PATTERN.finditer(line):
            year = int(match.group(1))
            if year not in line_years:
                line_years.append(year)
        if len(line_years) >= 2:
            return tuple(line_years)

    years: list[int] = []
    for line in header_lines:
        if "year ended" not in line.lower() and "as at" not in line.lower():
            continue
        for match in _YEAR_PATTERN.finditer(line):
            year = int(match.group(1))
            if year not in years:
                years.append(year)
    return tuple(years)


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
            stitched.append(f"{line} {next_line}")
            index += 2
            continue
        stitched.append(line)
        index += 1
    return stitched


def _metric_for_statement_line(
    source_line: str,
    section: str | None,
) -> tuple[str, str, str] | None:
    normalized = re.sub(r"\s+", " ", source_line.strip().lower())
    normalized = normalized.replace("–", "-")
    section_lower = (section or "").lower()

    contextual_patterns: tuple[tuple[str, str, str], ...] = (
        ("weighted average number of equity shares", "diluted_shares", "Diluted shares"),
        ("customers' bills discounted", "debt", "Customers' bills discounted"),
        ("customers’ bills discounted", "debt", "Customers' bills discounted"),
        ("investments accounted using equity method", "investments_in_associates", "Investments accounted using equity method"),
        ("interest and bank charges", "finance_costs", "Interest and bank charges"),
        ("total tax expense", "tax_expense", "Total tax expense"),
        ("profit before tax", "pre_tax_income", "Profit before tax"),
        ("total equity attributable to equity holders of the parent", "book_equity", "Equity attributable to parent"),
        ("total assets", "total_assets", "Total assets"),
    )
    for prefix, metric_code, reported_label in contextual_patterns:
        if normalized.startswith(prefix):
            return metric_code, reported_label, source_line.split("  ", maxsplit=1)[0].strip()

    if "profit and loss" in section_lower:
        if normalized.startswith("profit for the year attributable to equity holders of the parent"):
            return "net_income_parent", "Net income attributable to parent", "Equity holders of the parent"
        if normalized.startswith("equity holders of the parent"):
            return "net_income_parent", "Net income attributable to parent", "Equity holders of the parent"
    elif normalized.startswith("profit for the year attributable"):
        return None

    if normalized.startswith("non-controlling interests") or normalized.startswith("noncontrolling interests"):
        if "profit and loss" in section_lower:
            return "net_income_nci", "Net income attributable to NCI", "Non-controlling interests"
        return "minority_interests", "Minority interests", "Non-controlling interests"

    for metric_code, reported_label, aliases in _METRIC_ALIASES:
        for alias in sorted(aliases, key=len, reverse=True):
            if normalized == alias or normalized.startswith(f"{alias} "):
                return metric_code, reported_label, alias
    return None


def _row_bbox(page: Any | None, source_line: str) -> dict[str, float] | None:
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
    if not matches:
        return None
    match = matches[0]
    required = ("x0", "top", "x1", "bottom")
    if any(key not in match for key in required):
        return None
    return {key: float(match[key]) for key in required}


def _consolidate_candidates(candidates: list[PdfTableCandidate]) -> list[PdfTableCandidate]:
    deduplicated: dict[tuple[str, int, int, float], PdfTableCandidate] = {}
    for candidate in candidates:
        key = (candidate.metric_code, candidate.fiscal_year, candidate.source_page, candidate.value)
        existing = deduplicated.get(key)
        if existing is None or (
            existing.source_locator_json.get("type") != "pdf_table_cell"
            and candidate.source_locator_json.get("type") == "pdf_table_cell"
        ):
            deduplicated[key] = candidate

    output = list(deduplicated.values())
    for metric_code in ("debt", "lease_liabilities"):
        grouped: dict[tuple[int, int], list[PdfTableCandidate]] = {}
        for candidate in output:
            if candidate.metric_code == metric_code:
                grouped.setdefault((candidate.fiscal_year, candidate.source_page), []).append(candidate)
        for (fiscal_year, page_number), components in grouped.items():
            if len(components) < 2:
                continue
            output = [candidate for candidate in output if candidate not in components]
            total = round(sum(component.value for component in components), 6)
            first = components[0]
            component_locators = [component.source_locator_json for component in components]
            output.append(
                replace(
                    first,
                    reported_label=(
                        "Total debt (summed reported components)"
                        if metric_code == "debt"
                        else "Lease liabilities (summed reported components)"
                    ),
                    value=total,
                    source_text=" + ".join(component.source_text for component in components),
                    source_row_label=" + ".join(component.source_row_label for component in components),
                    source_cell_reference=f"P{page_number}:SUM:{metric_code}:{fiscal_year}"[:40],
                    source_locator_json={
                        "type": "pdf_reported_component_sum",
                        "page": page_number,
                        "operation": "sum",
                        "metric_code": metric_code,
                        "fiscal_year": fiscal_year,
                        "components": component_locators,
                    },
                    extraction_warnings="derived_sum_of_reported_components;review_required",
                    confidence_label="medium",
                )
            )
    return sorted(
        output,
        key=lambda item: (item.source_page, item.fiscal_year, item.metric_code, item.value),
    )


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
        metric = _metric_for_label(source_label)
        if metric is None:
            continue
        metric_code, reported_label = metric

        for column_index in range(1, min(len(row), len(headers))):
            column_label = (headers[column_index] or "").strip()
            fiscal_year = _fiscal_year(column_label)
            value_text = (row[column_index] or "").strip()
            value = _number(value_text)
            if fiscal_year is None or value is None:
                continue

            unit = _candidate_unit(metric_code, currency, scale)
            item_warnings = [] if unit else ["reporting_unit_missing"]
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
    match = _YEAR_PATTERN.search(value)
    return int(match.group(1)) if match else None


def _metric_for_label(value: str) -> tuple[str, str] | None:
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    normalized = re.sub(r"\s*[\[(]\s*note\s+\d+[a-z]?\s*[\])]\s*$", "", normalized)
    normalized = re.sub(r"\s+(?:note\s*)?\d+[a-z]?$", "", normalized)
    for metric_code, reported_label, aliases in _METRIC_ALIASES:
        if normalized in aliases:
            return metric_code, reported_label
    return None


def _number(value: str) -> float | None:
    cleaned = value.strip().replace(",", "")
    if not cleaned or cleaned in {"-", "--", "n/a", "N/A"}:
        return None
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()").strip()
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", cleaned):
        return None
    parsed = float(cleaned)
    return -parsed if negative else parsed


def _candidate_unit(metric_code: str, currency: str | None, scale: str | None) -> str | None:
    if metric_code in {"basic_shares", "diluted_shares"}:
        return "shares"
    if currency is None:
        return None
    return f"{currency} {scale}".strip() if scale else currency


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
