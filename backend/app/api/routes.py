from typing import TypeVar

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas import (
    AlertCreate,
    AlertRead,
    AlertUpdate,
    CompanyCreate,
    CompanyRead,
    CompanyUpdate,
    DailyBriefRead,
    EventCreate,
    EventExtractionRead,
    EventRead,
    EventUpdate,
    RawDocumentCreate,
    RawDocumentRead,
    RawDocumentUpdate,
    RssIngestionCreate,
    RssIngestionRead,
    SecFilingIngestionCreate,
    SecFilingIngestionRead,
    SourceCreate,
    SourceRead,
    SourceUpdate,
    ThesisNoteCreate,
    ThesisNoteRead,
    ThesisNoteUpdate,
)
from app.db.session import get_db
from app.models import Alert, Company, DailyBrief, Event, RawDocument, Source, ThesisNote
from app.services.daily_brief import generate_daily_brief, save_daily_brief
from app.services.event_extraction import extract_events_from_raw_documents
from app.services.rss_ingestion import ingest_rss_xml
from app.services.sec_ingestion import SecFilingMetadata, ingest_sec_filing_metadata


router = APIRouter()
ModelT = TypeVar("ModelT")


def get_or_404(db: Session, model: type[ModelT], item_id: int) -> ModelT:
    item = db.get(model, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return item


def create_record(db: Session, model: type[ModelT], payload: object) -> ModelT:
    record = model(**payload.model_dump())
    db.add(record)
    commit_or_conflict(db)
    db.refresh(record)
    return record


def update_record(db: Session, record: ModelT, payload: object) -> ModelT:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    commit_or_conflict(db)
    db.refresh(record)
    return record


def delete_record(db: Session, record: object) -> None:
    db.delete(record)
    commit_or_conflict(db)


def commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Record already exists") from exc


def require_reference(db: Session, model: type[ModelT], item_id: int | None, name: str) -> None:
    if item_id is not None and db.get(model, item_id) is None:
        raise HTTPException(status_code=404, detail=f"{name} not found")


def validate_raw_document_refs(db: Session, payload: RawDocumentCreate | RawDocumentUpdate) -> None:
    require_reference(db, Company, payload.company_id, "Company")
    require_reference(db, Source, payload.source_id, "Source")


def validate_event_refs(db: Session, payload: EventCreate | EventUpdate) -> None:
    require_reference(db, Company, payload.company_id, "Company")
    require_reference(db, RawDocument, payload.raw_document_id, "Raw document")


def validate_alert_refs(db: Session, payload: AlertCreate | AlertUpdate) -> None:
    require_reference(db, Event, payload.event_id, "Event")
    require_reference(db, Company, payload.company_id, "Company")


def validate_thesis_note_refs(db: Session, payload: ThesisNoteCreate | ThesisNoteUpdate) -> None:
    require_reference(db, Company, payload.company_id, "Company")


@router.post("/companies", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)) -> Company:
    return create_record(db, Company, payload)


@router.get("/companies", response_model=list[CompanyRead])
def list_companies(db: Session = Depends(get_db)) -> list[Company]:
    return list(db.scalars(select(Company).order_by(Company.id)))


@router.get("/companies/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: Session = Depends(get_db)) -> Company:
    return get_or_404(db, Company, company_id)


@router.patch("/companies/{company_id}", response_model=CompanyRead)
def update_company(company_id: int, payload: CompanyUpdate, db: Session = Depends(get_db)) -> Company:
    return update_record(db, get_or_404(db, Company, company_id), payload)


@router.delete("/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, Company, company_id))


@router.post("/sources", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)) -> Source:
    return create_record(db, Source, payload)


@router.get("/sources", response_model=list[SourceRead])
def list_sources(db: Session = Depends(get_db)) -> list[Source]:
    return list(db.scalars(select(Source).order_by(Source.id)))


@router.get("/sources/{source_id}", response_model=SourceRead)
def get_source(source_id: int, db: Session = Depends(get_db)) -> Source:
    return get_or_404(db, Source, source_id)


@router.patch("/sources/{source_id}", response_model=SourceRead)
def update_source(source_id: int, payload: SourceUpdate, db: Session = Depends(get_db)) -> Source:
    return update_record(db, get_or_404(db, Source, source_id), payload)


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, Source, source_id))


@router.post("/raw-documents", response_model=RawDocumentRead, status_code=status.HTTP_201_CREATED)
def create_raw_document(payload: RawDocumentCreate, db: Session = Depends(get_db)) -> RawDocument:
    validate_raw_document_refs(db, payload)
    return create_record(db, RawDocument, payload)


@router.get("/raw-documents", response_model=list[RawDocumentRead])
def list_raw_documents(db: Session = Depends(get_db)) -> list[RawDocument]:
    return list(db.scalars(select(RawDocument).order_by(RawDocument.id)))


@router.get("/raw-documents/{raw_document_id}", response_model=RawDocumentRead)
def get_raw_document(raw_document_id: int, db: Session = Depends(get_db)) -> RawDocument:
    return get_or_404(db, RawDocument, raw_document_id)


@router.patch("/raw-documents/{raw_document_id}", response_model=RawDocumentRead)
def update_raw_document(
    raw_document_id: int,
    payload: RawDocumentUpdate,
    db: Session = Depends(get_db),
) -> RawDocument:
    validate_raw_document_refs(db, payload)
    return update_record(db, get_or_404(db, RawDocument, raw_document_id), payload)


