from app.models import FilingSection, FilingSectionDiff
from helpers import response_data


def test_unmatched_filing_sections_are_baselines_and_company_filter_precedes_limit(client, db):
    from app.services.intelligence_review import build_intelligence_review_queue
    source = response_data(client.post("/sources", json={"name": "Baseline source", "source_type": "filing"}))
    for index in range(2):
        company = response_data(client.post("/companies", json={"ticker": f"BASE{index}", "name": "Baseline Co"}))
        document = response_data(client.post("/raw-documents", json={
            "company_id": company["id"], "source_id": source["id"], "document_type": "10-K", "title": "First filing",
            "raw_text": "Initial text", "content_hash": f"baseline-{index}"}))
        section = FilingSection(raw_document_id=document["id"], item_name="Risk Factors", text_content="Initial text", word_count=500)
        db.add(section)
        db.flush()
        db.add(FilingSectionDiff(current_section_id=section.id, prior_section_id=None,
            added_words=500, removed_words=0, diff_html=""))
        db.commit()
        if index == 0:
            first_id = company["id"]
    items = build_intelligence_review_queue(db, company_id=first_id, limit=1)
    assert len(items) == 1
    assert items[0]["company_id"] == first_id
    assert items[0]["item_type"] == "filing_baseline"
    assert items[0]["severity"] == "info"
    assert "not evidence of a language change" in items[0]["summary"]
    assert items[0]["prior_document_id"] is None
    response = response_data(client.get(f"/intelligence/review?company_id={first_id}"))
    assert response[0]["item_type"] == "filing_baseline"


def test_intelligence_review_combines_explicit_contradictions_and_filing_diffs(client, db):
    company = response_data(client.post("/companies", json={"ticker": "REVW", "name": "Review Co"}))
    source = response_data(client.post("/sources", json={"name": "Review source", "source_type": "filing"}))
    documents = []
    for suffix in ("prior", "current"):
        documents.append(response_data(client.post("/raw-documents", json={
            "company_id": company["id"],
            "source_id": source["id"],
            "document_type": "10-K",
            "title": f"{suffix} filing",
            "raw_text": f"{suffix} risk language",
            "content_hash": f"intelligence-review-{suffix}",
        })))
    events = []
    for index, title in enumerate(("Management expects growth", "Demand declined")):
        events.append(response_data(client.post("/events", json={
            "company_id": company["id"],
            "raw_document_id": documents[index]["id"],
            "event_type": "manual",
            "information_speed": "medium",
            "title": title,
        })))
    link_response = client.post(
        f"/events/{events[0]['id']}/contradictions",
        json={"target_event_id": events[1]["id"]},
    )
    assert link_response.status_code == 201

    prior = FilingSection(raw_document_id=documents[0]["id"], item_name="Risk Factors", text_content="old", word_count=1)
    current = FilingSection(raw_document_id=documents[1]["id"], item_name="Risk Factors", text_content="new risk language", word_count=3)
    db.add_all([prior, current])
    db.flush()
    db.add(FilingSectionDiff(current_section_id=current.id, prior_section_id=prior.id, added_words=60, removed_words=10, diff_html=""))
    db.commit()

    items = response_data(client.get(f"/intelligence/review?company_id={company['id']}"))

    assert {item["item_type"] for item in items} == {"contradiction", "filing_language_change"}
    contradiction = next(item for item in items if item["item_type"] == "contradiction")
    assert contradiction["claim_type"] == "User Assumption"
    language_change = next(item for item in items if item["item_type"] == "filing_language_change")
    assert language_change["claim_type"] == "Calculation"
    assert language_change["severity"] == "medium"
    assert language_change["evidence_href"].endswith(f"?diff={language_change['item_id'].split(':')[1]}")


def test_event_relationships_reject_self_links_and_duplicates(client):
    first = response_data(client.post("/events", json={"event_type": "manual", "information_speed": "slow", "title": "First"}))
    second = response_data(client.post("/events", json={"event_type": "manual", "information_speed": "slow", "title": "Second"}))
    assert client.post(f"/events/{first['id']}/contradictions", json={"target_event_id": first["id"]}).status_code == 422
    assert client.post(f"/events/{first['id']}/contradictions", json={"target_event_id": second["id"]}).status_code == 201
    assert client.post(f"/events/{first['id']}/contradictions", json={"target_event_id": second["id"]}).status_code == 409

    refreshed = response_data(client.get(f"/events/{first['id']}"))
    assert refreshed["contradicts"] == [{"id": second["id"], "title": "Second", "event_type": "manual"}]
