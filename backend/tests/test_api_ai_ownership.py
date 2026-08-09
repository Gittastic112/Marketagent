from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.main import app
from helpers import response_data


def use_user(user_id: str) -> None:
    app.dependency_overrides[get_current_user] = lambda: {
        "id": user_id,
        "email": f"{user_id}@example.com",
        "name": user_id,
    }


def test_raw_document_ai_outputs_are_private_to_the_generating_user(
    client: TestClient,
) -> None:
    company = response_data(
        client.post("/companies", json={"ticker": "AIOW", "name": "AI Owner"})
    )
    source = response_data(
        client.post("/sources", json={"name": "Manual AI Source", "source_type": "manual"})
    )
    document = response_data(
        client.post(
            "/raw-documents",
            json={
                "company_id": company["id"],
                "source_id": source["id"],
                "document_type": "manual_note",
                "title": "Private summary input",
                "raw_text": "Private raw document text.",
                "content_hash": "private-ai-output-1",
            },
        )
    )

    disclosure_response = client.post(
        f"/raw-documents/{document['id']}/ai-summary",
        json={"privacy_disclosure_version": "outdated"},
    )
    assert disclosure_response.status_code == 409
    assert disclosure_response.json()["errors"][0]["code"] == "AI_PRIVACY_DISCLOSURE_REQUIRED"

    generated_response = client.post(
        f"/raw-documents/{document['id']}/ai-summary",
        json={"privacy_disclosure_version": "v1"},
    )
    generated = response_data(generated_response)
    assert generated_response.json()["meta"]["is_mock"] is True
    assert generated["provider_name"] == "mock"

    use_user("other-user")

    assert response_data(
        client.get(f"/raw-documents/{document['id']}/ai-outputs")
    ) == []
