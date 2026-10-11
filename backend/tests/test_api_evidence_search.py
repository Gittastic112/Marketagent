from datetime import UTC, datetime

from sqlalchemy import event as sqlalchemy_event

from app.api.dependencies import get_current_user
from app.api.routers.search import (
    SEARCH_QUERY_BUDGET,
    SEARCH_RESPONSE_BUDGET_MS,
    normalize_search_timestamp,
)
from app.main import app
from app.models.ai import AiOutput
from app.models.event import Event
from app.models.narrative import NarrativeClaim, NarrativeCluster, NarrativeMention
from app.models.raw_document import RawDocument
from app.models.research import ResearchMessage, ResearchSession
from app.models.source import Source
from app.models.user import User
from helpers import response_data


def test_search_timestamp_normalization_supports_mixed_model_columns():
    naive = datetime(2026, 8, 1, 9, 30)
    aware = datetime(2026, 8, 1, 9, 30, tzinfo=UTC)

    assert normalize_search_timestamp(naive) == aware
    assert normalize_search_timestamp(aware) == aware


def test_evidence_search_returns_source_and_exact_stored_span(client):
    company = response_data(client.post("/companies", json={"ticker": "SRCH", "name": "Search Co"}))
    source = response_data(client.post("/sources", json={"name": "Search filing source", "source_type": "filing"}))
    text = "Operating margin expanded by 240 basis points after pricing improved."
    document = response_data(client.post("/raw-documents", json={
        "company_id": company["id"],
        "source_id": source["id"],
        "document_type": "10-Q",
        "title": "Quarterly margin filing",
        "raw_text": text,
        "content_hash": "evidence-search-document",
    }))
    response_data(client.post("/events", json={
        "company_id": company["id"],
        "raw_document_id": document["id"],
        "event_type": "filing_update",
        "information_speed": "medium",
        "title": "Operating margin expansion",
        "description": "Margin expanded in the quarter.",
    }))

    results = response_data(client.get("/search/evidence?q=margin"))

    document_result = next(item for item in results if item["result_type"] == "document")
    assert document_result["source_name"] == "Search filing source"
    assert document_result["claim_type"] == "Fact"
    assert document_result["scope"] == "shared"
    assert document_result["locator"]["quote"] == "margin"
    assert text[document_result["locator"]["start_char"]:document_result["locator"]["end_char"]] == "margin"
    assert any(item["result_type"] == "event" for item in results)


def test_evidence_search_company_filter_excludes_other_companies(client):
    first = response_data(client.post("/companies", json={"ticker": "ONE", "name": "One"}))
    second = response_data(client.post("/companies", json={"ticker": "TWO", "name": "Two"}))
    source = response_data(client.post("/sources", json={"name": "Filter source", "source_type": "manual"}))
    for company, suffix in ((first, "one"), (second, "two")):
        response_data(client.post("/raw-documents", json={
            "company_id": company["id"],
            "source_id": source["id"],
            "document_type": "note",
            "title": f"Searchable catalyst {suffix}",
            "raw_text": "Searchable catalyst evidence.",
            "content_hash": f"search-filter-{suffix}",
        }))

    results = response_data(client.get(f"/search/evidence?q=catalyst&company_id={first['id']}"))

    assert results
    assert {item["company_id"] for item in results} == {first["id"]}


def test_evidence_search_includes_owned_research_records_and_filters_types(client, db_session):
    company = response_data(client.post("/companies", json={"ticker": "OWND", "name": "Owned Search"}))
    thesis = response_data(client.post("/thesis-notes", json={
        "company_id": company["id"],
        "title": "Durable conviction thesis",
        "thesis_text": "Conviction depends on recurring revenue durability.",
    }))
    alert = response_data(client.post("/alerts", json={
        "company_id": company["id"],
        "alert_type": "manual",
        "title": "Conviction evidence changed",
        "summary": "New evidence changes conviction.",
    }))
    decision = response_data(client.post("/decisions", json={
        "company_id": company["id"],
        "decision_type": "Hold",
        "rationale": "Maintain conviction while recurring revenue is verified.",
    }))
    valuation = response_data(client.post(f"/companies/{company['id']}/valuation-models", json={
        "company_id": company["id"],
        "name": "Conviction base case",
        "description": "Valuation conditioned on recurring revenue durability.",
    }))

    statements: list[str] = []

    def record_statement(*args) -> None:
        statements.append(args[2])

    engine = db_session.get_bind()
    sqlalchemy_event.listen(engine, "before_cursor_execute", record_statement)
    try:
        response = client.get("/search/evidence?q=conviction")
    finally:
        sqlalchemy_event.remove(engine, "before_cursor_execute", record_statement)
    results = response_data(response)

    assert {item["result_type"] for item in results} == {"thesis", "alert", "decision", "valuation"}
    assert next(item for item in results if item["result_type"] == "thesis")["href"] == f"/thesis-notes/{thesis['id']}"
    assert next(item for item in results if item["result_type"] == "alert")["href"] == f"/alerts/{alert['id']}"
    assert next(item for item in results if item["result_type"] == "decision")["record_id"] == decision["id"]
    assert next(item for item in results if item["result_type"] == "valuation")["href"] == (
        f"/companies/{company['id']}/valuation/{valuation['id']}"
    )
    assert {item["claim_type"] for item in results} == {"User Assumption"}
    assert {item["scope"] for item in results} == {"private"}
    assert next(item for item in results if item["result_type"] == "alert")["source_name"] == "User alert"
    assert len(statements) <= SEARCH_QUERY_BUDGET
    assert response.json()["meta"]["processing_time_ms"] <= SEARCH_RESPONSE_BUDGET_MS

    thesis_only = response_data(client.get("/search/evidence?q=conviction&type=thesis"))
    assert [item["result_type"] for item in thesis_only] == ["thesis"]


