from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.ai import AiOutput
from app.models.raw_document import RawDocument
from app.services.ai_citations import extract_source_ids


MAX_SOURCE_CHARACTERS = 2_000_000
MAX_PASSAGE_CHARACTERS = 1_200
MIN_PASSAGE_CHARACTERS = 20
MAX_CLAIM_CHARACTERS = 600
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+(?:[.,][0-9]+)?%?")
SOURCE_MARKER_PATTERN = re.compile(r"\[source_id:([^\]]+)\]")
STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "was",
        "were",
        "with",
    }
)


@dataclass(frozen=True)
class SourceSegment:
    quote: str
    start_char: int
    end_char: int


@dataclass(frozen=True)
class RelevanceScore:
    score: float
    matched_terms: tuple[str, ...]
    claim_term_count: int
    matched_term_count: int


def _tokens(value: str) -> list[str]:
    tokens: list[str] = []
    for raw in TOKEN_PATTERN.findall(value or ""):
        normalized = raw.casefold().replace(",", "")
        if len(normalized) < 2 or normalized in STOP_WORDS:
            continue
        tokens.append(normalized)
    return tokens


def _claim_before_marker(output_text: str, marker_start: int) -> str | None:
    prefix = output_text[:marker_start].rstrip()
    if not prefix:
        return None
    window = prefix[max(0, len(prefix) - MAX_CLAIM_CHARACTERS):]
    boundaries = list(re.finditer(r"(?:\n+|(?<=[.!?])\s+)", window))
    if boundaries:
        window = window[boundaries[-1].end():]
    claim = SOURCE_MARKER_PATTERN.sub("", window).strip(" \t\r\n-*•.;:–—")
    return claim or None


def claim_for_source_marker(output_text: str, source_id: str) -> str | None:
    for match in SOURCE_MARKER_PATTERN.finditer(output_text or ""):
        if match.group(1).strip() != source_id:
            continue
        claim = _claim_before_marker(output_text, match.start())
        if claim:
            return claim
    return None


def _trimmed_segment(text: str, start: int, end: int) -> SourceSegment | None:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    if end - start < MIN_PASSAGE_CHARACTERS:
        return None
    return SourceSegment(quote=text[start:end], start_char=start, end_char=end)


def _sentence_segments(text: str, start: int, end: int) -> list[SourceSegment]:
    segments: list[SourceSegment] = []
    for match in re.finditer(r"[^.!?\n]+(?:[.!?]+(?=\s|$)|$)", text[start:end]):
        sentence_start = start + match.start()
        sentence_end = start + match.end()
        segment = _trimmed_segment(text, sentence_start, sentence_end)
        if segment is None:
            continue
        if len(segment.quote) <= MAX_PASSAGE_CHARACTERS:
            segments.append(segment)
            continue
        for chunk_start in range(segment.start_char, segment.end_char, MAX_PASSAGE_CHARACTERS):
            chunk = _trimmed_segment(
                text,
                chunk_start,
                min(segment.end_char, chunk_start + MAX_PASSAGE_CHARACTERS),
            )
            if chunk is not None:
                segments.append(chunk)
    return segments


def segment_source_text(text: str) -> list[SourceSegment]:
    bounded_text = (text or "")[:MAX_SOURCE_CHARACTERS]
    segments: list[SourceSegment] = []
    cursor = 0
    for boundary in re.finditer(r"\n{2,}|\Z", bounded_text):
        end = boundary.start()
        paragraph = _trimmed_segment(bounded_text, cursor, end)
        if paragraph is not None:
            if len(paragraph.quote) <= MAX_PASSAGE_CHARACTERS:
                segments.append(paragraph)
            else:
                segments.extend(_sentence_segments(bounded_text, paragraph.start_char, paragraph.end_char))
        cursor = boundary.end()
    if not segments and bounded_text:
        segments.extend(_sentence_segments(bounded_text, 0, len(bounded_text)))
    return segments


