"""Owner-scoped source organization, independent of immutable evidence/review."""
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.brief_source import BriefSource
from app.schemas.brief_sources import BriefSourceLifecycleWrite


def set_source_lifecycle(db: Session, user_id: str, source_id: int, payload: BriefSourceLifecycleWrite) -> BriefSource:
    # Serialize short organization writes with scan claims, never hold a lock
    # across provider I/O. Refresh an already-loaded identity-map row as well.
    source = db.scalar(select(BriefSource).where(BriefSource.id == source_id, BriefSource.user_id == user_id)
        .with_for_update().execution_options(populate_existing=True))
    if source is None:
        raise HTTPException(404, "Brief source not found")
    if source.lifecycle_version != payload.expected_version:
        db.rollback()
        raise HTTPException(409, "Source organization changed in another request. Reload before trying again.")
    if (source.archived_at is not None) == payload.archived:
        db.commit()
        return source
    now = datetime.now(UTC)
    if source.analysis_status == "scanning":
        started = source.analysis_started_at
        if started and started.replace(tzinfo=UTC) > now - timedelta(minutes=2):
            db.rollback()
            raise HTTPException(409, "A scan is still in progress. Wait for it to finish, then reload. Interrupted scans can be archived after two minutes.")
        # Abandon an expired attempt. A late response cannot resurrect it, even
        # if this source is restored before that provider response arrives.
        source.analysis_status = "failed"
        source.analysis_started_at = None
    source.archived_at = now if payload.archived else None
    source.lifecycle_version += 1
    db.commit()
    db.refresh(source)
    return source
