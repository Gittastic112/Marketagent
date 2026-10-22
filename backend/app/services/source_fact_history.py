from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import FinancialExtractionCandidate, SourceFactRevision


def record_financial_fact_revision(
    db: Session,
    candidate: FinancialExtractionCandidate,
    *,
    effective_at: date,
) -> SourceFactRevision:
    existing = db.scalar(
        select(SourceFactRevision).where(
            SourceFactRevision.financial_candidate_id == candidate.id
        )
    )
    if existing is not None:
        return existing

    observed_at = datetime.now(UTC)
    active = db.scalars(
        select(SourceFactRevision)
        .where(
            SourceFactRevision.company_id == candidate.company_id,
            SourceFactRevision.fact_key == candidate.metric_code,
            SourceFactRevision.period_type == candidate.period_type,
            SourceFactRevision.effective_at == effective_at,
            SourceFactRevision.superseded_at.is_(None),
        )
        .order_by(SourceFactRevision.revision_number.desc())
    ).all()
    # Legacy repeated occurrences may have more than one active revision. A
    # newly promoted fact supersedes every prior occurrence in this exact scope.
    for revision in active:
        revision.superseded_at = observed_at
    latest_revision = db.scalar(
        select(func.max(SourceFactRevision.revision_number)).where(
            SourceFactRevision.company_id == candidate.company_id,
            SourceFactRevision.fact_key == candidate.metric_code,
            SourceFactRevision.period_type == candidate.period_type,
            SourceFactRevision.effective_at == effective_at,
        )
    ) or 0
    locator = candidate.source_locator_json or {}
    claim_type = locator.get("claim_type", "Fact")
    if claim_type not in {"Fact", "Calculation"}:
        claim_type = "Fact"
    revision = SourceFactRevision(
        company_id=candidate.company_id,
        raw_document_id=candidate.raw_document_id,
        financial_candidate_id=candidate.id,
        fact_key=candidate.metric_code,
        value=candidate.value,
        unit=candidate.unit,
        period_type=candidate.period_type,
        effective_at=effective_at,
        observed_at=observed_at,
        revision_number=latest_revision + 1,
        claim_type=claim_type,
    )
    db.add(revision)
    return revision


def list_source_facts_as_of(
    db: Session,
    company_id: int,
    *,
    as_of: datetime | None = None,
) -> list[SourceFactRevision]:
    cutoff = as_of or datetime.now(UTC)
    revisions = list(
        db.scalars(
            select(SourceFactRevision)
            .where(
                SourceFactRevision.company_id == company_id,
                SourceFactRevision.observed_at <= cutoff,
            )
            .order_by(
                SourceFactRevision.effective_at.desc(),
                SourceFactRevision.fact_key,
                SourceFactRevision.observed_at.desc(),
            )
        )
    )
    latest: dict[tuple[str, str, date], SourceFactRevision] = {}
    for revision in revisions:
        key = (revision.fact_key, revision.period_type, revision.effective_at)
        latest.setdefault(key, revision)
    return list(latest.values())
