from sqlalchemy.orm import Session

from app.models.ai import AiOutput
from app.models.company import Company
from app.models.raw_document import RawDocument
from app.models.source import Source
from app.services.ai_citation_suggestions import (
    claim_for_source_marker,
    score_passage_relevance,
    segment_source_text,
)
from helpers import response_data


def _create_output(
    db: Session,
    *,
    suffix: str,
    source_text: str | None,
    output_text: str | None = None,
    declared_sources: list[str] | None = None,
) -> tuple[AiOutput, RawDocument]:
    company = Company(ticker=f"SG{suffix}", name=f"Suggestion {suffix}")
    source = Source(name=f"Suggestion source {suffix}", source_type="manual")
    db.add_all([company, source])
    db.flush()
    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="manual_note",
        title=f"Suggestion input {suffix}",
        raw_text=source_text,
        content_hash=f"ai-suggestion-{suffix}",
    )
    db.add(document)
    db.flush()
    source_id = f"raw_document:{document.id}"
    output = AiOutput(
        user_id="admin_user_id_fallback",
        raw_document_id=document.id,
        reference_type="raw_document",
        reference_id=document.id,
        model_name="fixture-model",
        provider_name="fixture",
        is_mock=False,
        prompt_version="fixture-v1",
        input_hash=f"fixture-suggestion-{suffix}",
        source_ids_json=declared_sources if declared_sources is not None else [source_id],
        source_scope="raw_document_text",
        privacy_disclosure_version="v1",
        external_data_classes_json=[],
        transmission_scope="none",
        execution_status="success",
        output_text=output_text or f"Revenue increased 12% year over year [source_id:{source_id}].",
        confidence_label="fixture",
    )
    db.add(output)
    db.commit()
    db.refresh(output)
    return output, document


def test_claim_extraction_uses_text_attached_to_the_requested_marker() -> None:
    text = (
        "Margins were stable [source_id:raw_document:1]. "
        "Revenue increased 12% year over year [source_id:raw_document:2]."
    )

    assert claim_for_source_marker(text, "raw_document:2") == "Revenue increased 12% year over year"


def test_source_segmentation_preserves_exact_offsets() -> None:
    text = "Intro paragraph.\n\nRevenue increased 12% year over year. Margins remained stable."

    segments = segment_source_text(text)

    target = next(segment for segment in segments if "Revenue increased" in segment.quote)
    assert text[target.start_char:target.end_char] == target.quote
    assert len(target.quote) <= 2_000


def test_relevance_scoring_rewards_matching_numeric_facts() -> None:
    claim = "Revenue increased 12% year over year"
    exact_number = "The company reported that revenue increased 12% year over year."
    wrong_number = "The company reported that revenue increased 3% year over year."

    exact = score_passage_relevance(claim, exact_number)
    wrong = score_passage_relevance(claim, wrong_number)

    assert exact.score > wrong.score
    assert "12%" in exact.matched_terms


def test_suggestion_endpoint_returns_ranked_exact_spans_that_validate(
    client,
    db_session: Session,
) -> None:
    source_text = (
        "Revenue was broadly unchanged in the prior period.\n\n"
        "Revenue increased 12% year over year as subscription demand improved.\n\n"
        "Operating expenses increased 3% during the same period."
    )
    output, document = _create_output(
        db_session,
        suffix="ready",
        source_text=source_text,
    )

    response = client.get(f"/ai-outputs/{output.id}/citations/suggestions")

    assert response.status_code == 200
    suggestion = response_data(response)[0]
    assert suggestion["source_id"] == f"raw_document:{document.id}"
    assert suggestion["status"] == "ready"
    assert suggestion["claim_text"] == "Revenue increased 12% year over year"
    candidate = suggestion["candidates"][0]
    assert source_text[candidate["start_char"]:candidate["end_char"]] == candidate["quote"]
    assert "12%" in candidate["matched_terms"]
    assert candidate["confidence"] in {"high", "medium", "low"}
    assert candidate["internal_href"] == f"/documents/{document.id}/sections"

    validated = response_data(
        client.post(
            f"/ai-outputs/{output.id}/citations/validate",
            json={
                "citations": [
                    {
                        "source_id": suggestion["source_id"],
                        "quote": candidate["quote"],
                        "start_char": candidate["start_char"],
                        "end_char": candidate["end_char"],
                    }
                ]
            },
        )
    )
    assert validated["citation_validation_status"] == "valid"
    assert validated["evaluation_json"]["passed"] is True


def test_suggestions_expose_missing_unsupported_and_undeclared_sources(
    client,
    db_session: Session,
) -> None:
    missing_output, _ = _create_output(
        db_session,
        suffix="missing",
        source_text=None,
    )
    missing = response_data(
        client.get(f"/ai-outputs/{missing_output.id}/citations/suggestions")
    )[0]
    assert missing["status"] == "source_text_unavailable"
    assert missing["candidates"] == []

    unsupported_output, _ = _create_output(
        db_session,
        suffix="unsupported",
        source_text="Stored text",
        output_text="A market claim [source_id:event:42].",
        declared_sources=["event:42"],
    )
    unsupported = response_data(
        client.get(f"/ai-outputs/{unsupported_output.id}/citations/suggestions")
    )[0]
    assert unsupported["status"] == "unsupported_source"

    undeclared_output, document = _create_output(
        db_session,
        suffix="undeclared",
        source_text="Revenue increased 12% year over year.",
        declared_sources=[],
    )
    undeclared_output.output_text = (
        f"Revenue increased 12% year over year [source_id:raw_document:{document.id}]."
    )
    db_session.commit()
    undeclared = response_data(
        client.get(f"/ai-outputs/{undeclared_output.id}/citations/suggestions")
    )[0]
    assert undeclared["status"] == "undeclared_source"
    assert undeclared["candidates"] == []


def test_suggestion_endpoint_is_owner_scoped(client, db_session: Session) -> None:
    from app.api.dependencies import get_current_user
    from app.main import app

    output, _ = _create_output(
        db_session,
        suffix="owner",
        source_text="Revenue increased 12% year over year.",
    )
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "different-user",
        "email": "different@example.com",
        "name": "Different User",
    }

    response = client.get(f"/ai-outputs/{output.id}/citations/suggestions")

    assert response.status_code == 404
