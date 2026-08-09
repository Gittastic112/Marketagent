import difflib
import html
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FilingSection, FilingSectionDiff, RawDocument


def _generate_html_diff(old_text: str, new_text: str) -> str:
    """Generates an HTML representation of the diff between two texts."""
    # We use a simple word-based SequenceMatcher for counting,
    # but for HTML display, HtmlDiff is built-in.
    # To avoid huge HTML tables, we'll implement a custom lightweight word-diff using SequenceMatcher.
    old_words = re.findall(r'\S+|\s+', old_text)
    new_words = re.findall(r'\S+|\s+', new_text)

    matcher = difflib.SequenceMatcher(None, old_words, new_words)
    result = []

    added_count = 0
    removed_count = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            result.append(html.escape("".join(old_words[i1:i2])))
        elif tag == 'insert':
            inserted = "".join(new_words[j1:j2])
            result.append(f'<ins class="diff-add">{html.escape(inserted)}</ins>')
            added_count += len([w for w in new_words[j1:j2] if w.strip()])
        elif tag == 'delete':
            deleted = "".join(old_words[i1:i2])
            result.append(f'<del class="diff-remove">{html.escape(deleted)}</del>')
            removed_count += len([w for w in old_words[i1:i2] if w.strip()])
        elif tag == 'replace':
            deleted = "".join(old_words[i1:i2])
            inserted = "".join(new_words[j1:j2])
            result.append(
                f'<del class="diff-remove">{html.escape(deleted)}</del>'
                f'<ins class="diff-add">{html.escape(inserted)}</ins>'
            )
            added_count += len([w for w in new_words[j1:j2] if w.strip()])
            removed_count += len([w for w in old_words[i1:i2] if w.strip()])

    html_diff = "".join(result)
    return html_diff, added_count, removed_count


def generate_section_diffs(db: Session, current_document: RawDocument, prior_document: RawDocument | None) -> list[FilingSectionDiff]:
    """
    Compares the FilingSections of a current document to a prior document.
    Returns a list of FilingSectionDiff objects.
    """
    current_sections = list(db.scalars(select(FilingSection).where(FilingSection.raw_document_id == current_document.id)))

    diffs = []

    if not prior_document:
        # If no prior document, all sections are essentially "new" with no prior section.
        for section in current_sections:
            diff = FilingSectionDiff(
                current_section_id=section.id,
                prior_section_id=None,
                added_words=section.word_count,
                removed_words=0,
                diff_html=f'<ins class="diff-add">{html.escape(section.text_content)}</ins>'
            )
            db.add(diff)
            diffs.append(diff)
        return diffs

    prior_sections = list(db.scalars(select(FilingSection).where(FilingSection.raw_document_id == prior_document.id)))
    prior_section_map = {s.item_name: s for s in prior_sections}

    for current_section in current_sections:
        prior_section = prior_section_map.get(current_section.item_name)

        if not prior_section:
            diff = FilingSectionDiff(
                current_section_id=current_section.id,
                prior_section_id=None,
                added_words=current_section.word_count,
                removed_words=0,
                diff_html=f'<ins class="diff-add">{html.escape(current_section.text_content)}</ins>'
            )
        else:
            diff_html, added_words, removed_words = _generate_html_diff(prior_section.text_content, current_section.text_content)
            diff = FilingSectionDiff(
                current_section_id=current_section.id,
                prior_section_id=prior_section.id,
                added_words=added_words,
                removed_words=removed_words,
                diff_html=diff_html
            )

        db.add(diff)
        diffs.append(diff)

    return diffs