def score_passage_relevance(claim: str, passage: str) -> RelevanceScore:
    claim_tokens = list(dict.fromkeys(_tokens(claim)))
    passage_tokens = set(_tokens(passage))
    if not claim_tokens:
        return RelevanceScore(0.0, (), 0, 0)
    matched = [token for token in claim_tokens if token in passage_tokens]
    claim_numbers = [token for token in claim_tokens if any(character.isdigit() for character in token)]
    claim_words = [token for token in claim_tokens if token not in claim_numbers]
    matched_numbers = [token for token in claim_numbers if token in passage_tokens]
    matched_words = [token for token in claim_words if token in passage_tokens]
    word_score = len(matched_words) / len(claim_words) if claim_words else 0.0
    if claim_numbers:
        number_score = len(matched_numbers) / len(claim_numbers)
        score = (0.65 * word_score) + (0.35 * number_score)
    else:
        score = word_score
    return RelevanceScore(
        score=round(score, 4),
        matched_terms=tuple(matched),
        claim_term_count=len(claim_tokens),
        matched_term_count=len(matched),
    )


def _confidence(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _rank_candidates(
    document: RawDocument,
    claim_text: str,
    *,
    limit: int,
) -> list[dict]:
    ranked: list[tuple[RelevanceScore, SourceSegment]] = []
    for segment in segment_source_text(document.raw_text or ""):
        relevance = score_passage_relevance(claim_text, segment.quote)
        if relevance.score <= 0:
            continue
        ranked.append((relevance, segment))
    ranked.sort(
        key=lambda item: (
            item[0].score,
            item[0].matched_term_count,
            -len(item[1].quote),
            -item[1].start_char,
        ),
        reverse=True,
    )
    return [
        {
            "quote": segment.quote,
            "start_char": segment.start_char,
            "end_char": segment.end_char,
            "score": relevance.score,
            "confidence": _confidence(relevance.score),
            "matched_terms": list(relevance.matched_terms),
            "claim_term_count": relevance.claim_term_count,
            "matched_term_count": relevance.matched_term_count,
            "internal_href": f"/documents/{document.id}/sections",
        }
        for relevance, segment in ranked[:limit]
    ]


def suggest_ai_citations(
    db: Session,
    output: AiOutput,
    *,
    limit_per_source: int = 3,
) -> list[dict]:
    declared_sources = set(output.source_ids_json or [])
    suggestions: list[dict] = []
    for source_id in extract_source_ids(output.output_text or ""):
        claim_text = claim_for_source_marker(output.output_text or "", source_id)
        base = {
            "source_id": source_id,
            "claim_text": claim_text,
            "source_title": None,
            "candidates": [],
            "limitations": [
                "Deterministic lexical match only; verify that a passage supports the claim before validation.",
            ],
        }
        if source_id not in declared_sources:
            suggestions.append({**base, "status": "undeclared_source"})
            continue
        if not source_id.startswith("raw_document:"):
            suggestions.append({**base, "status": "unsupported_source"})
            continue
        try:
            document_id = int(source_id.split(":", 1)[1])
        except (IndexError, ValueError):
            suggestions.append({**base, "status": "unsupported_source"})
            continue
        document = db.get(RawDocument, document_id)
        if document is None or not (document.raw_text or "").strip():
            suggestions.append({**base, "status": "source_text_unavailable"})
            continue
        base["source_title"] = document.title
        if not claim_text:
            suggestions.append({**base, "status": "claim_text_unavailable"})
            continue
        candidates = _rank_candidates(document, claim_text, limit=limit_per_source)
        limitations = list(base["limitations"])
        if len(document.raw_text or "") > MAX_SOURCE_CHARACTERS:
            limitations.append(
                f"Matching inspected only the first {MAX_SOURCE_CHARACTERS:,} stored characters."
            )
        if not candidates:
            suggestions.append(
                {**base, "status": "no_candidate", "limitations": limitations}
            )
            continue
        if candidates[0]["confidence"] == "low":
            limitations.append("The best candidate has low lexical overlap with the generated claim.")
        suggestions.append(
            {
                **base,
                "status": "ready",
                "candidates": candidates,
                "limitations": limitations,
            }
        )
    return suggestions
