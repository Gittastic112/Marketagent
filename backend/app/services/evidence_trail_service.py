from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import (
    EvidenceAlertSummaryRead,
    EvidenceCompanySummaryRead,
    EvidenceDocumentSummaryRead,
    EvidenceEventSummaryRead,
    EvidenceLocatorRead,
    EvidenceSourceSummaryRead,
    EvidenceThesisImpactSummaryRead,
    EvidenceTrailRead,
    EvidenceValuationImpactSummaryRead,
)
from app.models.alert import Alert
from app.models.company import Company
from app.models.dcf import ValuationAssumptionChangeLog, ValuationModel
from app.models.event import Event
from app.models.event_evidence_reference import EventEvidenceReference
from app.models.raw_document import RawDocument
from app.models.source import Source
from app.models.thesis_note import EventThesisImpact, ThesisAssumption, ThesisNote
from app.services.pdf_page_rendering import validate_pdf_region_against_asset


MAX_EXCERPT_LENGTH = 1_200
MAX_SUMMARY_LENGTH = 2_000
MAX_DESCRIPTION_LENGTH = 4_000


def _bounded_text(value: str | None, limit: int) -> str | None:
    if not value:
        return None
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 1].rstrip()}..."


def _claim_context(alert: Alert | None, event: Event | None) -> tuple[str | None, str]:
    candidates = (
        (alert.evidence if alert else None, "alert.evidence"),
        (event.description if event else None, "event.description"),
        (alert.summary if alert else None, "alert.summary"),
    )
    for value, origin in candidates:
        excerpt = _bounded_text(value, MAX_EXCERPT_LENGTH)
        if excerpt:
            return excerpt, origin
    return None, "none"


def _claim_type(alert: Alert | None, event: Event | None, document: RawDocument | None) -> str:
    if document:
        return "Source Summary"
    if (alert and alert.alert_type.startswith("manual")) or (event and event.event_type.startswith("manual")):
        return "User Assumption"
    return "Estimate"


def _confidence(alert: Alert | None, event: Event | None) -> str:
    if alert and alert.confidence_bucket in {"high", "medium", "low"}:
        return alert.confidence_bucket
    if not event or event.credibility_score is None:
        return "unknown"
    if event.credibility_score >= 80:
        return "high"
    if event.credibility_score >= 50:
        return "medium"
    return "low"


def _preferred_reference(db: Session, event_id: int | None) -> EventEvidenceReference | None:
    if event_id is None:
        return None
    references = list(
        db.scalars(
            select(EventEvidenceReference)
            .where(EventEvidenceReference.event_id == event_id)
            .order_by(EventEvidenceReference.id.desc())
        )
    )
    priority = {"text_span": 4, "pdf_region": 3, "xbrl_fact": 3, "section": 2}
    return max(references, key=lambda item: (priority.get(item.locator_type, 0), item.id), default=None)


def _thesis_impacts(db: Session, event_id: int, user_id: str) -> list[EvidenceThesisImpactSummaryRead]:
    rows = db.execute(
        select(EventThesisImpact, ThesisAssumption)
        .join(ThesisAssumption, EventThesisImpact.thesis_assumption_id == ThesisAssumption.id)
        .join(ThesisNote, ThesisAssumption.thesis_note_id == ThesisNote.id)
        .where(
            EventThesisImpact.event_id == event_id,
            ThesisNote.user_id == user_id,
        )
        .order_by(EventThesisImpact.id)
    ).all()
    return [
        EvidenceThesisImpactSummaryRead(
            id=impact.id,
            thesis_assumption_id=assumption.id,
            assumption_description=_bounded_text(assumption.description, MAX_SUMMARY_LENGTH) or "",
            assumption_status=assumption.status,
            impact_classification=impact.impact_classification,
            rationale=_bounded_text(impact.rationale, MAX_SUMMARY_LENGTH) or "",
            created_at=impact.created_at,
        )
        for impact, assumption in rows
    ]


