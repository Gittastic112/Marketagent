from datetime import datetime
from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.macro import MacroSeries, MacroObservation
from app.providers.fred_provider import FredProvider

def ingest_fred_series(db: Session, series_id: str, api_key: str | None = None) -> Dict[str, Any]:
    """
    Fetches a FRED series and its observations, and saves them to the database.
    """
    provider = FredProvider(api_key=api_key)
    
    # Fetch series metadata
    series_info = provider.fetch_series_info(series_id)
    
    # Check if series exists
    series = db.scalar(select(MacroSeries).where(MacroSeries.name == series_info["id"]))
    
    if not series:
        series = MacroSeries(
            name=series_info["id"],
            description=series_info.get("title"),
            units=series_info.get("units_short"),
            frequency=series_info.get("frequency_short")
        )
        db.add(series)
        db.flush()
        
    # Fetch observations
    observations = provider.fetch_observations(series_id)
    
    # We need to skip existing observations
    existing_dates = set(
        db.scalars(
            select(MacroObservation.date_recorded)
            .where(MacroObservation.series_id == series.id)
        )
    )
    
    created_count = 0
    for obs in observations:
        if obs["value"] == ".":
            continue # FRED uses '.' for missing values
            
        try:
            date_recorded = datetime.strptime(obs["date"], "%Y-%m-%d").date()
            if date_recorded not in existing_dates:
                db.add(MacroObservation(
                    series_id=series.id,
                    date_recorded=date_recorded,
                    value=float(obs["value"])
                ))
                created_count += 1
        except ValueError:
            continue
            
    db.commit()
    
    return {
        "series_id": series_id,
        "observations_fetched": len(observations),
        "observations_created": created_count
    }
