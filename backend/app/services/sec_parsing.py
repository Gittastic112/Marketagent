import html
import re

from sqlalchemy.orm import Session

from app.models import FilingSection, RawDocument


def strip_html(text: str) -> str:
    """A basic HTML stripper that removes tags and unescapes HTML entities."""
    # Remove <style> and <script> blocks completely
    text = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', text, flags=re.IGNORECASE | re.DOTALL)
    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', ' ', text, flags=re.DOTALL)
    # Remove all other tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Unescape HTML entities
    text = html.unescape(text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_sec_filing(db: Session, document: RawDocument) -> list[FilingSection]:
    """
    Parses a RawDocument representing an SEC filing into FilingSections.
    This is a heuristic-based parser that looks for standardized SEC items (e.g., "Item 1.").
    """
    if not document.raw_text:
        return []

    # First, clean the text for easier searching
    cleaned_text = strip_html(document.raw_text)

    # Common pattern for SEC items: "Item 1.", "Item 1A.", "ITEM 7.", etc.
    # SEC filings are messy, so we look for "Item" followed by a number, an optional letter, and optional punctuation.
    item_pattern = re.compile(r'(?:\b(?:Item|ITEM)\s+([1-9][0-9]?[A-Z]?)\b\.?)')

    sections = []

    # We will search for all matches of the pattern
    matches = list(item_pattern.finditer(cleaned_text))

    if not matches:
        # If we couldn't find any items, just return the whole thing as one section
        section = FilingSection(
            raw_document_id=document.id,
            item_name="Full Document",
            title="Full Document",
            text_content=cleaned_text,
            word_count=len(cleaned_text.split())
        )
        db.add(section)
        sections.append(section)
        return sections

    # Otherwise, split by the matches
    for i in range(len(matches)):
        match = matches[i]
        item_num = match.group(1).upper()
        item_name = f"Item {item_num}"

        start_pos = match.start()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(cleaned_text)

        section_text = cleaned_text[start_pos:end_pos].strip()

        # Avoid creating tiny meaningless sections or duplicates if the parser is confused
        # (e.g. table of contents items vs actual items)
        if len(section_text) < 50:
            continue

        # Optional: Extract title. The title is usually the text right after the item, up to a period or newline.
        # But since we stripped newlines, we'll just take the first few words as a hint.
        preview = section_text[:200]

        section = FilingSection(
            raw_document_id=document.id,
            item_name=item_name,
            title=preview[:50] + "...",
            text_content=section_text,
            word_count=len(section_text.split())
        )
        db.add(section)
        sections.append(section)

    # If the parser resulted in no viable sections (e.g. all were too small), fallback
    if not sections:
        section = FilingSection(
            raw_document_id=document.id,
            item_name="Full Document",
            title="Full Document",
            text_content=cleaned_text,
            word_count=len(cleaned_text.split())
        )
        db.add(section)
        sections.append(section)

    return sections
