from __future__ import annotations

from datetime import date
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.macro import MacroObservation, MacroSeries
from app.models.market_regime_input import MarketRegimeInput
from app.services.market_regime_engine import MarketRegimeEngine


SUPPORTED_SERIES_ID = "NFCI"
SOURCE_NAME = "Federal Reserve Bank of Chicago via FRED"
SOURCE_URL = "https://fred.stlouisfed.org/series/NFCI"
FRESHNESS_THRESHOLD_DAYS = MarketRegimeEngine.FRESHNESS_DAYS["macro"]
METHODOLOGY = (
    "Calculation: NFCI is a standardized financial-conditions index where positive values "
    "indicate tighter-than-average conditions. Regime macro score = clamp(-NFCI × 50, "
    "-100, 100), so NFCI +2 maps to -100 and NFCI -2 maps to +100."
)


def normalize_nfci(value: float) -> float:
    numeric_value = float(value)
    if not math.isfinite(numeric_value):
        raise ValueError("NFCI observation must be finite.")
    return round(max(-100.0, min(100.0, -numeric_value * 50.0)), 4)


def preview_nfci_macro_input(
    db: Session,
    *,
    target_date: date | None = None,
) -> dict:
    effective_date = target_date or date.today()
    series = db.scalar(select(MacroSeries).where(MacroSeries.name == SUPPORTED_SERIES_ID))
    blockers: list[str] = []
    warnings: list[str] = []
    observation = None

    if series is None:
        blockers.append("Import the FRED NFCI series before applying provider-backed macro data.")
    else:
        if series.provider_name != "FRED" or series.source_url != SOURCE_URL:
            blockers.append(
                "The stored NFCI series lacks verified FRED provenance; refresh it through FRED ingestion."
            )
        observation = db.scalar(
            select(MacroObservation)
            .where(
                MacroObservation.series_id == series.id,
                MacroObservation.date_recorded <= effective_date,
            )
            .order_by(MacroObservation.date_recorded.desc(), MacroObservation.id.desc())
            .limit(1)
        )
        if observation is None:
            blockers.append("The stored NFCI series has no observation on or before the target date.")
        elif not math.isfinite(observation.value):
            blockers.append("The latest NFCI observation is not a finite numeric value.")

    age_days = (
        (effective_date - observation.date_recorded).days
        if observation is not None
        else None
    )
    is_stale = age_days is not None and age_days > FRESHNESS_THRESHOLD_DAYS
    if is_stale:
        warnings.append(
            f"The latest NFCI observation is {age_days} days old; the macro threshold is "
            f"{FRESHNESS_THRESHOLD_DAYS} days. Applying it will produce a stale regime state."
        )

    applied_input = None
    if observation is not None:
        applied_input = db.scalar(
            select(MarketRegimeInput).where(
                MarketRegimeInput.metric_name == "macro",
                MarketRegimeInput.input_type == "provider",
                MarketRegimeInput.source_record_type == "macro_observation",
                MarketRegimeInput.source_record_id == observation.id,
            )
        )

    return {
        "metric_name": "macro",
        "series_id": SUPPORTED_SERIES_ID,
        "macro_series_id": series.id if series is not None else None,
        "observation_id": observation.id if observation is not None else None,
        "observed_value": observation.value if observation is not None else None,
        "normalized_value": (
            normalize_nfci(observation.value)
            if observation is not None and math.isfinite(observation.value)
            else None
        ),
        "as_of_date": observation.date_recorded if observation is not None else None,
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "methodology": METHODOLOGY,
        "claim_type": "Calculation",
        "freshness_threshold_days": FRESHNESS_THRESHOLD_DAYS,
        "age_days": age_days,
        "is_stale": is_stale,
        "can_apply": not blockers and applied_input is None,
        "blockers": blockers,
        "warnings": warnings,
        "applied_input_id": applied_input.id if applied_input is not None else None,
        "created": False,
    }


def apply_nfci_macro_input(
    db: Session,
    *,
    target_date: date | None = None,
) -> dict:
    preview = preview_nfci_macro_input(db, target_date=target_date)
    if preview["blockers"]:
        raise ValueError(" ".join(preview["blockers"]))

    existing = (
        db.get(MarketRegimeInput, preview["applied_input_id"])
        if preview["applied_input_id"] is not None
        else None
    )
    created = existing is None
    if existing is None:
        existing = MarketRegimeInput(
            metric_name="macro",
            value=preview["normalized_value"],
            as_of_date=preview["as_of_date"],
            source_url=SOURCE_URL,
            source_name=SOURCE_NAME,
            input_type="provider",
            methodology=METHODOLOGY,
            source_record_type="macro_observation",
            source_record_id=preview["observation_id"],
        )
        db.add(existing)
        db.commit()
        db.refresh(existing)
        MarketRegimeEngine(db).calculate_regime_score(target_date or date.today())

    return {
        **preview,
        "applied_input_id": existing.id,
        "created": created,
    }
