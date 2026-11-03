from hashlib import sha256

import pytest

from app.api.dependencies import get_current_user
from app.main import app
from app.models import Company, RawDocument, Source, User
from app.models.evaluation import EvaluationRun, FinancialExtractionEval
from app.models.financial import FinancialExtractionCandidate


@pytest.fixture
def evaluation_case(db_session):
    company = Company(ticker="EVAL", name="Mock Data evaluation issuer")
    source = Source(name="Mock Data reference", source_type="manual")
    db_session.add_all([company, source])
    db_session.flush()
    document = RawDocument(company_id=company.id, source_id=source.id,
        document_type="annual_report", title="Mock Data annual report 2025",
        raw_text="Revenue 100 USD\nNet income 0 USD", content_hash="evaluation-fixture")
    db_session.add(document)
    db_session.commit()
    return document, {
        "run_name": "Mock Data extraction check", "document_id": document.id,
        "source_text_sha256": sha256(document.raw_text.encode()).hexdigest(),
        "reference_reviewed": True, "reference_is_complete": True, "is_mock": True,
        "expected": [
            {"metric_code": "revenue", "value": 100, "unit": "USD", "fiscal_year": 2025,
             "period_type": "annual", "source_line_number": 1},
            {"metric_code": "net_income", "value": 0, "unit": "USD", "fiscal_year": 2025,
             "period_type": "annual", "source_line_number": 2},
        ],
    }


def test_executes_against_reference_and_persists_atomic_report(client, db_session, evaluation_case):
    document, payload = evaluation_case
    basis = client.get(f"/evaluations/documents/{document.id}/basis").json()["data"]
    assert basis["source_text_sha256"] == payload["source_text_sha256"]
    response = client.post("/evaluations/runs", json=payload)
    assert response.status_code == 201, response.text
    result = response.json()["data"]
    assert result["status"] == "completed"
    assert result["completed_at"]
    report = result["report_json"]
    # The current text extractor does not extract units. Do not disguise that
    # known limitation as successful full financial extraction.
    assert report["precision"] == report["recall"] == 0
    assert report["numeric_accuracy"] == 1
    assert report["unit_accuracy"] == 0
    assert report["expected_count"] == report["predicted_count"] == 2
    assert report["is_mock"] is True
    assert len(report["reference_sha256"]) == 64
    assert response.json()["meta"]["is_mock"] is True
    assert db_session.query(FinancialExtractionEval).count() == 1
    assert db_session.query(FinancialExtractionCandidate).count() == 0
    assert document.raw_text == "Revenue 100 USD\nNet income 0 USD"
    assert client.get(f"/evaluations/runs/{result['id']}").json()["data"]["report_json"] == report


@pytest.mark.parametrize("change", ["value", "unit", "period", "missing"])
def test_mismatches_reduce_scores_instead_of_passing(client, evaluation_case, change, monkeypatch):
    _simulate_complete_units(monkeypatch)
    _, payload = evaluation_case
    if change == "value": payload["expected"][0]["value"] = 101
    if change == "unit": payload["expected"][0]["unit"] = "INR"
    if change == "period": payload["expected"][0]["fiscal_year"] = 2024
    if change == "missing": payload["expected"].pop()
    response = client.post("/evaluations/runs", json=payload)
    assert response.status_code == 201
    report = response.json()["data"]["report_json"]
    assert report["precision"] == .5
    assert report["recall"] == (1 if change == "missing" else .5)
    assert report["false_positive_count"] == 1


def _simulate_complete_units(monkeypatch):
    """Isolate reference matching, not a claim of actual extractor unit coverage."""
    from app.services import extraction_evaluation
    from app.services.financial_extraction import preview_financial_candidates

    def mock_extractor(document):
        rows = preview_financial_candidates(document)
        for row in rows:
            row.unit = "USD"
        return rows
    monkeypatch.setattr(extraction_evaluation, "preview_financial_candidates", mock_extractor)


def test_exact_reference_matching_preserves_zero_values(client, evaluation_case, monkeypatch):
    _simulate_complete_units(monkeypatch)
    _, payload = evaluation_case
    report = client.post("/evaluations/runs", json=payload).json()["data"]["report_json"]
    assert report["precision"] == report["recall"] == 1
    assert all(row["exact_match"] for row in report["comparisons"])


def test_empty_extraction_is_not_perfect_precision(client, db_session, evaluation_case):
    document, payload = evaluation_case
    document.raw_text = "No financial metrics on this line.\nOther text."
    db_session.commit()
    payload["source_text_sha256"] = sha256(document.raw_text.encode()).hexdigest()
    response = client.post("/evaluations/runs", json=payload)
    report = response.json()["data"]["report_json"]
    assert report["precision"] is None
    assert report["recall"] == 0
    assert report["false_negative_count"] == 2


@pytest.mark.parametrize("change,status", [
    ("stale", 409), ("unreviewed", 422), ("incomplete", 422),
    ("duplicate", 422), ("empty", 422), ("line", 422), ("missing_document", 404),
])
def test_invalid_reference_writes_nothing(client, db_session, evaluation_case, change, status):
    _, payload = evaluation_case
    if change == "stale": payload["source_text_sha256"] = "0" * 64
    if change == "unreviewed": payload["reference_reviewed"] = False
    if change == "incomplete": payload["reference_is_complete"] = False
    if change == "duplicate": payload["expected"].append(payload["expected"][0].copy())
    if change == "empty": payload["expected"] = []
    if change == "line": payload["expected"][0]["source_line_number"] = 100
    if change == "missing_document": payload["document_id"] = 99999
    assert client.post("/evaluations/runs", json=payload).status_code == status
    assert db_session.query(EvaluationRun).count() == 0
    assert db_session.query(FinancialExtractionEval).count() == 0


def test_runs_are_owner_scoped_and_mock_sources_cannot_be_relabelled(client, db_session, evaluation_case):
    _, payload = evaluation_case
    payload["is_mock"] = False
    created = client.post("/evaluations/runs", json=payload).json()["data"]
    assert created["report_json"]["is_mock"] is True
    db_session.add(User(id="other_evaluator", email="other-eval@example.invalid", name="Other"))
    db_session.commit()
    app.dependency_overrides[get_current_user] = lambda: {"id": "other_evaluator"}
    assert client.get("/evaluations/runs").json()["data"] == []
    assert client.get(f"/evaluations/runs/{created['id']}").status_code == 404
