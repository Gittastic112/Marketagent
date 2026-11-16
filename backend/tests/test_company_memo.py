"""Mock Data exports must use current fields and only the caller's private notes."""
from datetime import UTC, datetime

from app.models import Company, Event, ThesisNote, User
from conftest import TEST_USER_ID


def test_memo_uses_owned_notes_current_events_and_download_contract(client, db):
    company = Company(ticker="MEMO", name="Mock Data memo company")
    db.add_all([company, User(id="memo-other", email="other@example.invalid", name="Other")])
    db.flush()
    db.add_all([
        ThesisNote(company_id=company.id, user_id=TEST_USER_ID, title="Owned thesis",
                   thesis_text="Mock Data owned rationale", status="active"),
        ThesisNote(company_id=company.id, user_id="memo-other", title="Foreign private title",
                   thesis_text="Foreign private rationale", status="active"),
        Event(company_id=company.id, title="Mock Data filed event", description="Source summary text",
              event_type="filing", information_speed="slow", event_time=datetime(2026, 11, 1, tzinfo=UTC)),
    ])
    db.commit()
    response = client.get(f"/companies/{company.id}/memo")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert response.headers["content-disposition"] == 'attachment; filename="memo_MEMO.md"'
    assert "Owned thesis" in response.text and "Mock Data owned rationale" in response.text
    assert "Foreign private" not in response.text
    assert "2026-11-01" in response.text and "Mock Data filed event" in response.text
    assert "Source summary text" in response.text
    assert "User Assumption: no linked source document" in response.text
    assert "Source Summary" not in response.text


def test_empty_memo_and_unknown_company(client, db):
    company = Company(ticker="EMPTYMEMO", name="Mock Data empty company")
    db.add(company)
    db.commit()
    response = client.get(f"/companies/{company.id}/memo")
    assert response.status_code == 200
    assert "No thesis notes recorded" in response.text
    assert "No recent events recorded" in response.text
    assert client.get("/companies/999999/memo").status_code == 404
