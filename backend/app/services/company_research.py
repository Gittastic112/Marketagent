"""Bounded, read-only company identity and stored annual business excerpts."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.raw_document import RawDocument
from app.models.sec_parsing import FilingSection


def company_research_profiles(db: Session, company_ids: list[int]) -> list[dict]:
    candidates = select(
        RawDocument.company_id, RawDocument.id.label("document_id"), RawDocument.title.label("document_title"),
        RawDocument.published_at, FilingSection.id.label("section_id"),
        func.substr(FilingSection.text_content, 1, 1400).label("excerpt"),
        func.row_number().over(partition_by=RawDocument.company_id,
            order_by=(RawDocument.published_at.desc().nullslast(), RawDocument.id.desc(), FilingSection.word_count.desc())).label("position"),
    ).join(FilingSection, FilingSection.raw_document_id == RawDocument.id).where(
        RawDocument.company_id.in_(company_ids), or_(RawDocument.document_type.in_(["10-K", "10-k", "annual_report"]),
            (RawDocument.document_type == "sec_filing_metadata") & (RawDocument.raw_payload_json["form_type"].as_string() == "10-K")),
        FilingSection.item_name == "Item 1", FilingSection.word_count >= 80,
    ).subquery()
    rows = db.execute(select(Company.id, Company.ticker, Company.name, Company.sector, Company.industry,
        Company.country, Company.currency, Company.primary_exchange, Company.exchange,
        candidates.c.document_id, candidates.c.document_title, candidates.c.published_at,
        candidates.c.section_id, candidates.c.excerpt,
    ).outerjoin(candidates, (candidates.c.company_id == Company.id) & (candidates.c.position == 1))
        .where(Company.id.in_(company_ids)).order_by(Company.ticker)).mappings()
    return [{**dict(row), "business_status": "stored_excerpt" if row["excerpt"] else "not_available",
             "basis": "Company catalog plus an excerpt from the latest stored annual Item 1, not a live company profile.",
             "source_href": f'/documents/{row["document_id"]}/sections' if row["document_id"] else None,
             "warnings": ["Parser-selected business excerpt, not independently reviewed. Open the full source for context."]
                 if row["excerpt"] else ["No usable annual business section stored. Import and parse a 10-K to add business context."]}
            for row in rows]
