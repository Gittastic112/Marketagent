"""Manual research records retain their company, text and discovery time."""
import pytest


@pytest.mark.parametrize("endpoint,payload", [
    ("variant-perceptions", {"market_belief": "Mock Data market view", "my_belief": "Mock Data analyst view"}),
    ("evidence", {"evidence_text": "Mock Data reviewable passage", "effect": "Neutral", "date_discovered": "2026-01-15T00:00:00Z"}),
])
def test_research_creation_retains_company_and_rejects_missing_reference(client, endpoint, payload):
    company = client.post("/companies", json={"ticker": "JOURNAL", "name": "Mock Data research journal"}).json()["data"]
    response = client.post(f"/{endpoint}", json={**payload, "company_id": company["id"]})
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["company_id"] == company["id"]
    for key, value in payload.items():
        if key == "date_discovered":
            assert data[key][:10] == value[:10]
        else:
            assert data[key] == value
    assert client.post(f"/{endpoint}", json={**payload, "company_id": 999999}).status_code == 404
    assert len(client.get(f"/{endpoint}", params={"company_id": company["id"]}).json()["data"]) == 1


def test_second_outcome_review_is_a_conflict_and_does_not_replace_saved_review(client):
    company = client.post("/companies", json={"ticker": "OUTCOME", "name": "Mock Data outcome"}).json()["data"]
    decision = client.post("/decisions", json={"company_id": company["id"], "decision_type": "Pass",
        "rationale": "Mock Data missing evidence", "price_at_time": 0}).json()["data"]
    path = f"/decisions/{decision['id']}/review"
    assert client.post(path, json={"what_happened": "Mock Data original review"}).status_code == 201
    response = client.post(path, json={"what_happened": "Outdated tab replacement"})
    assert response.status_code == 409, response.text
    stored = client.get(f"/decisions/{decision['id']}").json()["data"]
    assert stored["price_at_time"] == 0
    assert stored["outcome_review"]["what_happened"] == "Mock Data original review"