def _valuation_impacts(
    db: Session,
    event_id: int,
    user_id: str,
) -> list[EvidenceValuationImpactSummaryRead]:
    rows = db.scalars(
        select(ValuationAssumptionChangeLog)
        .join(
            ValuationModel,
            ValuationAssumptionChangeLog.valuation_model_id == ValuationModel.id,
        )
        .where(
            ValuationAssumptionChangeLog.event_id == event_id,
            ValuationModel.user_id == user_id,
        )
        .order_by(ValuationAssumptionChangeLog.id)
    ).all()
    return [
        EvidenceValuationImpactSummaryRead(
            id=impact.id,
            valuation_model_id=impact.valuation_model_id,
            assumption_set_id=impact.assumption_set_id,
            parameter_name=impact.parameter_name,
            old_value=impact.old_value,
            new_value=impact.new_value,
            rationale=_bounded_text(impact.rationale, MAX_SUMMARY_LENGTH),
            is_applied=impact.is_applied,
            created_at=impact.created_at,
        )
        for impact in rows
    ]


def build_evidence_trail(
    db: Session,
    *,
    user_id: str,
    event: Event | None,
    alert: Alert | None = None,
) -> EvidenceTrailRead:
    reference = _preferred_reference(db, event.id if event else None)
    document_id = reference.raw_document_id if reference else event.raw_document_id if event else None
    document = db.get(RawDocument, document_id) if document_id else None
    source = db.get(Source, document.source_id) if document else None
    company_id = event.company_id if event and event.company_id else alert.company_id if alert else None
    company = db.get(Company, company_id) if company_id else None
    claim_excerpt, excerpt_origin = _claim_context(alert, event)
    if reference and reference.quote:
        claim_excerpt = _bounded_text(reference.quote, MAX_EXCERPT_LENGTH)
        excerpt_origin = "event.evidence_reference"
    warnings: list[str] = []
    pdf_region_exact = False
    if reference and reference.locator_type == "pdf_region" and document and document.asset:
        try:
            validate_pdf_region_against_asset(
                reference.bounding_box_json,
                source_page=reference.source_page,
                content=document.asset.content,
            )
            pdf_region_exact = True
        except (IndexError, ValueError):
            warnings.append(
                "The PDF-region locator is not reproducible and is shown as page-level evidence."
            )
    reference_is_complete = bool(
        reference and (reference.locator_type != "pdf_region" or pdf_region_exact)
    )

    if event is None:
        evidence_status = "missing"
        warnings.append("This alert is not linked to an event.")
    elif document and source and reference_is_complete:
        evidence_status = "complete"
    elif document or claim_excerpt:
        evidence_status = "partial"
        if document and source and reference is None:
            warnings.append("The source chain is document-level and has no exact event evidence reference.")
        else:
            warnings.append("The event does not have a complete document-to-source chain.")
    else:
        evidence_status = "missing"
        warnings.append("No source document or claim context is stored for this event.")

    if document and document.published_at is None:
        warnings.append("The source document has no publication timestamp.")
    if reference and reference.confidence_label != "high":
        warnings.append(f"The selected evidence locator has {reference.confidence_label} confidence.")
    if source and not source.active:
        warnings.append("The linked source is currently inactive.")

    if reference and reference.start_char is not None and reference.end_char is not None:
        precision = "span"
    elif reference and reference.locator_type == "pdf_region" and pdf_region_exact:
        precision = "region"
    elif reference and reference.source_page is not None:
        precision = "page"
    elif reference and reference.source_section:
        precision = "section"
    else:
        precision = "document" if document else "none"

    locator = EvidenceLocatorRead(
        precision=precision,
        label=(
            f"Page {reference.source_page} region"
            if reference and reference.source_page and pdf_region_exact
            else f"Page {reference.source_page}"
            if reference and reference.source_page
            else reference.source_section
            if reference and reference.source_section
            else "Exact source passage"
            if precision == "span"
            else "Open source document"
            if document
            else "No source locator"
        ),
        reference_id=reference.id if reference else None,
        locator_type=reference.locator_type if reference else None,
        source_page=reference.source_page if reference else None,
        source_section=reference.source_section if reference else None,
        start_char=reference.start_char if reference else None,
        end_char=reference.end_char if reference else None,
        quote=_bounded_text(reference.quote, MAX_EXCERPT_LENGTH) if reference else None,
        confidence_label=reference.confidence_label if reference else None,
        internal_href=(
            f"/documents/{document.id}/event-evidence?evidence_reference={reference.id}"
            if document and reference and pdf_region_exact
            else f"/documents/{document.id}/sections?evidence_reference={reference.id}"
            if document and reference
            else f"/documents/{document.id}/sections"
            if document
            else None
        ),
        source_href=document.url if document else None,
        asset_href=(
            f"/api/backend/api/raw-documents/{document.id}/asset/content"
            + (f"#page={reference.source_page}" if reference and reference.source_page else "")
            if document and document.asset
            else None
        ),
    )

    event_summary = None
    thesis_impacts: list[EvidenceThesisImpactSummaryRead] = []
    valuation_impacts: list[EvidenceValuationImpactSummaryRead] = []
    if event:
        event_summary = EvidenceEventSummaryRead(
            id=event.id,
            company_id=event.company_id,
            raw_document_id=event.raw_document_id,
            event_type=event.event_type,
            information_speed=event.information_speed,
            title=event.title,
            description=_bounded_text(event.description, MAX_DESCRIPTION_LENGTH),
            event_time=event.event_time,
            credibility_score=event.credibility_score,
            priority_score=event.priority_score,
            created_at=event.created_at,
        )
        thesis_impacts = _thesis_impacts(db, event.id, user_id)
        valuation_impacts = _valuation_impacts(db, event.id, user_id)

    return EvidenceTrailRead(
        entry_point="alert" if alert else "event",
        claim_type=_claim_type(alert, event, document),
        evidence_status=evidence_status,
        confidence=_confidence(alert, event),
        source_timestamp=(
            document.published_at
            if document and document.published_at
            else event.event_time
            if event and event.event_time
            else event.created_at
            if event
            else alert.created_at
            if alert
            else None
        ),
        claim_excerpt=claim_excerpt,
        excerpt_origin=excerpt_origin,
        alert=(
            EvidenceAlertSummaryRead(
                id=alert.id,
                event_id=alert.event_id,
                company_id=alert.company_id,
                alert_type=alert.alert_type,
                severity=alert.severity,
                title=alert.title,
                summary=_bounded_text(alert.summary, MAX_SUMMARY_LENGTH),
                why_it_matters=_bounded_text(alert.why_it_matters, MAX_SUMMARY_LENGTH),
                confidence_bucket=alert.confidence_bucket,
                created_at=alert.created_at,
            )
            if alert
            else None
        ),
        event=event_summary,
        company=(
            EvidenceCompanySummaryRead(
                id=company.id,
                ticker=company.ticker,
                name=company.name,
                market=company.market,
                primary_exchange=company.primary_exchange,
            )
            if company
            else None
        ),
        source=(
            EvidenceSourceSummaryRead(
                id=source.id,
                name=source.name,
                source_type=source.source_type,
                reliability_score=source.reliability_score,
                active=source.active,
            )
            if source
            else None
        ),
        document=(
            EvidenceDocumentSummaryRead(
                id=document.id,
                company_id=document.company_id,
                source_id=document.source_id,
                document_type=document.document_type,
                title=document.title,
                url=document.url,
                published_at=document.published_at,
                ingested_at=document.ingested_at,
                content_hash=document.content_hash,
                has_raw_text=bool(document.raw_text),
                has_asset=bool(document.asset),
                asset_page_count=document.asset.page_count if document.asset else None,
            )
            if document
            else None
        ),
        locator=locator,
        thesis_impacts=thesis_impacts,
        valuation_impacts=valuation_impacts,
        warnings=warnings,
    )
