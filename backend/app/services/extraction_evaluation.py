"""Bounded local extraction evaluation against explicitly reviewed reference rows.

No provider calls, candidate promotion, or modifications to source documents.
Scores describe agreement with User Assumptions, not independent certification.
"""
from datetime import UTC, datetime
from hashlib import sha256
import json
from math import isclose, isfinite

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import RawDocument
from app.models.evaluation import EvaluationRun, FinancialExtractionEval
from app.schemas.evaluation import FinancialEvaluationCreate
from app.services.financial_extraction import EXTRACTION_METHOD, preview_financial_candidates

EVALUATOR_VERSION = "financial-reference-v1"


def document_basis(db: Session, document_id: int) -> tuple[RawDocument, dict]:
    document = db.get(RawDocument, document_id)
    if document is None:
        raise HTTPException(404, "Source document not found.")
    if not document.raw_text or document.company_id is None:
        raise HTTPException(422, "A company-linked document with stored text is required.")
    if len(document.raw_text.encode("utf-8")) > 1_000_000:
        raise HTTPException(413, "Evaluation supports at most 1 MB of source text.")
    metadata = document.raw_payload_json or {}
    mock = bool(metadata.get("is_mock")) or "mock data" in (
        f"{document.title} {document.source.name if document.source else ''}".lower())
    return document, {
        "document_id": document.id, "title": document.title,
        "source_text_sha256": sha256(document.raw_text.encode("utf-8")).hexdigest(),
        "source_content_hash": document.content_hash,
        "line_count": len(document.raw_text.splitlines()),
        "extractor_version": EXTRACTION_METHOD, "is_mock": mock,
    }


def execute_financial_evaluation(db: Session, user_id: str, request: FinancialEvaluationCreate) -> EvaluationRun:
    document, basis = document_basis(db, request.document_id)
    if basis["source_text_sha256"] != request.source_text_sha256:
        raise HTTPException(409, "Source text changed. Reload its basis and review the reference again.")
    if any(row.source_line_number > basis["line_count"] for row in request.expected):
        raise HTTPException(422, "A reference source line falls outside the stored document.")
    started = datetime.now(UTC)
    predicted = preview_financial_candidates(document)
    if len(predicted) > 2_000:
        raise HTTPException(413, "Evaluation supports at most 2,000 extracted candidates.")
    expected = {(row.metric_code, row.source_line_number): row for row in request.expected}
    used = set()
    matches = units = periods = locators = numeric = 0
    details = []
    for candidate in predicted:
        key = (candidate.metric_code, candidate.source_line_number)
        reference = expected.get(key) if key not in used else None
        if reference is not None:
            used.add(key)
        value_ok = reference is not None and isfinite(candidate.value) and isclose(
            candidate.value, reference.value, rel_tol=1e-9, abs_tol=1e-9)
        unit_ok = reference is not None and (candidate.unit or "").strip().casefold() == reference.unit.casefold()
        period_ok = reference is not None and candidate.fiscal_year == reference.fiscal_year and candidate.period_type == reference.period_type
        locator_ok = reference is not None
        exact = value_ok and unit_ok and period_ok and locator_ok
        matches += int(exact)
        numeric += int(value_ok)
        units += int(unit_ok)
        periods += int(period_ok)
        locators += int(locator_ok)
        details.append({"metric_code": candidate.metric_code, "source_line_number": candidate.source_line_number,
            "value_matches": value_ok, "unit_matches": unit_ok, "period_matches": period_ok,
            "locator_matches": locator_ok, "exact_match": exact})
    count = len(predicted)
    rate = lambda successes: successes / count if count else None
    reference_rows = [row.model_dump(mode="json") for row in request.expected]
    reference_hash = sha256(json.dumps(reference_rows, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    report = {**basis, "evaluator_version": EVALUATOR_VERSION,
        "reference_sha256": reference_hash, "reference": reference_rows,
        "reference_reviewed": True, "reference_is_complete": True,
        "claim_type": "Calculation", "reference_claim_type": "User Assumption",
        "is_mock": request.is_mock or basis["is_mock"], "predicted_count": count,
        "expected_count": len(expected), "true_positive_count": matches,
        "false_positive_count": count - matches, "false_negative_count": len(expected) - matches,
        "precision": rate(matches), "recall": matches / len(expected),
        "numeric_accuracy": rate(numeric), "unit_accuracy": rate(units),
        "period_accuracy": rate(periods), "source_locator_accuracy": rate(locators),
        "comparisons": details,
        "formula": "Exact match requires metric, source line, value (1e-9 tolerance), unit and period. Precision = exact matches / predictions; recall = exact matches / reference rows. Other accuracies use all predictions as denominator.",
        "limitations": [
            "Reference completeness and correctness are asserted by the reviewer, not independently verified.",
            "Evaluates the local text-line extractor only, not PDF layout, XBRL, normalization, AI or investment outcomes.",
            "Missing extraction units count as errors; no unit or currency is inferred for evaluation.",
            "No predictions means unavailable precision, not perfect precision.",
        ]}
    run = EvaluationRun(user_id=user_id, run_name=request.run_name, evaluation_type="financial_extraction",
        status="completed", created_at=started, completed_at=datetime.now(UTC), report_json=report)
    db.add(run)
    db.flush()
    db.add(FinancialExtractionEval(evaluation_run_id=run.id, document_id=document.id,
        precision=report["precision"], recall=report["recall"], unit_accuracy=report["unit_accuracy"],
        period_accuracy=report["period_accuracy"], source_locator_accuracy=report["source_locator_accuracy"],
        manual_intervention_count=0))
    db.commit()
    db.refresh(run)
    return run
