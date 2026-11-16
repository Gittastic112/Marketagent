"""Bounded projection of preserved revisions, with publication and recording kept separate."""
from collections import defaultdict
from datetime import UTC, date, datetime, time
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FinancialExtractionCandidate as Candidate, RawDocument, SourceFactRevision as Revision
from app.services.financial_period_basis import financial_period_basis, period_scope_key
from app.services.financial_review_plan import LABELS, TRACKS, _scaled

MAX_REVISIONS = 2000


def _source_publication(record):
    locator = record.source_locator_json or {}
    if record.document_type != "xbrl_facts":
        return record.published_at
    # A companyfacts snapshot contains different filings. Its retrieval or
    # document timestamp cannot stand in for a particular fact's availability.
    if (locator.get("type") != "xbrl_fact" or record.source_provider != "SEC EDGAR"
            or not record.extraction_method.startswith("sec_xbrl_")
            or not record.payload_sha256 or locator.get("payload_sha256") != record.payload_sha256):
        return None
    filed = locator.get("filed")
    try:
        parsed = date.fromisoformat(filed) if isinstance(filed, str) and len(filed) == 10 else None
    except ValueError:
        return None
    if parsed is None or parsed.isoformat() != filed or parsed < record.effective_at:
        return None
    return datetime.combine(parsed, time.min, tzinfo=UTC)


def dated_financial_inputs(db: Session, company_id: int, *, valuation_date: date,
                           knowledge="available_by_date", track="operating"):
    records = db.execute(select(Revision.id, Revision.fact_key, Revision.value, Revision.unit,
        Revision.effective_at, Revision.observed_at, Revision.revision_number, Revision.claim_type,
        Candidate.id.label("candidate_id"), Candidate.fiscal_year, Candidate.period_type,
        Candidate.source_locator_json, Candidate.source_text, Candidate.extraction_method,
        RawDocument.id.label("document_id"), RawDocument.document_type,
        RawDocument.raw_payload_json["provider"].as_string().label("source_provider"),
        RawDocument.raw_payload_json["payload_sha256"].as_string().label("payload_sha256"),
        RawDocument.published_at, RawDocument.ingested_at)
        .join(Candidate, Candidate.id == Revision.financial_candidate_id)
        .join(RawDocument, RawDocument.id == Revision.raw_document_id)
        .where(Revision.company_id == company_id, Candidate.company_id == company_id,
               RawDocument.company_id == company_id, Revision.effective_at <= valuation_date)
        .order_by(Revision.effective_at.desc(), Revision.observed_at.desc(), Revision.id.desc())
        .limit(MAX_REVISIONS + 1)).all()
    truncated = len(records) > MAX_REVISIONS
    grouped = defaultdict(list)
    for source_record in records[:MAX_REVISIONS]:
        record = SimpleNamespace(**source_record._mapping)
        record.published_at = _source_publication(record)
        grouped[record.fact_key].append(record)
    rows = []
    for metric in dict.fromkeys([*TRACKS[track], *sorted(grouped)]):
        candidates = grouped[metric]
        # Each metric displays its own period; there is no synthetic common year.
        dated = [r for r in candidates if knowledge == "latest_recorded" or (
            r.published_at is not None and r.published_at.date() <= valuation_date)]
        latest_end = max((r.effective_at for r in dated or candidates), default=None)
        current = [r for r in candidates if r.effective_at == latest_end]
        sources, eligible = [], []
        for r in current:
            availability = "publication_unknown" if r.published_at is None else (
                "available_by_date" if r.published_at.date() <= valuation_date else "published_later")
            basis = financial_period_basis(r, effective_at=r.effective_at)
            sources.append(dict(revision_id=r.id, revision_number=r.revision_number, candidate_id=r.candidate_id,
                document_id=r.document_id, href=f"/documents/{r.document_id}/sections?candidate_id={r.candidate_id}",
                value=r.value, unit=r.unit, claim_type=r.claim_type, published_at=r.published_at,
                recorded_at=r.observed_at, retrieved_at=r.ingested_at, availability=availability,
                period=basis, locator=r.source_locator_json or {}, passage=(r.source_text or "")[:2000]))
            if knowledge == "latest_recorded" or availability == "available_by_date":
                eligible.append(r)
        chosen = None
        status = "missing" if not current else "unavailable_by_date"
        limitations = []
        if eligible:
            # Same-publication competing claims and distinct period/basis scopes stay unresolved.
            rank = (lambda r: r.observed_at) if knowledge == "latest_recorded" else (lambda r: r.published_at)
            latest = max(rank(r) for r in eligible)
            contenders = [r for r in eligible if rank(r) == latest]
            identities = {period_scope_key(s["period"]) for s in sources if s["revision_id"] in {r.id for r in eligible}}
            if len({(r.value, r.unit) for r in contenders}) > 1 or len(identities) > 1:
                status = "conflict"
                limitations.append("Competing values or period/accounting scopes require source selection; no value was chosen.")
            else:
                chosen = max(contenders, key=lambda r: (r.observed_at, r.id))
                status = "available"
        currency = None
        if chosen and chosen.unit:
            first = chosen.unit.split()[0]
            currency = first if len(first) == 3 and first.isalpha() and first.isupper() else None
        normalized = _scaled(metric, chosen.value, chosen.unit, currency) if chosen else None
        if chosen and normalized is None:
            status = "unit_review"
            limitations.append("Original units are retained; a full-unit conversion is not available.")
        if chosen:
            selected = next(s for s in sources if s["revision_id"] == chosen.id)
            if selected["period"]["identity_status"] == "legacy_date_only":
                limitations.append("Legacy reporting date only; original period dates are unverified.")
            if not selected["period"].get("accounting_basis"):
                limitations.append("Accounting basis is not recorded.")
        rows.append(dict(metric=metric, label=LABELS.get(metric, metric.replace("_", " ").capitalize()),
            status=status, selected_revision_id=chosen.id if chosen else None,
            original_value=chosen.value if chosen else None, original_unit=chosen.unit if chosen else None,
            normalized_value=normalized, normalized_unit="shares" if metric == "diluted_shares" else currency,
            conversion=f"{chosen.value:g} {chosen.unit} = {normalized:g} full units" if chosen and normalized is not None else None,
            claim_type=chosen.claim_type if chosen else None, effective_at=latest_end, sources=sources, limitations=limitations))
    return dict(company_id=company_id, valuation_date=valuation_date, knowledge=knowledge, track=track,
        rows=rows, truncated=truncated, limitations=[
            "Read-only evidence checklist, not complete model inputs or approval. No saved model is changed.",
            "Publication dates are recorded source metadata, not certified historical source vintages. Later retrieval is shown separately.",
            "SEC companyfacts evidence uses each original fact's filed date, not the snapshot retrieval date. Missing or unverified filing dates stay unknown.",
            "Each input retains its own reporting period. Annual, interim and point-in-time scopes are not combined.",
            *( ["Revision scan limit reached; coverage and selection may be partial."] if truncated else []),
        ])
