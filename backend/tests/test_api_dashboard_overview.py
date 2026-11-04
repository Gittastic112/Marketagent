from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import event as sqlalchemy_event
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.api.routers.dashboard import DASHBOARD_QUERY_BUDGET, DASHBOARD_RESPONSE_BUDGET_MS
from app.main import app
from app.models import Event, PortfolioSnapshot, ProcessingRun, RawDocument, Source, ThesisAssumption, ThesisNote
from helpers import response_data


def _use_user(user_id: str) -> None:
    app.dependency_overrides[get_current_user] = lambda: {
        "id": user_id,
        "email": f"{user_id}@example.com",
        "name": user_id,
    }


def test_dashboard_overview_consolidates_data_and_enforces_ownership(
    client: TestClient,
    db_session: Session,
) -> None:
    company = response_data(client.post("/companies", json={"ticker": "DASH", "name": "Dashboard Co"}))
    response_data(
        client.post(
            "/alerts",
            json={"company_id": company["id"], "alert_type": "manual", "title": "Owner alert"},
        )
    )
    response_data(
        client.post(
            "/thesis-notes",
            json={"company_id": company["id"], "title": "Owner thesis", "thesis_text": "Evidence-backed thesis."},
        )
    )
    response_data(client.post("/portfolios", json={"name": "Owner portfolio", "base_currency": "USD"}))

    _use_user("other-dashboard-user")
    other_alert = response_data(
        client.post(
            "/alerts",
            json={"company_id": company["id"], "alert_type": "manual", "title": "Other alert"},
        )
    )
    response_data(
        client.post(
            "/thesis-notes",
            json={"company_id": company["id"], "title": "Other thesis", "thesis_text": "Other thesis."},
        )
    )

    statements: list[str] = []

    def record_statement(*args) -> None:
        statements.append(args[2])

    engine = db_session.get_bind()
    sqlalchemy_event.listen(engine, "before_cursor_execute", record_statement)
    try:
        response = client.get("/dashboard/overview")
    finally:
        sqlalchemy_event.remove(engine, "before_cursor_execute", record_statement)
    overview = response_data(response)

    assert [item["id"] for item in overview["alerts"]] == [other_alert["id"]]
    assert [item["title"] for item in overview["thesis_notes"]] == ["Other thesis"]
    assert overview["default_portfolio"] is None
    assert overview["companies"][0]["ticker"] == "DASH"
    assert overview["daily_brief"]["summary"] == (
        "0 events in the stored-event preview; 0 unresolved contradiction alerts; "
        "0 affected held companies."
    )
    assert len(statements) <= DASHBOARD_QUERY_BUDGET
    assert response.json()["meta"]["processing_time_ms"] <= DASHBOARD_RESPONSE_BUDGET_MS


def test_dashboard_overview_uses_latest_stored_snapshot_without_live_recalculation(
    client: TestClient,
    db_session: Session,
) -> None:
    company = response_data(client.post("/companies", json={"ticker": "NOPRICE", "name": "No Price Co"}))
    portfolio = response_data(client.post("/portfolios", json={"name": "Partial portfolio", "base_currency": "USD"}))
    response_data(client.post("/portfolio-holdings", json={
        "portfolio_id": portfolio["id"],
        "company_id": company["id"],
        "ticker": "NOPRICE",
        "quantity": 2,
        "average_cost": 10,
        "currency": "USD",
        "as_of_date": "2026-07-31",
    }))
    db_session.add(PortfolioSnapshot(
        portfolio_id=portfolio["id"],
        snapshot_date=date(2026, 7, 31),
        total_market_value=None,
        total_cost_basis=20,
        total_cash=0,
        total_portfolio_value=None,
        base_currency="USD",
        calculation_status="partial",
        holdings_count=1,
        priced_holdings_count=0,
        missing_price_tickers_json=["NOPRICE"],
        missing_fx_pairs_json=[],
        payload_json={},
    ))
    db_session.commit()

    response = client.get("/dashboard/overview")
    overview = response_data(response)

    assert overview["portfolio_analytics"] is None
    assert overview["default_portfolio_snapshot"]["calculation_status"] == "partial"
    assert overview["default_portfolio_snapshot"]["missing_price_tickers_json"] == ["NOPRICE"]
    assert (
        "The latest portfolio snapshot is partial; missing prices or FX remain unavailable."
        in response.json()["meta"]["warnings"]
    )