def test_evidence_search_does_not_leak_owned_research_records(client):
    company = response_data(client.post("/companies", json={"ticker": "PRIV", "name": "Private Search"}))
    response_data(client.post("/thesis-notes", json={
        "company_id": company["id"],
        "title": "Private catalyst thesis",
        "thesis_text": "Private catalyst detail.",
    }))
    response_data(client.post("/alerts", json={
        "company_id": company["id"],
        "alert_type": "manual",
        "title": "Private catalyst alert",
    }))
    response_data(client.post("/decisions", json={
        "company_id": company["id"],
        "decision_type": "Pass",
        "rationale": "Private catalyst is not sufficiently supported.",
    }))
    response_data(client.post(f"/companies/{company['id']}/valuation-models", json={
        "company_id": company["id"],
        "name": "Private catalyst valuation",
    }))

    app.dependency_overrides[get_current_user] = lambda: {
        "id": "other-search-user",
        "email": "other-search@example.com",
        "name": "Other Search User",
    }
    results = response_data(client.get("/search/evidence?q=private"))

    assert not [item for item in results if item["result_type"] in {"thesis", "alert", "decision", "valuation"}]


def test_evidence_search_includes_shared_narrative_clusters_and_claims(client, db_session):
    cluster = NarrativeCluster(
        name="Datacenter efficiency cycle",
        description="A shared narrative about infrastructure efficiency.",
    )
    db_session.add(cluster)
    db_session.flush()
    db_session.add(
        NarrativeClaim(
            cluster_id=cluster.id,
            claim_text="Rack density is the narrative catalyst to verify.",
        )
    )
    db_session.commit()

    cluster_results = response_data(client.get("/search/evidence?q=efficiency&type=narrative"))
    claim_results = response_data(client.get("/search/evidence?q=density&type=narrative"))

    assert len(cluster_results) == 1
    assert cluster_results[0]["record_id"] == cluster.id
    assert cluster_results[0]["scope"] == "shared"
    assert cluster_results[0]["review_status"] == "not_applicable"
    assert cluster_results[0]["claim_type"] == "AI Interpretation"
    assert cluster_results[0]["href"] == f"/narratives#narrative-{cluster.id}"
    assert len(claim_results) == 1
    assert claim_results[0]["record_id"] == cluster.id
    assert "density" in claim_results[0]["excerpt"].lower()


def test_evidence_search_includes_only_owned_research_sessions_and_user_messages(client, db_session):
    owned = ResearchSession(
        user_id="admin_user_id_fallback",
        title="Private semiconductor notebook",
    )
    other_user = User(id="other-search-owner", email="search-owner@example.com", name="Other owner")
    other = ResearchSession(
        user_id=other_user.id,
        title="Private semiconductor notebook from another user",
    )
    db_session.add_all([other_user, owned, other])
    db_session.flush()
    owned_message = ResearchMessage(
        session_id=owned.id,
        role="user",
        content="Verify semiconductor inventory normalization before changing the thesis.",
    )
    db_session.add_all([
        owned_message,
        ResearchMessage(
            session_id=other.id,
            role="user",
            content="Semiconductor inventory detail belonging to another user.",
        ),
        ResearchMessage(
            session_id=owned.id,
            role="assistant",
            content="Unreviewed assistant semiconductor text must not appear as a message result.",
        ),
    ])
    db_session.commit()

    results = response_data(client.get("/search/evidence?q=semiconductor"))

    session_results = [item for item in results if item["result_type"] == "research_session"]
    message_results = [item for item in results if item["result_type"] == "research_message"]
    assert [item["record_id"] for item in session_results] == [owned.id]
    assert [item["record_id"] for item in message_results] == [owned_message.id]
    assert message_results[0]["href"] == f"/research/sessions/{owned.id}#message-{owned_message.id}"
    assert {item["scope"] for item in session_results + message_results} == {"private"}
    assert {item["claim_type"] for item in session_results + message_results} == {"User Assumption"}


