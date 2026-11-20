"""Bind a private thesis decision to the exact observed close and reviewed evidence."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from app.models import Company, Event, FinancialExtractionCandidate, RawDocument, SourceFactRevision, ThesisNote
from app.models.dcf import DcfAssumptionSet, ValuationModel
from app.models.thesis_note import ThesisAssumption, ThesisChange, ThesisPricePin
from app.schemas.publication import document_publication
from app.services.assumption_versions import _hash
from app.services.price_timeline import _utc, company_timeline


def _owned(db, note_id, pin_id, owner, *, lock=False):
    note = select(ThesisNote).where(ThesisNote.id == note_id, ThesisNote.user_id == owner)
    note = db.scalar(note.with_for_update(of=ThesisNote).execution_options(populate_existing=True) if lock else note)
    pin = db.get(ThesisPricePin, pin_id)
    if not note or not pin or pin.thesis_note_id != note.id or pin.company_id != note.company_id:
        raise HTTPException(404, "Pinned observation not found for this thesis")
    return note, pin


def decision_choices(db, note_id, pin_id, owner):
    note, pin = _owned(db, note_id, pin_id, owner)
    day = date.fromisoformat(pin.anchor["date"])
    timeline = company_timeline(db, note.company_id, owner, pin.anchor["key"], day)
    point = next((p for p in timeline.points if p.date == day), None)
    preceding = next((p for p in timeline.points if point and p.date == point.previous_date), None)
    originals = []
    seen = set()
    for observed, scope in ((point, "selected close"), (preceding, "preceding close")):
        for source in observed.sources if observed else ():
            key = (source.document_id, source.event_id)
            if key not in seen:
                originals.append({**source.model_dump(mode="json"), "close_context": scope})
                seen.add(key)
    ids = {s["document_id"] for s in originals}
    refs = db.scalars(select(SourceFactRevision).where(SourceFactRevision.company_id == note.company_id,
        SourceFactRevision.raw_document_id.in_(ids)).order_by(SourceFactRevision.id.desc()).limit(201)).all() if ids else []
    versions = db.execute(select(DcfAssumptionSet.id, ValuationModel.name).join(ValuationModel)
        .where(ValuationModel.company_id == note.company_id, ValuationModel.user_id == owner)
        .order_by(DcfAssumptionSet.id.desc()).limit(101)).all()
    return dict(assumptions=[dict(id=a.id, label=a.description) for a in note.assumptions],
        originals=originals, revisions=[dict(id=r.id, document_id=r.raw_document_id, label=f"{r.fact_key} · revision {r.revision_number}") for r in refs[:200]],
        versions=[dict(id=i, label=n) for i,n in versions[:100]], partial=timeline.context_limited or len(refs)>200 or len(versions)>100)


def _context(db, note, pin, command, lock=False):
    def resolve(query):
        if lock:
            query = query.with_for_update(of=query.column_descriptions[0]["entity"]).execution_options(populate_existing=True)
        return db.scalar(query)
    assumption = resolve(select(ThesisAssumption).where(ThesisAssumption.id == command.assumption_id,
                         ThesisAssumption.thesis_note_id == note.id))
    if not assumption:
        raise HTTPException(404, "Assumption not found for this thesis")
    original, baseline = None, None
    if command.original:
        ref = command.original
        doc = resolve(select(RawDocument).where(RawDocument.id == ref.id, RawDocument.company_id == note.company_id))
        if not doc:
            raise HTTPException(404, "Original not found for this company")
        meta = doc.raw_payload_json or {}
        publication = document_publication(doc.published_at, doc.document_type, meta.get("source_kind"), meta.get("publication_precision"))
        if doc.document_type == "xbrl_facts":
            # A dataset retrieval timestamp cannot date an individual original filing.
            publication = None
        original = dict(kind="raw_document", id=doc.id, content_hash=doc.content_hash, title=doc.title,
                        url=doc.url, revision=None, event_id=None)
        if ref.revision_id is not None:
            rev = resolve(select(SourceFactRevision).where(SourceFactRevision.id == ref.revision_id,
                SourceFactRevision.raw_document_id == doc.id, SourceFactRevision.company_id == note.company_id))
            if not rev:
                raise HTTPException(404, "Revision not found for this original")
            candidate = resolve(select(FinancialExtractionCandidate).where(FinancialExtractionCandidate.id == rev.financial_candidate_id,
                FinancialExtractionCandidate.company_id == note.company_id, FinancialExtractionCandidate.raw_document_id == doc.id))
            if not candidate:
                raise HTTPException(404, "Original revision locator unavailable")
            original["revision"] = dict(kind="source_fact_revision", id=rev.id, number=rev.revision_number,
                metric=rev.fact_key, value=rev.value, unit=rev.unit, effective_at=rev.effective_at, superseded_at=rev.superseded_at,
                locator=candidate.source_locator_json, candidate_id=candidate.id, review_status=candidate.review_status)
            if doc.document_type == "xbrl_facts":
                from types import SimpleNamespace
                from app.services.dated_financial_inputs import _source_publication
                publication = _source_publication(SimpleNamespace(source_locator_json=candidate.source_locator_json,
                    document_type=doc.document_type, source_provider=meta.get("provider"), extraction_method=candidate.extraction_method,
                    source_kind=meta.get("source_kind"), adapter=meta.get("adapter"), document_url=doc.url,
                    payload_sha256=meta.get("payload_sha256"), effective_at=rev.effective_at))
        if ref.event_id is not None:
            event = resolve(select(Event).where(Event.id == ref.event_id, Event.raw_document_id == doc.id,
                                            Event.company_id == note.company_id))
            if not event:
                raise HTTPException(404, "Event not found for this original")
            original["event_id"] = event.id
            original["event_time"] = event.event_time
        original["published"] = publication
        close_time = pin.anchor.get("source_timestamp")
        if isinstance(publication, datetime) and close_time:
            scope = "after_close" if _utc(publication) > _utc(datetime.fromisoformat(close_time)) else "by_close"
        elif publication:
            zone = ZoneInfo({"IN":"Asia/Kolkata","US":"America/New_York"}.get(pin.anchor.get("market"), "UTC"))
            day = publication.astimezone(zone).date() if isinstance(publication, datetime) else publication
            close_day = date.fromisoformat(pin.anchor["date"])
            scope = "later_date" if day > close_day else "earlier_date" if day < close_day else "same_date_order_unknown"
        else:
            scope = "publication_unknown"
        original["temporal_scope"] = scope
    if command.valuation_version_id is not None:
        version = resolve(select(DcfAssumptionSet).join(ValuationModel).where(DcfAssumptionSet.id == command.valuation_version_id,
            ValuationModel.company_id == note.company_id, ValuationModel.user_id == note.user_id))
        if not version:
            raise HTTPException(404, "Valuation version not found for this company and owner")
        baseline = dict(kind="dcf_assumption_set", id=version.id, model_id=version.valuation_model_id,
                        updated_at=version.updated_at, is_stale=version.is_stale)
    latest_change = db.scalar(select(ThesisChange.id).where(ThesisChange.thesis_note_id == note.id)
                              .order_by(ThesisChange.id.desc()).limit(1))
    return jsonable_encoder(dict(thesis_id=note.id, company_id=note.company_id, pin_id=pin.id, anchor=pin.anchor,
        observation_fingerprint=pin.fingerprint, pin_note=pin.text, last_change_id=latest_change,
        assumption={c.name:getattr(assumption,c.name) for c in ThesisAssumption.__table__.columns},
        original=original, source_state="selected" if original else "none", valuation_version=baseline,
        decision=command.decision, reason=command.reason))


def preview_decision(db, note_id, pin_id, owner, command):
    note, pin = _owned(db,note_id,pin_id,owner)
    context = _context(db,note,pin,command)
    return dict(context=context, context_hash=_hash(context))


def save_decision(db, note_id, pin_id, owner, command):
    note, _ = _owned(db,note_id,pin_id,owner)
    db.scalar(select(Company.id).where(Company.id == note.company_id).with_for_update())
    note, pin = _owned(db,note_id,pin_id,owner,lock=True)
    key = str(command.request_id)
    signature = _hash({"pin_id":pin_id, "command":command.model_dump(mode="json")})
    previous = db.scalar(select(ThesisChange).where(ThesisChange.thesis_note_id == note.id, ThesisChange.request_id == key))
    if previous:
        if (previous.price_review or {}).get("request_hash") != signature:
            raise HTTPException(409,"This submission already belongs to another decision.")
        return dict(change_id=previous.id,replayed=True)
    context = _context(db,note,pin,command,lock=True)
    if command.context_hash != _hash(context):
        raise HTTPException(409,"The reviewed evidence or thesis changed. Preview the current decision.")
    receipt = ThesisChange(thesis_note_id=note.id, request_id=key, drift_score=0,
        change_summary=f"{command.decision.replace('_',' ').capitalize()} · {command.reason}",
        price_review={"kind":"price_thesis_decision_v1", "request_hash":signature, "context_hash":command.context_hash, **context})
    db.add(receipt)
    db.commit()
    return dict(change_id=receipt.id,replayed=False)
