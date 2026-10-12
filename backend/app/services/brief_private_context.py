"""Bounded, owned research receipts for deterministic brief snapshots. No AI calls."""
from collections import Counter
from datetime import UTC, date, datetime
from hashlib import sha256
import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.brief_source import BriefSource
from app.schemas.brief_context import BriefResearchContext, BriefResearchDecision, BriefResearchSource
from app.services.brief_comparison_reviews import latest_reviews
from app.services.brief_source_triage import compare_sources

COMPANY_LIMIT = 10
SOURCE_LIMIT = 20
DECISION_LIMIT = 30


def snapshot_private_research(db: Session, user_id: str, target_date: date) -> dict:
    scope = (BriefSource.user_id == user_id, BriefSource.archived_at.is_(None))
    company_count = db.scalar(select(func.count(func.distinct(BriefSource.company_id))).where(*scope)) or 0
    company_ids = list(db.scalars(select(BriefSource.company_id).where(*scope).group_by(BriefSource.company_id)
        .order_by(func.max(BriefSource.id).desc()).limit(COMPANY_LIMIT)))
    excluded = Counter(companies_outside_limit=max(0, company_count - COMPANY_LIMIT))
    sources, reviewed, queue, hashes, seen_content = [], [], [], [], set()
    for company_id in company_ids:
        comparison = compare_sources(db, user_id, company_id, include_mock=False)
        hashes.append(comparison.evidence_hash)
        excluded.update(comparison.coverage.excluded)
        excluded["archived"] += comparison.coverage.archived_sources
        excluded["sources_outside_comparison_limit"] += comparison.coverage.not_examined
        reviews = {review.field: review for review in latest_reviews(db, user_id, company_id, False, comparison.evidence_hash)}
        included_ids = set()
        by_id = {source.id: source for source in comparison.sources}
        for source in comparison.sources:
            if source.created_at.date() > target_date or source.generated_at.date() > target_date or (source.as_of_date and source.as_of_date > target_date):
                excluded["after_requested_date"] += 1
                continue
            # Original text hash, not an AI paraphrase, identifies known copies.
            content_hash = source.content_sha256 or source.source_sha256
            if content_hash in seen_content:
                excluded["duplicate_content"] += 1
                continue
            if len(sources) >= SOURCE_LIMIT:
                excluded["sources_outside_snapshot_limit"] += 1
                continue
            seen_content.add(content_hash)
            included_ids.add(source.id)
            sources.append(BriefResearchSource(source=source, content_hash=content_hash,
                freshness="unknown" if source.as_of_date is None else "historical" if source.as_of_date < target_date else "dated_today",
                href=f"/daily-brief/sources/{source.id}"))
        for group in comparison.groups:
            if len(reviewed) + len(queue) >= DECISION_LIMIT:
                excluded["decisions_outside_limit"] += 1
                continue
            ids = sorted({item.source_id for item in group.items})
            if not included_ids.intersection(ids):
                continue
            receipt = reviews.get(group.field)
            if receipt and receipt.created_at.date() > target_date:
                receipt = None
                excluded["receipts_after_requested_date"] += 1
            state = "reviewed"
            if not set(ids).issubset(included_ids):
                state = "incomplete_source_snapshot"
            elif receipt is not None and not receipt.is_current:
                state = "stale_receipt"
            elif group.comparability_status == "incompatible":
                state = "incompatible_basis"
            elif any(by_id[source_id].review_status != "approved" for source_id in ids):
                state = "pending_ai_review"
            elif receipt is None:
                state = "missing_receipt"
            decision = BriefResearchDecision(company_id=company_id, ticker=comparison.ticker, field=group.field,
                comparison_hash=comparison.evidence_hash, comparability_status=group.comparability_status,
                source_ids=ids, receipt=receipt, state=state,
                href=f"/daily-brief/triage?company_id={company_id}")
            (reviewed if state == "reviewed" else queue).append(decision)
    context = BriefResearchContext(captured_at=datetime.now(UTC), as_of_date=target_date,
        status="partial" if queue or any(excluded.values()) else "complete" if sources else "empty", input_sha256="",
        company_count=company_count, company_limit=COMPANY_LIMIT, source_limit=SOURCE_LIMIT, decision_limit=DECISION_LIMIT,
        excluded=dict(excluded), sources=sources, reviewed=reviewed, review_queue=queue,
        limitations=["Saved as generated. Source lifecycle and analyst decisions may have changed; open the linked current record before relying on it.",
            "Analyst dispositions are User Assumptions, not source verification or numerical input approval. AI findings remain AI Interpretation.",
            "Historical and unknown source dates are shown explicitly. Matching labels, copied sources and opposing suggestions are not corroboration."])
    basis = {"owner": user_id, "comparisons": hashes, "context": context.model_dump(mode="json", exclude={"captured_at", "input_sha256"})}
    context.input_sha256 = sha256(json.dumps(basis, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return context.model_dump(mode="json")
