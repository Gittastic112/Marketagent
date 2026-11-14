from datetime import UTC, date, datetime, timedelta

from sqlalchemy import event

from app.models import Alert, Company, Portfolio, PortfolioHolding, User
from app.models.dcf import ValuationSetupDraft
from app.models import Event, ProcessingRun, RawDocument, Source
from app.models.thesis_note import ThesisNote, ThesisAssumption, EventThesisImpact


def setup(db):
    first = Company(ticker="QONE", name="Mock Data held")
    second = Company(ticker="QTWO", name="Mock Data unheld")
    db.add_all([first, second, User(id="queue-other", email="queue-other@example.invalid")]); db.flush()
    own = Portfolio(name="Mock Data selected holdings", base_currency="USD")
    other = Portfolio(name="Mock Data private portfolio", user_id="queue-other", base_currency="USD")
    db.add_all([own, other]); db.flush()
    db.add(PortfolioHolding(portfolio_id=own.id, company_id=first.id, ticker=first.ticker,
        quantity=2, average_cost=0, currency="USD", as_of_date=date.today()))
    for company in (first, second):
        db.add(Alert(company_id=company.id, alert_type="mock", title="Mock Data owned alert", review_status="unreviewed"))
    db.add(Alert(company_id=first.id, user_id="queue-other", alert_type="mock", title="PRIVATE HIDDEN", review_status="unreviewed"))
    db.add(ValuationSetupDraft(company_id=first.id, user_id="queue-other", status="draft"))
    db.commit()
    return own, other, first


def test_queue_owner_scope_holdings_filter_counts_and_read_only(client, db):
    own, other, first = setup(db)
    before = db.query(Alert).count()
    response = client.get(f"/review-queue?portfolio_id={own.id}")
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["total"] == data["returned"] == data["counts"]["needs_review"] == 1
    assert data["items"][0]["company_id"] == first.id
    assert "PRIVATE HIDDEN" not in response.text
    assert client.get(f"/review-queue?portfolio_id={other.id}").status_code == 404
    assert db.query(Alert).count() == before
    assert client.get("/review-queue?state=resolved").status_code == 422
    assert client.get("/review-queue?limit=101").status_code == 422


def test_queue_has_stable_identity_bounded_results_and_query_count(client, db):
    setup(db)
    now = datetime.now(UTC)
    for i in range(130):
        db.add(Alert(alert_type="mock", title=f"Mock Data item {i}", review_status="unreviewed",
            created_at=now - timedelta(minutes=i)))
    db.commit()
    statements = []
    def capture(conn, cursor, statement, params, context, executemany):
        statements.append(statement)
    event.listen(db.get_bind(), "before_cursor_execute", capture)
    try:
        response = client.get("/review-queue?limit=5")
    finally:
        event.remove(db.get_bind(), "before_cursor_execute", capture)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["total"] == 132 and data["returned"] == 5 and data["truncated"]
    assert len(statements) <= 14
    assert all(s.lstrip().upper().startswith("SELECT") for s in statements)
    again = client.get("/review-queue?limit=5").json()["data"]
    assert [i["identity"] for i in data["items"]] == [i["identity"] for i in again["items"]]
    dates = [datetime.fromisoformat(i["relevant_at"].replace("Z", "+00:00")) for i in data["items"]]
    assert dates == sorted(dates, reverse=True)


def test_queue_keeps_thesis_permissions_and_public_failure_scope(client, db):
    _, _, company = setup(db)
    event = Event(company_id=company.id, title="Mock Data public event", event_type="filing", information_speed="slow")
    db.add(event); db.flush()
    for owner in ("admin_user_id_fallback", "queue-other"):
        note = ThesisNote(user_id=owner, company_id=company.id, title=f"Mock Data {owner}", thesis_text="Mock Data")
        db.add(note); db.flush()
        assumption = ThesisAssumption(thesis_note_id=note.id, description="Mock Data assumption")
        db.add(assumption); db.flush()
        db.add(EventThesisImpact(event_id=event.id, thesis_assumption_id=assumption.id,
            impact_classification="Weakens", rationale="Mock Data interpretation", review_status="unreviewed"))
    db.add_all([ProcessingRun(run_type="mock_public", source_type="sec", company_id=company.id,
        started_at=datetime.now(UTC), status="partial", error_details_json={"private": "MUST NOT LEAK"}),
        ProcessingRun(run_type="mock_private_ai", source_type="ai", started_at=datetime.now(UTC), status="failed")])
    db.commit()
    response = client.get("/review-queue")
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    thesis = [row for row in data["items"] if row["domain"] == "thesis"]
    assert len(thesis) == 1 and "note_id=" in thesis[0]["href"]
    assert "queue-other" not in response.text and "MUST NOT LEAK" not in response.text
    assert data["counts"]["waiting_for_source"] == 1
