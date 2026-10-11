import json
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import HTTPException
import pypdfium2 as pdfium
from sqlalchemy import func, select

from app.api.dependencies import get_current_user
from app.main import app
from app.models import AiOutput, BriefSource, Company, ProcessingRun, User, ValuationSetupDraft
from app.providers.base import AIProviderResult
from app.providers.mock_provider import MockAIProvider
from app.services.ai_citations import validate_ai_citations
from app.services.pdf_financial_extraction import parse_pdf_page_ranges
from conftest import TEST_USER_ID

TEXT = "Apple reported increased services revenue. Management described persistent currency headwinds and uncertainty about future demand."


@pytest.fixture
def company(db):
    record = Company(ticker="AAPL", name="Apple", market="US", country="United States", currency="USD")
    db.add(record)
    db.commit()
    return record


def paste(client, company, **overrides):
    return client.post("/brief-sources", json={"company_id": company.id, "title": "User source",
                       "text": TEXT, **overrides})


def scan(client, source_id):
    return client.post(f"/brief-sources/{source_id}/analyze", json={"privacy_disclosure_version": "v1"})


def generated(source_id, **overrides):
    return {"source_marker": f"[source_id:brief_source:{source_id}]",
            "summary": "Services growth and currency headwinds merit review, without assumed numerical changes.",
            "findings": [{"title": "Services revenue growth", "importance": "medium",
                "importance_reason": "The reported revenue direction may affect the forward growth narrative.",
                "quote": "Apple reported increased services revenue.", "confidence": "medium",
                "valuation_inputs": [{"field": "revenue_growth_years_json", "direction": "review",
                                      "reason": "Review whether the existing growth path already reflects this report."}]}], **overrides}


def mock_generation(monkeypatch, response, prompts=None):
    def generate(self, prompt, schema):
        if prompts is not None:
            prompts.append(prompt)
        return AIProviderResult("fixture-model", json.dumps(response), "Mock Data test", "medium")
    monkeypatch.setattr(MockAIProvider, "generate_structured_response", generate)


def test_private_source_duplicate_and_no_body_in_list(client, db, company):
    first = paste(client, company)
    assert first.status_code == 200
    source_id = first.json()["data"]["id"]
    assert paste(client, company).json()["data"]["id"] == source_id
    listing = client.get("/brief-sources").json()["data"]
    assert len(listing) == 1
    assert "text" not in listing[0] and "content_text" not in listing[0] and "pdf_bytes" not in listing[0]
    assert client.get(f"/brief-sources/{source_id}").json()["data"]["text"] == TEXT
    assert db.scalar(select(func.count()).select_from(BriefSource)) == 1
    assert db.scalars(select(ProcessingRun)).all()[-1].skipped_duplicate_count == 1


def test_other_owner_cannot_list_read_scan_or_download(client, db, company):
    source_id = paste(client, company).json()["data"]["id"]
    db.add(User(id="other", email="other@example.test", name="Other"))
    db.commit()
    app.dependency_overrides[get_current_user] = lambda: {"id": "other"}
    assert client.get("/brief-sources").json()["data"] == []
    for suffix in ["", "/pdf"]:
        assert client.get(f"/brief-sources/{source_id}{suffix}").status_code == 404
    assert scan(client, source_id).status_code == 404


@pytest.mark.parametrize("overrides", [{"text": "short"}, {"text": "x" * 60001}, {"text": TEXT + "\x00"},
    {"title": " "}, {"as_of_date": "2999-01-01"}, {"source_url": "javascript:alert(1)"}, {"company_id": 9999}])
def test_source_validation(client, company, overrides):
    assert paste(client, company, **overrides).status_code in (400, 404, 422)


def test_scan_requires_disclosure_and_preserves_private_models(client, db, company, monkeypatch):
    source_id = paste(client, company).json()["data"]["id"]
    prompts = []
    mock_generation(monkeypatch, generated(source_id), prompts)
    assert client.post(f"/brief-sources/{source_id}/analyze", json={"privacy_disclosure_version": "old"}).status_code == 409
    assert prompts == []
    result = scan(client, source_id)
    assert result.status_code == 200, result.text
    data = result.json()["data"]
    assert data["analysis_status"] == "complete" and data["is_mock"] is True
    assert data["review_status"] == "pending"
    suggestion = data["analysis"]["findings"][0]["valuation_inputs"][0]
    assert suggestion["review_href"] == f"/companies/{company.id}/valuation/draft#revenue-growth"
    assert db.scalar(select(func.count()).select_from(ValuationSetupDraft)) == 0
    assert scan(client, source_id).status_code == 200
    assert len(prompts) == 1
    assert "portfolio_holdings" not in prompts[0] and "current_assumptions" not in prompts[0]
    output = db.get(AiOutput, data["ai_output_id"])
    assert output.citation_validation_status == "valid" and output.is_blocked is False
    assert output.user_id == TEST_USER_ID and output.input_hash
    assert output.external_data_classes_json == ["selected_source_text", "source_date", "public_company_identity", "valuation_field_names"]
    assert db.scalars(select(ProcessingRun)).all()[-1].status == "success"


@pytest.mark.parametrize("corruption", ["quote", "field", "marker", "recommendation"])
def test_invalid_ai_is_blocked_not_published(client, db, company, monkeypatch, corruption):
    source_id = paste(client, company).json()["data"]["id"]
    response = generated(source_id)
    if corruption == "quote":
        response["findings"][0]["quote"] = "Invented claim not in the source"
    elif corruption == "field":
        response["findings"][0]["valuation_inputs"][0]["field"] = "secret_portfolio"
    elif corruption == "marker":
        response["source_marker"] = "[source_id:raw_document:9999]"
    else:
        response["summary"] = "You should buy this stock immediately."
    mock_generation(monkeypatch, response)
    result = scan(client, source_id)
    assert result.status_code == 422
    data = client.get(f"/brief-sources/{source_id}").json()["data"]
    assert data["analysis_status"] == "failed" and data["analysis"] is None
    assert db.get(AiOutput, data["ai_output_id"]).is_blocked is True


