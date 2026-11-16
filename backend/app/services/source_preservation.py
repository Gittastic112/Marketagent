"""Source evidence is immutable; dependent records cannot be silently cascaded away."""
from datetime import UTC, datetime

from sqlalchemy import literal, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import RawDocument


def changes_source_evidence(document: RawDocument, patch: dict) -> bool:
    def comparable(value):
        if isinstance(value, datetime):
            return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
        return value
    # The display title may be renamed; source identity, bytes and timing may not.
    return any(key != "title" and comparable(value) != comparable(getattr(document, key))
               for key, value in patch.items())


def has_document_dependents(db: Session, document_id: int) -> bool:
    # Include every persisted FK consumer, including assets, citations, extraction
    # and source revisions. Never load private bodies or reveal which owner depends on it.
    for dependent in Base.metadata.tables.values():
        for column in dependent.columns:
            if any(fk.target_fullname == "raw_documents.id" for fk in column.foreign_keys):
                if db.scalar(select(literal(True)).select_from(dependent)
                             .where(column == document_id).limit(1)):
                    return True
    return False