@router.delete("/raw-documents/{raw_document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_raw_document(raw_document_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, RawDocument, raw_document_id))


@router.post("/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: Session = Depends(get_db)) -> Event:
    validate_event_refs(db, payload)
    return create_record(db, Event, payload)


@router.get("/events", response_model=list[EventRead])
def list_events(db: Session = Depends(get_db)) -> list[Event]:
    return list(db.scalars(select(Event).order_by(Event.id)))


@router.get("/events/{event_id}", response_model=EventRead)
def get_event(event_id: int, db: Session = Depends(get_db)) -> Event:
    return get_or_404(db, Event, event_id)


@router.patch("/events/{event_id}", response_model=EventRead)
def update_event(event_id: int, payload: EventUpdate, db: Session = Depends(get_db)) -> Event:
    validate_event_refs(db, payload)
    return update_record(db, get_or_404(db, Event, event_id), payload)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, Event, event_id))


@router.post("/alerts", response_model=AlertRead, status_code=status.HTTP_201_CREATED)
def create_alert(payload: AlertCreate, db: Session = Depends(get_db)) -> Alert:
    validate_alert_refs(db, payload)
    return create_record(db, Alert, payload)


@router.get("/alerts", response_model=list[AlertRead])
def list_alerts(db: Session = Depends(get_db)) -> list[Alert]:
    return list(db.scalars(select(Alert).order_by(Alert.id)))


@router.get("/alerts/{alert_id}", response_model=AlertRead)
def get_alert(alert_id: int, db: Session = Depends(get_db)) -> Alert:
    return get_or_404(db, Alert, alert_id)


@router.patch("/alerts/{alert_id}", response_model=AlertRead)
def update_alert(alert_id: int, payload: AlertUpdate, db: Session = Depends(get_db)) -> Alert:
    validate_alert_refs(db, payload)
    return update_record(db, get_or_404(db, Alert, alert_id), payload)


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(alert_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, Alert, alert_id))


@router.post("/thesis-notes", response_model=ThesisNoteRead, status_code=status.HTTP_201_CREATED)
def create_thesis_note(payload: ThesisNoteCreate, db: Session = Depends(get_db)) -> ThesisNote:
    validate_thesis_note_refs(db, payload)
    return create_record(db, ThesisNote, payload)


@router.get("/thesis-notes", response_model=list[ThesisNoteRead])
def list_thesis_notes(db: Session = Depends(get_db)) -> list[ThesisNote]:
    return list(db.scalars(select(ThesisNote).order_by(ThesisNote.id)))


@router.get("/thesis-notes/{thesis_note_id}", response_model=ThesisNoteRead)
def get_thesis_note(thesis_note_id: int, db: Session = Depends(get_db)) -> ThesisNote:
    return get_or_404(db, ThesisNote, thesis_note_id)


@router.patch("/thesis-notes/{thesis_note_id}", response_model=ThesisNoteRead)
def update_thesis_note(
    thesis_note_id: int,
    payload: ThesisNoteUpdate,
    db: Session = Depends(get_db),
) -> ThesisNote:
    validate_thesis_note_refs(db, payload)
    return update_record(db, get_or_404(db, ThesisNote, thesis_note_id), payload)


@router.delete("/thesis-notes/{thesis_note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thesis_note(thesis_note_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, ThesisNote, thesis_note_id))


@router.get("/daily-brief")
def get_daily_brief(db: Session = Depends(get_db)) -> dict:
    return generate_daily_brief(db)


@router.post("/daily-brief", response_model=DailyBriefRead, status_code=status.HTTP_201_CREATED)
def create_daily_brief(db: Session = Depends(get_db)) -> DailyBrief:
    return save_daily_brief(db)


@router.get("/daily-brief-history", response_model=list[DailyBriefRead])
def list_daily_brief_history(db: Session = Depends(get_db)) -> list[DailyBrief]:
    return list(db.scalars(select(DailyBrief).order_by(DailyBrief.created_at.desc(), DailyBrief.id.desc()).limit(30)))


@router.post("/ingest/rss", response_model=RssIngestionRead, status_code=status.HTTP_201_CREATED)
def ingest_rss(payload: RssIngestionCreate, db: Session = Depends(get_db)) -> dict[str, int]:
    require_reference(db, Source, payload.source_id, "Source")
    require_reference(db, Company, payload.company_id, "Company")
    result = ingest_rss_xml(db, source_id=payload.source_id, rss_xml=payload.rss_xml, company_id=payload.company_id)
    return {"created": result.created, "skipped_duplicates": result.skipped_duplicates}


@router.post("/ingest/sec-filings", response_model=SecFilingIngestionRead, status_code=status.HTTP_201_CREATED)
def ingest_sec_filings(payload: SecFilingIngestionCreate, db: Session = Depends(get_db)) -> dict[str, int]:
    require_reference(db, Source, payload.source_id, "Source")
    require_reference(db, Company, payload.company_id, "Company")
    filings = [
        SecFilingMetadata(
            accession_number=filing.accession_number,
            form_type=filing.form_type,
            filing_date=filing.filing_date,
            report_date=filing.report_date,
            primary_document=filing.primary_document,
            filing_url=filing.filing_url,
        )
        for filing in payload.filings
    ]
    result = ingest_sec_filing_metadata(
        db,
        source_id=payload.source_id,
        company_id=payload.company_id,
        filings=filings,
    )
    return {"created": result.created, "skipped_duplicates": result.skipped_duplicates}


@router.post("/extract/events", response_model=EventExtractionRead, status_code=status.HTTP_201_CREATED)
def extract_events(db: Session = Depends(get_db)) -> dict[str, int]:
    result = extract_events_from_raw_documents(db)
    return {"created": result.created, "skipped_existing": result.skipped_existing}