def test_evidence_search_indexes_only_approved_unblocked_successful_owned_ai_outputs(client, db_session):
    source = Source(name="Reviewed AI search source", source_type="manual")
    other_user = User(id="other-search-owner", email="other-ai-search@example.com", name="Other AI owner")
    db_session.add_all([source, other_user])
    db_session.flush()
    document = RawDocument(
        source_id=source.id,
        document_type="manual_note",
        title="Reviewed research input",
        raw_text="Stored operating leverage evidence.",
        content_hash="reviewed-ai-search-source",
    )
    db_session.add(document)
    db_session.flush()

    def output(suffix: str, **overrides) -> AiOutput:
        values = {
            "user_id": "admin_user_id_fallback",
            "raw_document_id": document.id,
            "reference_type": "raw_document",
            "reference_id": document.id,
            "model_name": "search-fixture-model",
            "provider_name": "search-fixture-provider",
            "is_mock": True,
            "prompt_version": f"search-{suffix}",
            "input_hash": f"search-{suffix}",
            "source_ids_json": [f"raw_document:{document.id}"],
            "source_scope": "raw_document_text",
            "privacy_disclosure_version": "v1",
            "external_data_classes_json": [],
            "transmission_scope": "none",
            "execution_status": "success",
            "is_blocked": False,
            "output_text": f"Reviewed operating leverage interpretation {suffix}.",
            "confidence_label": "fixture",
            "human_review_status": "approved",
            "reviewer_id": "admin_user_id_fallback",
            "reviewed_at": datetime.now(UTC),
        }
        values.update(overrides)
        return AiOutput(**values)

    approved = output("approved")
    db_session.add_all([
        approved,
        output("pending", human_review_status="pending", reviewed_at=None, reviewer_id=None),
        output("blocked", is_blocked=True),
        output("failed", execution_status="failed"),
        output("other-owner", user_id="other-search-owner"),
    ])
    db_session.commit()

    response = client.get("/search/evidence?q=leverage&type=ai_output")
    results = response_data(response)

    assert [item["record_id"] for item in results] == [approved.id]
    assert results[0]["claim_type"] == "AI Interpretation"
    assert results[0]["scope"] == "private"
    assert results[0]["review_status"] == "approved"
    assert results[0]["is_mock"] is True
    assert results[0]["href"] == f"/documents/{document.id}/ai#ai-output-{approved.id}"
    assert response.json()["meta"]["is_mock"] is True


def test_evidence_search_new_corpora_respect_company_filter_and_bound_private_excerpts(client, db_session):
    first = response_data(client.post("/companies", json={"ticker": "NAR1", "name": "Narrative One"}))
    second = response_data(client.post("/companies", json={"ticker": "NAR2", "name": "Narrative Two"}))
    cluster = NarrativeCluster(name="Capacity narrative", description="Shared capacity research")
    db_session.add(cluster)
    db_session.flush()
    for company_id in (first["id"], second["id"]):
        event = Event(
            company_id=company_id,
            event_type="manual",
            information_speed="slow",
            title=f"Capacity event {company_id}",
        )
        db_session.add(event)
        db_session.flush()
        if company_id == first["id"]:
            db_session.add(NarrativeMention(cluster_id=cluster.id, event_id=event.id, context_text="Capacity"))
    session = ResearchSession(user_id="admin_user_id_fallback", title="Capacity private session")
    db_session.add(session)
    db_session.flush()
    private_message = ResearchMessage(
        session_id=session.id,
        role="user",
        content=("private context " * 80) + "capacity checkpoint " + ("private tail " * 80),
    )
    db_session.add(private_message)
    db_session.commit()

    first_results = response_data(client.get(f"/search/evidence?q=capacity&company_id={first['id']}"))
    second_results = response_data(client.get(f"/search/evidence?q=capacity&company_id={second['id']}"))
    private_results = response_data(client.get("/search/evidence?q=capacity&type=research_message"))

    assert any(item["result_type"] == "narrative" for item in first_results)
    assert not any(item["result_type"] == "narrative" for item in second_results)
    assert not any(item["result_type"] in {"research_session", "research_message"} for item in first_results)
    assert len(private_results[0]["excerpt"]) <= 280
