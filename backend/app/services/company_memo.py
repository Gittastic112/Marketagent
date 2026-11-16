"""Deterministic export of shared company context and the caller's private thesis."""
import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, Event, ThesisNote


def company_memo(db: Session, company: Company, user_id: str) -> tuple[str, str]:
    notes = list(db.scalars(select(ThesisNote).where(
        ThesisNote.company_id == company.id, ThesisNote.user_id == user_id,
    ).order_by(ThesisNote.created_at.desc(), ThesisNote.id.desc())))
    events = list(db.scalars(select(Event).where(Event.company_id == company.id)
        .order_by(Event.event_time.desc().nulls_last(), Event.id.desc()).limit(10)))
    lines = [f"# Research Memo: {company.name} ({company.ticker})", "",
        f"Exported {datetime.now(UTC).isoformat()}. Stored research, not a recommendation.",
        f"**Sector:** {company.sector or 'Unknown'} | **Industry:** {company.industry or 'Unknown'}",
        f"**Exchange:** {company.exchange or 'Unknown'} | **Currency:** {company.currency or 'Unknown'}", "",
        "## Thesis Notes", "User Assumption: these are the signed-in user's notes.", ""]
    if not notes:
        lines.append("No thesis notes recorded.")
    for note in notes:
        lines.extend([f"### {note.title}",
            f"Note {note.id} | {note.status} | Updated {note.updated_at.isoformat()}",
            note.thesis_text, ""])
    lines.extend(["## Recent Events", "Up to ten stored events; review their evidence before relying on them.", ""])
    if not events:
        lines.append("No recent events recorded.")
    for event in events:
        basis = "Source Summary" if event.raw_document_id is not None else "User Assumption: no linked source document"
        lines.extend([f"### {event.event_time.date().isoformat() if event.event_time else 'Date unknown'}: {event.title}",
            basis,
            event.description or "No stored description.",
            f"[Event evidence](/events/{event.id}/evidence-resolution)", ""])
    ticker = re.sub(r"[^A-Za-z0-9._-]", "_", company.ticker)[:80] or str(company.id)
    return "\n".join(lines), f"memo_{ticker}.md"