def test_provider_failure_is_audited_and_retryable(client, db, company, monkeypatch):
    source_id = paste(client, company).json()["data"]["id"]
    def fail(*args, **kwargs):
        raise RuntimeError("provider raw secret body must not escape")
    monkeypatch.setattr(MockAIProvider, "generate_structured_response", fail)
    result = scan(client, source_id)
    assert result.status_code == 502 and "raw secret" not in result.text
    assert db.get(BriefSource, source_id).analysis_status == "failed"
    assert db.scalars(select(ProcessingRun)).all()[-1].status == "failed"
    assert db.scalars(select(AiOutput)).all()[-1].execution_status == "failed"
    mock_generation(monkeypatch, generated(source_id))
    assert scan(client, source_id).status_code == 200


def test_active_scan_conflict_and_interrupted_scan_recovery(client, db, company, monkeypatch):
    source_id = paste(client, company).json()["data"]["id"]
    source = db.get(BriefSource, source_id)
    source.analysis_status = "scanning"
    source.analysis_started_at = datetime.now(UTC)
    db.commit()
    assert scan(client, source_id).status_code == 409
    source.analysis_started_at = datetime.now(UTC) - timedelta(minutes=3)
    db.commit()
    mock_generation(monkeypatch, generated(source_id))
    assert scan(client, source_id).status_code == 200


def test_pdf_invalid_blank_and_huge_ranges_fail_safely(client, db, company):
    data = {"company_id": company.id, "title": "PDF source"}
    response = client.post("/brief-sources/pdf", data=data, files={"file": ("test.pdf", b"not-pdf", "application/pdf")})
    assert response.status_code == 400
    writer = pdfium.PdfDocument.new()
    writer.new_page(200, 200)
    content = BytesIO()
    writer.save(content)
    writer.close()
    response = client.post("/brief-sources/pdf", data=data, files={"file": ("blank.pdf", content.getvalue(), "application/pdf")})
    assert response.status_code == 422 and "OCR" in response.text
    with pytest.raises(HTTPException):
        parse_pdf_page_ranges("1-999999999999")
    assert db.scalar(select(func.count()).select_from(BriefSource)) == 0


def test_brief_citations_cannot_bypass_owner(db, client, company):
    source_id = paste(client, company).json()["data"]["id"]
    source_id_marker = f"brief_source:{source_id}"
    db.add(User(id="other", email="other@example.test", name="Other"))
    db.commit()
    output = AiOutput(user_id="other", model_name="fixture", provider_name="mock", is_mock=True,
        prompt_version="test", input_hash="hash", source_ids_json=[source_id_marker],
        output_text=f"[source_id:{source_id_marker}]", confidence_label="low")
    db.add(output)
    db.commit()
    _, status = validate_ai_citations(db, output, [{"source_id": source_id_marker, "quote": TEXT}])
    assert status == "invalid" and output.is_blocked


def test_pdf_success_retains_original_and_extraction_provenance(client, db, company):
    original = (Path(__file__).parent / "fixtures" / "financial_statement_table.pdf").read_bytes()
    response = client.post("/brief-sources/pdf", data={"company_id": company.id, "title": "Test financial PDF"},
                           files={"file": ("statement.pdf", original, "application/pdf")})
    assert response.status_code == 200, response.text
    source = response.json()["data"]
    assert source["extraction"]["selected_pages"] == [1]
    assert source["extraction"]["text_sha256"]
    assert source["extraction"]["page_spans"][0]["page"] == 1
    pdf = client.get(f'/brief-sources/{source["id"]}/pdf')
    assert pdf.content == original
    assert pdf.headers["cache-control"] == "private, no-store" and pdf.headers["x-content-type-options"] == "nosniff"
    assert db.scalar(select(func.count()).select_from(ValuationSetupDraft)) == 0


def test_pdf_indirect_content_streams_are_resolved(monkeypatch):
    from types import SimpleNamespace
    import pdfplumber
    from pdfminer.pdftypes import PDFObjRef, resolve1
    from app.services.brief_source_extraction import extract_brief_pdf
    original = (Path(__file__).parent / "fixtures" / "financial_statement_table.pdf").read_bytes()
    pdf = pdfplumber.open(BytesIO(original))
    stream = resolve1(pdf.pages[0].page_obj.contents[0])
    pdf.pages[0].page_obj.contents = [PDFObjRef(SimpleNamespace(getobj=lambda _: stream), 1)]
    monkeypatch.setattr(pdfplumber, "open", lambda *args, **kwargs: pdf)
    text, evidence = extract_brief_pdf("indirect.pdf", "application/pdf", original, None)
    assert len(text) > 40 and evidence["page_count"] == 1


def test_provider_schema_is_structural_while_local_field_validation_is_strict():
    from app.services.brief_sources import _response_schema
    from app.schemas.brief_sources import BriefAnalysis
    from pydantic import ValidationError
    provider_schema = json.dumps(_response_schema())
    assert '"enum"' not in provider_schema and '"maxItems"' not in provider_schema
    invalid = generated(1)
    invalid["findings"][0]["valuation_inputs"][0]["field"] = "invented_input"
    with pytest.raises(ValidationError):
        BriefAnalysis.model_validate(invalid)
