"""Transcript intake with distinct event, publication and observation times."""
from __future__ import annotations

import hashlib
import math
import re
from datetime import UTC, datetime

from app.providers.research_sources.errors import SourceAdapterError
from app.providers.research_sources.http import fetch_transcript_json
from app.schemas.source_adapters import TranscriptEvidence, TranscriptRequest, TranscriptSegment


def _invalid() -> SourceAdapterError:
    return SourceAdapterError("TRANSCRIPT_SCHEMA_INVALID", "Transcript identity or content does not match the requested call.", 502)


def _aware_time(value) -> datetime | None:
    if not value:
        return None
    if not isinstance(value, str):
        raise _invalid()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise _invalid() from None
    # Do not invent a timezone, or turn a date-only call into a precise instant.
    return parsed.astimezone(UTC) if parsed.tzinfo is not None else None


def _segment(text: str, index: int, *, speaker=None, section=None, start=None) -> TranscriptSegment:
    if not isinstance(text, str) or not text.strip():
        raise _invalid()
    digest = hashlib.sha256(text.encode()).hexdigest()[:16]
    return TranscriptSegment(segment_id=f"segment-{index}-{digest}", text=text,
        speaker=speaker, section=section, start_seconds=start)


def normalize_earningscall(payload: dict | list, *, symbol: str, exchange: str,
                           request: TranscriptRequest, observed_at: datetime) -> TranscriptEvidence:
    if not isinstance(payload, dict):
        raise _invalid()
    event = payload.get("event")
    if (not isinstance(event, dict) or payload.get("symbol") != symbol
            or payload.get("exchange") != exchange or payload.get("level") != request.level
            or event.get("year") != request.fiscal_year or event.get("quarter") != request.fiscal_quarter):
        raise _invalid()
    segments = []
    if request.level == 1:
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            raise _invalid()
        segments = [_segment(part, i) for i, part in enumerate(text.split("\n\n")) if part.strip()]
    elif request.level in {2, 3}:
        turns = payload.get("speakers")
        if not isinstance(turns, list) or not turns or len(turns) > 10000:
            raise _invalid()
        for index, turn in enumerate(turns):
            if not isinstance(turn, dict) or not isinstance(turn.get("speaker"), dict):
                raise _invalid()
            speaker = turn["speaker"].get("name") or turn["speaker"].get("id")
            if not isinstance(speaker, str):
                raise _invalid()
            start = None
            if request.level == 3:
                words, times = turn.get("words"), turn.get("start_times")
                if (not isinstance(words, list) or not isinstance(times, list) or not words
                        or len(words) != len(times) or not all(isinstance(word, str) for word in words)
                        or any(isinstance(t, bool) or not isinstance(t, (float, int))
                               or not math.isfinite(t) or t < 0 for t in times)
                        or times != sorted(times)):
                    raise _invalid()
                text, start = " ".join(words), float(times[0])
            else:
                text = turn.get("text")
            segments.append(_segment(text, index, speaker=speaker, start=start))
        text = "\n\n".join(f"{s.speaker}: {s.text}" for s in segments)
    else:
        for key in ("prepared_remarks", "questions_and_answers"):
            part = payload.get(key)
            if not isinstance(part, str):
                raise _invalid()
            if part.strip():
                segments.append(_segment(part, len(segments), section=key))
        text = "\n\n".join(s.text for s in segments)
    if not text.strip():
        raise _invalid()
    call_at = _aware_time(event.get("conference_date"))
    warnings = ["PUBLICATION_TIME_UNKNOWN", "TRANSCRIPT_REQUIRES_REVIEW"]
    if call_at is None:
        warnings.append("CALL_TIME_PRECISION_OR_TIMEZONE_UNKNOWN")
    return TranscriptEvidence(provider="earningscall", provider_record_id=f"{exchange}:{symbol}:{request.fiscal_year}:Q{request.fiscal_quarter}:L{request.level}",
        symbol=symbol, exchange=exchange, fiscal_year=request.fiscal_year, fiscal_quarter=request.fiscal_quarter,
        call_at=call_at, published_at=None, observed_at=observed_at, text=text, segments=segments,
        api_version="v4", raw_payload=payload, warnings=warnings)


def normalize_fmp(payload: dict | list, *, symbol: str, request: TranscriptRequest,
                  observed_at: datetime) -> TranscriptEvidence:
    if not isinstance(payload, list) or len(payload) != 1 or not isinstance(payload[0], dict):
        if payload == []:
            raise SourceAdapterError("TRANSCRIPT_UNAVAILABLE", "No transcript is available for the requested call.", 404)
        raise _invalid()
    row = payload[0]
    year = row.get("year", row.get("fiscalYear"))
    quarter = row.get("period", row.get("quarter"))
    if row.get("symbol") != symbol or str(year) != str(request.fiscal_year) or str(quarter).upper() not in {str(request.fiscal_quarter), f"Q{request.fiscal_quarter}"}:
        raise _invalid()
    text = row.get("content")
    if not isinstance(text, str) or not text.strip():
        raise _invalid()
    segments = [_segment(part, i) for i, part in enumerate(text.split("\n\n")) if part.strip()]
    call_at = _aware_time(row.get("date"))
    warnings = ["PUBLICATION_TIME_UNKNOWN", "TRANSCRIPT_REQUIRES_REVIEW"]
    if call_at is None:
        warnings.append("CALL_DATE_RETAINED_WITHOUT_INVENTED_TIMEZONE")
    return TranscriptEvidence(provider="fmp", provider_record_id=f"{symbol}:{request.fiscal_year}:Q{request.fiscal_quarter}",
        symbol=symbol, exchange=None, fiscal_year=request.fiscal_year, fiscal_quarter=request.fiscal_quarter,
        call_at=call_at, published_at=None, observed_at=observed_at, text=text, segments=segments,
        api_version="stable", raw_payload=payload, warnings=warnings)


def fetch_transcript(*, request: TranscriptRequest, symbol: str, exchange: str | None,
                     api_key: str | None, observed_at: datetime | None = None) -> TranscriptEvidence:
    if not api_key:
        raise SourceAdapterError("PROVIDER_NOT_CONFIGURED", "The selected transcript provider is not configured.", 503)
    if not re.fullmatch(r"[A-Z0-9_.:-]{1,40}", symbol):
        raise SourceAdapterError("IDENTITY_UNSUPPORTED", "The company needs a supported provider symbol.")
    params = {"apikey": api_key, "symbol": symbol, "year": request.fiscal_year, "quarter": request.fiscal_quarter}
    if request.provider == "earningscall":
        if not exchange or not re.fullmatch(r"[A-Z0-9_.-]{1,20}", exchange):
            raise SourceAdapterError("EXCHANGE_REQUIRED", "EarningsCall requires an explicitly resolved exchange.")
        params.update(exchange=exchange, level=request.level)
    elif request.level != 1:
        raise SourceAdapterError("UNSUPPORTED_TRANSCRIPT_LEVEL", "The FMP adapter supports original transcript text only.")
    payload = fetch_transcript_json(request.provider, params)
    observed_at = observed_at or datetime.now(UTC)
    if request.provider == "earningscall":
        return normalize_earningscall(payload, symbol=symbol, exchange=exchange, request=request, observed_at=observed_at)
    return normalize_fmp(payload, symbol=symbol, request=request, observed_at=observed_at)
