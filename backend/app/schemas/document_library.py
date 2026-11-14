from pydantic import BaseModel
from app.schemas.evidence import RawDocumentSummaryRead


class DocumentLibraryRead(BaseModel):
    items: list[RawDocumentSummaryRead]
    total: int
    offset: int
    limit: int
