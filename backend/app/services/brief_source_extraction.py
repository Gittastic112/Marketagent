"""Bounded text-only PDF intake. No OCR, URL fetching or financial-fact creation."""
from hashlib import sha256
from io import BytesIO

from fastapi import HTTPException
import pdfplumber
from pdfminer.pdftypes import resolve1

from app.services.pdf_financial_extraction import parse_pdf_page_ranges, validate_pdf_upload
from app.services.pdf_jobs import PdfJobError, run_pdf_job

MAX_BRIEF_PDF_BYTES = 12 * 1024 * 1024
MAX_BRIEF_TEXT = 60_000
MAX_BRIEF_PAGES = 20


def extract_brief_pdf(filename: str, content_type: str | None, content: bytes, page_ranges: str | None) -> tuple[str, dict]:
    if len(content) > MAX_BRIEF_PDF_BYTES:
        raise HTTPException(413, "PDF must be at most 12 MB.")
    validate_pdf_upload(filename=filename, content_type=content_type, content=content)
    # Invalid/huge ranges are rejected before allocating a parser process.
    parse_pdf_page_ranges(page_ranges, max_targeted_pages=MAX_BRIEF_PAGES)
    try:
        result = run_pdf_job("brief", content, {"page_ranges": page_ranges})
    except PdfJobError as error:
        raise HTTPException(error.status_code, str(error)) from None
    if (not isinstance(result, list) or len(result) != 2 or not isinstance(result[0], str)
        or not isinstance(result[1], dict) or not 40 <= len(result[0]) <= MAX_BRIEF_TEXT):
        raise HTTPException(422, "PDF parser returned an invalid result.")
    return result[0], result[1]


def _extract_brief_pdf(filename: str, content_type: str | None, content: bytes, page_ranges: str | None) -> tuple[str, dict]:
    if len(content) > MAX_BRIEF_PDF_BYTES:
        raise HTTPException(413, "PDF must be at most 12 MB.")
    validate_pdf_upload(filename=filename, content_type=content_type, content=content)
    try:
        reader = pdfplumber.open(BytesIO(content))
        count = len(reader.pages)
        if count < 1 or count > 1000:
            raise HTTPException(422, "PDF must contain 1 to 1,000 pages.")
        selected = parse_pdf_page_ranges(page_ranges, max_targeted_pages=MAX_BRIEF_PAGES) if page_ranges else tuple(range(1, count + 1))
        if not selected or len(selected) > MAX_BRIEF_PAGES or max(selected) > count:
            raise HTTPException(422, "Select at most 20 existing pages, for example 1-4,8.")
        parts, spans, blank = [], [], []
        length = 0
        for number in selected:
            page = reader.pages[number - 1]
            # Bound decompressed page streams before text extraction.
            if sum(len(resolve1(stream).get_data()) for stream in page.page_obj.contents) > 4 * 1024 * 1024:
                raise HTTPException(422, "A PDF page is too complex. Upload a simpler text-based PDF.")
            text = (page.extract_text() or "").replace("\x00", "").strip()
            if not text:
                blank.append(number)
                continue
            if length + len(text) + 2 > MAX_BRIEF_TEXT:
                raise HTTPException(422, "Selected pages exceed 60,000 characters. Select fewer pages.")
            if parts:
                parts.append("\n\n")
                length += 2
            spans.append({"page": number, "start_char": length, "end_char": length + len(text)})
            parts.append(text)
            length += len(text)
        body = "".join(parts)
        if len(body) < 40:
            raise HTTPException(422, "No usable text layer. OCR is not available; paste the text or upload a text-based PDF.")
        return body, {
            "method": "pdfplumber_text_v1", "page_count": count, "selected_pages": list(selected),
            "page_spans": spans, "blank_pages": blank, "character_count": len(body),
            "text_sha256": sha256(body.encode()).hexdigest(),
            "warnings": (["Only selected pages were extracted."] if len(selected) < count else [])
            + (["Some selected pages have no text. Images and charts were not analyzed."] if blank else [])
            + ["Text extraction only. Images, charts and table layout are not visually interpreted."],
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(422, "PDF could not be read. Upload a valid, text-based PDF.") from None
    finally:
        if "reader" in locals():
            reader.close()
