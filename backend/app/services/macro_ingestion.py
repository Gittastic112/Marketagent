from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import math
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.macro import MacroObservation, MacroSeries
from app.providers.fred_provider import FredProvider


FRED_SERIES_ID_PATTERN = re.compile(r"^[A-Z0-9_.-]{1,50}$")


@dataclass(frozen=True)
class FredIngestionResult:
    series_id: str
    macro_series_id: int
    source_url: str
    fetched_count: int
    created_count: int
    skipped_duplicate_count: int
    skipped_missing_count: int
    error_count: int
    errors: tuple[str, ...]


def normalize_fred_series_id(series_id: str) -> str:
    normalized = series_id.strip().upper()
    if not FRED_SERIES_ID_PATTERN.fullmatch(normalized):
        raise ValueError(
            "FRED series ID must contain only letters, numbers, dot, dash, or underscore."
        )
    return normalized


def fred_series_url(series_id: str) -> str:
    return f"https://fred.stlouisfed.org/series/{series_id}"


def ingest_fred_series(
    db: Session,
    series_id: str,
    api_key: str | None = None,
) -> FredIngestionResult:
    """Fetch one FRED series and persist valid, previously unseen observations."""
    normalized_id = normalize_fred_series_id(series_id)
    provider = FredProvider(api_key=api_key)
    series_info = provider.fetch_series_info(normalized_id)
    provider_series_id = normalize_fred_series_id(str(series_info.get("id") or ""))
    if provider_series_id != normalized_id:
        raise ValueError("FRED returned metadata for a different series.")

    observations = provider.fetch_observations(normalized_id)
    if not isinstance(observations, list):
        raise RuntimeError("FRED observations response was not a list.")
    series = db.scalar(select(MacroSeries).where(MacroSeries.name == normalized_id))
    source_url = fred_series_url(normalized_id)
    if series is not None and (series.provider_name != "FRED" or series.source_url != source_url):
        raise ValueError("An existing non-FRED series cannot be relabelled as FRED evidence.")
    if series is None:
        series = MacroSeries(name=normalized_id)
        db.add(series)
    series.description = series_info.get("title")
    series.units = series_info.get("units_short")
    series.frequency = series_info.get("frequency_short")
    series.provider_name = provider.provider_name
    series.source_url = source_url
    db.flush()

    existing_values = dict(db.execute(select(MacroObservation.date_recorded, MacroObservation.value)
        .where(MacroObservation.series_id == series.id)).all())
    created_count = 0
    duplicate_count = 0
    missing_count = 0
    errors: list[str] = []

    for observation in observations:
        if not isinstance(observation, dict):
            errors.append("FRED_OBSERVATION_INVALID")
            continue
        raw_value = observation.get("value")
        if raw_value is None or raw_value == "" or raw_value == ".":
            missing_count += 1
            continue
        try:
            recorded_date = datetime.strptime(
                str(observation.get("date")), "%Y-%m-%d"
            ).date()
            numeric_value = float(raw_value)
            if not math.isfinite(numeric_value) or recorded_date > date.today() or isinstance(raw_value, bool):
                raise ValueError("non-finite observation")
        except (TypeError, ValueError):
            errors.append("FRED_OBSERVATION_INVALID")
            continue
        if recorded_date in existing_values:
            if existing_values[recorded_date] != numeric_value:
                errors.append("FRED_OBSERVATION_REVISION_REQUIRES_REVIEW")
                continue
            duplicate_count += 1
            continue
        db.add(
            MacroObservation(
                series_id=series.id,
                date_recorded=recorded_date,
                value=numeric_value,
            )
        )
        existing_values[recorded_date] = numeric_value
        created_count += 1

    db.commit()
    return FredIngestionResult(
        series_id=normalized_id,
        macro_series_id=series.id,
        source_url=source_url,
        fetched_count=len(observations),
        created_count=created_count,
        skipped_duplicate_count=duplicate_count,
        skipped_missing_count=missing_count,
        error_count=len(errors),
        errors=tuple(errors),
    )
