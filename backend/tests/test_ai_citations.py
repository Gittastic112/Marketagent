import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.main import app
from app.models.ai import AiOutput
from app.models.company import Company
from app.models.raw_document import RawDocument
from app.models.source import Source
from helpers import response_data


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ai_output_evaluation_cases.json"
CASES = json.loads(FIXTURE_PATH.read_text())


def _create_output(db: Session, case: dict, *, suffix: str) -> tuple[AiOutput, RawDocument]:
    company = Company(ticker=f"AI{suffix}", name=f"AI citation {suffix}")
    source = Source(name=f"AI citation source {suffix}", source_type="manual")
    db.add_all([company, source])
    db.flush()
    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="manual_note",
        title=f"AI citation input {suffix}",
        raw_text=case["source_text"],
        content_hash=f"ai-citation-{suffix}",
    )
    db.add(document)
    db.flush()
    output = AiOutput(
        user_id="admin_user_id_fallback",
        raw_document_id=document.id,
        reference_type="raw_document",
        reference_id=document.id,
        model_name="fixture-model",
        provider_name="fixture",
        is_mock=True,
        prompt_version="fixture-v1",
        input_hash=f"fixture-{suffix}",
        source_ids_json=[f"raw_document:{document.id}"],
        source_scope="raw_document_text",
        privacy_disclosure_version="v1",
        external_data_classes_json=[],
        transmission_scope="none",
        execution_status="success",
        output_text=case["output_text"],
        confidence_label="test_fixture",
    )
    db.add(output)
    db.commit()
    db.refresh(output)
    return output, document


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_ai_citation_fixture_cases(
    client: TestClient,
    db_session: Session,
    case: dict,
) -> None:
    output, document = _create_output(db_session, case, suffix=str(CASES.index(case)))
    data = response_data(
        client.post(
            f"/ai-outputs/{output.id}/citations/validate",
            json={
                "citations": [
                    {
                        "source_id": f"raw_document:{document.id}",
                        "quote": case["quote"],
                    }
                ]
            },
        )
    )

    assert data["citation_validation_status"] == case["expected_status"]
    assert data["evaluation_json"]["passed"] is case["expected_passed"]


def test_ai_output_approval_requires_passing_evaluation(
    client: TestClient,
    db_session: Session,
) -> None:
    output, _ = _create_output(db_session, CASES[1], suffix="approval")

    response = client.patch(
        f"/ai-outputs/{output.id}/review",
        json={"status": "approved"},
    )

    assert response.status_code == 409
    assert "cannot be approved" in response.json()["errors"][0]["message"]


def test_ai_output_review_is_owner_scoped(
    client: TestClient,
    db_session: Session,
) -> None:
    output, _ = _create_output(db_session, CASES[0], suffix="owner")
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "different-user",
        "email": "different@example.com",
        "name": "Different User",
    }

    response = client.get(f"/ai-outputs/{output.id}")

    assert response.status_code == 404


def test_rejection_requires_and_persists_review_notes(
    client: TestClient,
    db_session: Session,
) -> None:
    output, _ = _create_output(db_session, CASES[0], suffix="reject")
    missing_notes = client.patch(
        f"/ai-outputs/{output.id}/review",
        json={"status": "rejected"},
    )
    assert missing_notes.status_code == 422

    reviewed = response_data(
        client.patch(
            f"/ai-outputs/{output.id}/review",
            json={"status": "rejected", "notes": "The summary overstates the source."},
        )
    )
    assert reviewed["human_review_status"] == "rejected"
    assert reviewed["review_notes"] == "The summary overstates the source."
    assert reviewed["reviewer_id"] == "admin_user_id_fallback"
