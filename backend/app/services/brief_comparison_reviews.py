"""Owned append-only decisions on exact bounded comparison evidence, never approvals."""
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, defer

from app.models.brief_review import BriefComparisonReview as Review
from app.models.user import User
from app.schemas.brief_triage import BriefReviewDetail, BriefReviewEvidence, BriefReviewRead, BriefReviewWrite
from app.services.brief_source_triage import compare_sources


def _read(row: Review, current_hash: str) -> BriefReviewRead:
    return BriefReviewRead(id=row.id, company_id=row.company_id, field=row.field, include_mock=row.include_mock,
        version=row.version, evidence_hash=row.evidence_hash, disposition=row.disposition,
        notes=row.notes, created_at=row.created_at, is_current=row.evidence_hash == current_hash)


def latest_reviews(db: Session, user_id: str, company_id: int, include_mock: bool, current_hash: str) -> list[BriefReviewRead]:
    scope = (Review.user_id == user_id, Review.company_id == company_id, Review.include_mock == include_mock)
    latest = select(func.max(Review.id)).where(*scope).group_by(Review.field)
    rows = db.scalars(select(Review).options(defer(Review.evidence_json)).where(Review.id.in_(latest)).order_by(Review.field)).all()
    return [_read(row, current_hash) for row in rows]


def save_review(db: Session, user_id: str, payload: BriefReviewWrite) -> BriefReviewRead:
    # Serialize a user's short review writes, including the first receipt where
    # no review row exists to lock. No lock is held across external I/O.
    if db.scalar(select(User.id).where(User.id == user_id).with_for_update()) is None:
        raise HTTPException(401, "Not authenticated")
    db.expire_all()
    comparison = compare_sources(db, user_id, payload.company_id, include_mock=payload.include_mock)
    if comparison.evidence_hash != payload.evidence_hash:
        db.rollback()
        raise HTTPException(409, "Comparison evidence changed. Refresh and review it again before saving.")
    group = next((group for group in comparison.groups if group.field == payload.field), None)
    if group is None:
        raise HTTPException(409, "This input has no eligible comparison evidence to review.")
    scope = (Review.user_id == user_id, Review.company_id == payload.company_id,
        Review.field == payload.field, Review.include_mock == payload.include_mock)
    version = db.scalar(select(func.max(Review.version)).where(*scope)) or 0
    if version != payload.expected_version:
        db.rollback()
        raise HTTPException(409, "Another review was saved. Refresh before recording a new decision.")
    source_ids = {item.source_id for item in group.items}
    evidence = BriefReviewEvidence(company_id=comparison.company_id, company_name=comparison.company_name,
        ticker=comparison.ticker, include_mock=comparison.include_mock, methodology=comparison.methodology,
        compared_at=comparison.computed_at, coverage=comparison.coverage, group=group,
        sources=[source for source in comparison.sources if source.id in source_ids])
    row = Review(user_id=user_id, company_id=payload.company_id, field=payload.field, include_mock=payload.include_mock,
        version=version + 1, evidence_hash=comparison.evidence_hash, disposition=payload.disposition,
        notes=payload.notes, evidence_json=evidence.model_dump(mode="json"))
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Another review was saved. Refresh before recording a new decision.") from None
    db.refresh(row)
    return _read(row, comparison.evidence_hash)


def review_history(db: Session, user_id: str, company_id: int, field: str, include_mock: bool,
                   before_id: int | None, limit: int) -> list[BriefReviewRead]:
    comparison = compare_sources(db, user_id, company_id, include_mock=include_mock)
    query = select(Review).where(Review.user_id == user_id, Review.company_id == company_id,
        Review.field == field, Review.include_mock == include_mock)
    if before_id is not None: query = query.where(Review.id < before_id)
    rows = db.scalars(query.order_by(Review.id.desc()).limit(limit)).all()
    return [_read(row, comparison.evidence_hash) for row in rows]


def review_detail(db: Session, user_id: str, review_id: int) -> BriefReviewDetail:
    row = db.scalar(select(Review).where(Review.id == review_id, Review.user_id == user_id))
    if row is None: raise HTTPException(404, "Comparison review not found")
    current = compare_sources(db, user_id, row.company_id, include_mock=row.include_mock)
    return BriefReviewDetail(**_read(row, current.evidence_hash).model_dump(), evidence=row.evidence_json)
