"""Owner-scoped, bounded projection; reads never create a second review store."""
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, literal, select

from app.models import Alert, Company, FinancialExtractionCandidate, Portfolio, PortfolioHolding, ProcessingRun, RawDocument
from app.models.dcf import ValuationSetupDraft
from app.models.thesis_note import ThesisNote, ThesisAssumption, EventThesisImpact


def build_review_queue(db, user_id, *, state=None, company_id=None, portfolio_id=None, limit=50):
    captured = datetime.now(UTC)
    if portfolio_id is not None and not db.scalar(select(Portfolio.id).where(
        Portfolio.id == portfolio_id, Portfolio.user_id == user_id)):
        raise LookupError("Portfolio not found")
    holdings = select(PortfolioHolding.company_id).where(PortfolioHolding.portfolio_id == portfolio_id,
        PortfolioHolding.quantity != 0, PortfolioHolding.company_id.is_not(None))
    # Every query selects scalar columns only; relationship loaders cannot widen scope.
    def query(model, timestamp, title, company, *conditions):
        q = select(model.id.label("id"), timestamp.label("at"), title.label("title"), company.label("company_id")).select_from(model)
        if company_id is not None:
            q = q.where(company == company_id)
        if portfolio_id is not None:
            q = q.where(company.in_(holdings))
        return q.where(timestamp <= captured, *conditions)
    specs = [
        ("financial", "needs_review", "shared_source", "Inspect financial candidates", "Extracted value awaits financial review; this is not approval.",
         query(FinancialExtractionCandidate, FinancialExtractionCandidate.updated_at, FinancialExtractionCandidate.reported_label,
            FinancialExtractionCandidate.company_id, FinancialExtractionCandidate.review_status.in_(["needs_review", "reviewed", "overridden"]))),
        ("alert", "needs_review", "owned", "Review alert", "The alert's own review state requires attention.",
         query(Alert, Alert.created_at, Alert.title, Alert.company_id, Alert.user_id == user_id,
               Alert.review_status.in_(["unreviewed", "needs_follow_up"]))),
        ("draft", "in_progress", "owned", "Resume draft", "A saved setup draft exists. Resuming does not refresh or change its values.",
         query(ValuationSetupDraft, ValuationSetupDraft.updated_at, literal("Valuation setup draft"), ValuationSetupDraft.company_id,
               ValuationSetupDraft.user_id == user_id, ValuationSetupDraft.status.in_(["draft", "ready_to_value"]))),
        ("thesis", "needs_review", "owned", "Review thesis evidence", "An interpretation is unreviewed; reviewing it cannot approve financial facts.",
         query(EventThesisImpact, EventThesisImpact.created_at, ThesisNote.title, ThesisNote.company_id,
               ThesisNote.user_id == user_id, EventThesisImpact.review_status.in_(["unreviewed", "needs_review"]))
            .join(ThesisAssumption, ThesisAssumption.id == EventThesisImpact.thesis_assumption_id)
            .join(ThesisNote, ThesisNote.id == ThesisAssumption.thesis_note_id).add_columns(ThesisNote.id.label("note_id"))),
        ("source_failure", "waiting_for_source", "shared_source", "Inspect source processing", "A public-source attempt failed or completed only partly. Saved models are unchanged.",
         query(ProcessingRun, ProcessingRun.started_at, literal("Public-source processing needs attention"), ProcessingRun.company_id,
               ProcessingRun.source_type.in_(["sec", "rss", "fred", "market_data"]),
               ProcessingRun.status.in_(["failed", "error", "partial"]))),
        ("source", "new_source", "shared_source", "Inspect source", "Source stored within 30 days. Availability does not mean reviewed or used in a model.",
         query(RawDocument, RawDocument.ingested_at, RawDocument.title, RawDocument.company_id,
               RawDocument.ingested_at >= captured - timedelta(days=30),
               RawDocument.document_type.in_(["annual_report", "quarterly_report", "sec_filing_metadata", "earnings_release", "sec_companyfacts"]))),
    ]
    counts = {key: 0 for key in ("needs_review", "waiting_for_source", "in_progress", "new_source")}
    items = []
    for domain, item_state, scope, action, reason, q in specs:
        count = db.scalar(select(func.count()).select_from(q.subquery())) or 0
        counts[item_state] += count
        if state and item_state != state:
            continue
        for row in db.execute(q.order_by(q.selected_columns.at.desc(), q.selected_columns.id.desc()).limit(limit)):
            href = (f"/companies/{row.company_id}/fundamentals#financial-candidate-review" if domain == "financial" else
                f"/companies/{row.company_id}/valuation/draft" if domain == "draft" else
                f"/companies/{row.company_id}/thesis?note_id={row.note_id}#thesis-evidence" if domain == "thesis" else
                f"/documents/{row.id}/sections" if domain == "source" else
                "/alerts" if domain == "alert" else "/data-health")
            at = row.at.replace(tzinfo=UTC) if row.at.tzinfo is None else row.at.astimezone(UTC)
            items.append(dict(identity=f"{domain}:{row.id}:{at.isoformat()}", domain=domain, record_id=row.id,
                company_id=row.company_id, ticker=None, title=row.title, reason=reason, state=item_state,
                relevant_at=at, href=href, action=action, permission_scope=scope,
                severity_basis="Workflow state only; ordered newest first. Not an investment ranking."))
    items.sort(key=lambda item: (item["relevant_at"], item["domain"], item["record_id"]), reverse=True)
    items = items[:limit]
    names = dict(db.execute(select(Company.id, Company.ticker).where(Company.id.in_(
        {item["company_id"] for item in items if item["company_id"] is not None}))).all())
    for item in items:
        item["ticker"] = names.get(item["company_id"])
    total = counts[state] if state else sum(counts.values())
    return dict(captured_at=captured, portfolio_id=portfolio_id, items=items, counts=counts, total=total,
        returned=len(items), limit=limit, truncated=total > len(items),
        basis="Current declared holdings" if portfolio_id else "Shared company sources and this user's private research",
        limitations=["Counts refer to source records, not distinct companies or required investment decisions.",
            "This projection covers candidates, alerts, drafts, thesis evidence and selected public-source runs/documents. It is not a complete source-gap or stale-model inventory.",
            "Historical failed attempts remain visible even after a later successful attempt; inspect processing history.",
            "No provider, AI, model save, approval or portfolio transaction is triggered by this read."])