def test_dashboard_overview_never_runs_ai_or_mutates_briefing_state(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    company = response_data(client.post("/companies", json={"ticker": "FAST", "name": "Fast Dashboard"}))
    response_data(client.post("/events", json={
        "company_id": company["id"],
        "event_type": "manual",
        "information_speed": "fast",
        "title": "Material dashboard event",
        "description": "Stored evidence only.",
        "priority_score": 90,
    }))
    thesis = ThesisNote(
        user_id="admin_user_id_fallback",
        company_id=company["id"],
        title="Dashboard thesis",
        thesis_text="Existing thesis",
        status="active",
    )
    db_session.add(thesis)
    db_session.flush()
    db_session.add(ThesisAssumption(thesis_note_id=thesis.id, description="Margins remain durable"))
    db_session.commit()

    ai_calls: list[str] = []
    monkeypatch.setattr(
        "app.services.morning_briefing_engine.map_event_to_dcf_variables",
        lambda **kwargs: ai_calls.append("valuation"),
    )
    monkeypatch.setattr(
        "app.services.morning_briefing_engine.detect_thesis_contradiction",
        lambda **kwargs: ai_calls.append("contradiction"),
    )
    response = client.get("/dashboard/overview")

    assert response.status_code == 200, response.text
    assert ai_calls == []
    assert len(db_session.new) == 0


def test_dashboard_latency_budget_is_observability_not_a_partial_data_warning(
    client: TestClient,
    monkeypatch,
    caplog,
) -> None:
    timestamps = iter([0.0, 1.25])
    monkeypatch.setattr(
        "app.api.routers.dashboard.perf_counter",
        lambda: next(timestamps),
    )

    response = client.get("/dashboard/overview")

    assert response.status_code == 200, response.text
    assert response.json()["meta"]["processing_time_ms"] == 1250
    assert not any("local budget" in warning for warning in response.json()["meta"]["warnings"])
    assert "Dashboard overview took 1250 ms" in caplog.text


def test_dashboard_fresh_session_keeps_source_provenance_and_bounded_coverage(client, db_session, monkeypatch):
    now = datetime.now(UTC)
    source = Source(name="Recorded official source", source_type="filing")
    document = RawDocument(source=source, document_type="filing", title="Recorded filing",
        url="https://example.invalid/retained", published_at=now - timedelta(days=1),
        raw_text="Original body must not load into the dashboard", content_hash="dashboard-source-parity")
    linked = Event(raw_document=document, event_type="filing", information_speed="slow",
        title="Linked source event", priority_score=100, created_at=now - timedelta(minutes=1))
    db_session.add(linked)
    for index in range(12):
        db_session.add(Event(event_type="manual", information_speed="slow", title=f"Manual {index}",
            priority_score=90, created_at=now - timedelta(minutes=2, seconds=index)))
    # The dashboard's recent-run preview can exclude old failures even below its ten-failure cap.
    db_session.add(ProcessingRun(run_type="old_failure", status="failed", error_count=1,
        started_at=now - timedelta(days=1), created_at=now - timedelta(days=1)))
    for index in range(21):
        db_session.add(ProcessingRun(run_type="recent_success", status="success", error_count=0,
            started_at=now - timedelta(minutes=3, seconds=index), created_at=now - timedelta(minutes=3, seconds=index)))
    db_session.commit()
    linked_id, document_id = linked.id, document.id
    db_session.expunge_all()

    def forbidden(**_kwargs):
        raise AssertionError("Dashboard must not invoke AI")
    monkeypatch.setattr("app.services.morning_briefing_engine.map_event_to_dcf_variables", forbidden)
    monkeypatch.setattr("app.services.morning_briefing_engine.detect_thesis_contradiction", forbidden)
    statements = []
    def record(_connection, _cursor, statement, *_args):
        statements.append(statement)
    engine = db_session.get_bind()
    original_dependency = app.dependency_overrides[get_db]
    def fresh_session():
        with Session(engine) as session:
            yield session
            assert not session.new and not session.dirty and not session.deleted
    app.dependency_overrides[get_db] = fresh_session
    sqlalchemy_event.listen(engine, "before_cursor_execute", record)
    try:
        payload = response_data(client.get("/dashboard/overview"))["daily_brief"]
    finally:
        app.dependency_overrides[get_db] = original_dependency
        sqlalchemy_event.remove(engine, "before_cursor_execute", record)

    event = next(item for item in payload["high_materiality_events"] if item["event_id"] == linked_id)
    assert event["evidence_status"] == "source_linked"
    assert event["claim_type"] == "Source Summary"
    assert event["source_name"] == "Recorded official source"
    assert event["raw_document_id"] == document_id
    assert event["source_url"] == "https://example.invalid/retained"
    assert all(item["claim_type"] == "User Assumption" for item in payload["high_materiality_events"] if item["event_id"] != linked_id)
    coverage = payload["public_coverage"]
    assert coverage["events"]["eligible_count"] == 13
    assert coverage["events"]["included_count"] == 10
    assert coverage["events"]["excluded_count"] == 3
    assert coverage["failed_runs"]["eligible_count"] == 1
    assert coverage["failed_runs"]["included_count"] == 0
    assert coverage["failed_runs"]["exclusion_reasons"] == {"dashboard_recent_run_preview": 1}
    assert coverage["status"] == "partial"
    assert len(statements) <= DASHBOARD_QUERY_BUDGET
    assert all("raw_documents.raw_text" not in statement and "raw_documents_1.raw_text" not in statement for statement in statements)
    assert "Original body must not load" not in str(payload)
