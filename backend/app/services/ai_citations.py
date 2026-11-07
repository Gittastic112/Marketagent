import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.ai import AiOutput
from app.models.raw_document import RawDocument
from app.services.ai_claim_review import review_claim_literals


PROHIBITED_RECOMMENDATION_PATTERNS = (
    re.compile(r"\b(?:buy|sell)\s+(?:this|the|shares?|stock)\b", re.IGNORECASE),
    re.compile(r"\byou should (?:buy|sell)\b", re.IGNORECASE),
    re.compile(r"\bguaranteed (?:upside|return|profit)\b", re.IGNORECASE),
    re.compile(r"\bstrong (?:buy|sell)\b", re.IGNORECASE),
    re.compile(r"\b(?:must|need to) (?:buy|sell)\b", re.IGNORECASE),
)

def extract_source_ids(text: str) -> list[str]:
    """Extracts all unique source IDs from [source_id:X] patterns in the text."""
    pattern = re.compile(r"\[source_id:([^\]]+)\]")
    return list(dict.fromkeys(value.strip() for value in pattern.findall(text or "") if value.strip()))



def _validate_document_citation(
    db: Session,
    citation: dict[str, Any],
    owner_id: str | None = None,
) -> dict[str, Any]:
    source_id = str(citation.get("source_id") or "")
    try:
        document_id = int(source_id.split(":", 1)[1])
    except (IndexError, ValueError):
        return {**citation, "status": "invalid", "reason": "Unsupported source identifier"}
    if source_id.startswith("brief_source:"):
        from app.models.brief_source import BriefSource
        source = db.get(BriefSource, document_id)
        text = source.content_text if source and owner_id is not None and source.user_id == owner_id else None
        href = f"/daily-brief/sources/{document_id}"
    else:
        document = db.get(RawDocument, document_id)
        text = document.raw_text if document else None
        href = f"/documents/{document_id}/sections"
    if not text:
        return {**citation, "status": "invalid", "reason": "Stored source text is unavailable"}

    quote = str(citation.get("quote") or "")
    if not quote.strip():
        return {**citation, "status": "invalid", "reason": "A nonempty exact quote is required"}
    start_char = citation.get("start_char")
    end_char = citation.get("end_char")
    if start_char is None and end_char is None:
        first = text.find(quote)
        if first < 0:
            return {**citation, "status": "invalid", "reason": "Quote was not found in stored source text"}
        if text.find(quote, first + 1) >= 0:
            return {**citation, "status": "invalid", "reason": "Quote is not unique; provide exact character offsets"}
        start_char = first
        end_char = first + len(quote)
    if not isinstance(start_char, int) or not isinstance(end_char, int):
        return {**citation, "status": "invalid", "reason": "Character offsets are invalid"}
    if start_char < 0 or end_char <= start_char or end_char > len(text):
        return {**citation, "status": "invalid", "reason": "Character offsets exceed stored source text"}
    if text[start_char:end_char] != quote:
        return {**citation, "status": "invalid", "reason": "Quote does not match the exact source span"}
    return {
        **citation,
        "start_char": start_char,
        "end_char": end_char,
        "status": "valid",
        "reason": None,
        "internal_href": href,
    }


def validate_ai_citations(
    db: Session,
    output: AiOutput,
    citations: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    declared_sources = set(output.source_ids_json or [])
    referenced_sources = set(extract_source_ids(output.output_text or ""))
    results: list[dict[str, Any]] = []
    for citation in citations:
        source_id = str(citation.get("source_id") or "")
        if source_id not in declared_sources:
            results.append({**citation, "status": "invalid", "reason": "Source was not declared for this AI output"})
            continue
        if source_id not in referenced_sources:
            results.append({**citation, "status": "invalid", "reason": "Source is not cited in the AI output text"})
            continue
        if source_id.startswith(("raw_document:", "brief_source:")):
            results.append(_validate_document_citation(db, citation, output.user_id))
            continue
        results.append({**citation, "status": "invalid", "reason": "This source type has no exact-text validator"})

    validated_sources = {
        str(result.get("source_id")) for result in results if result.get("status") == "valid"
    }
    for source_id in sorted(referenced_sources - validated_sources):
        if any(str(result.get("source_id")) == source_id for result in results):
            continue
        results.append(
            {
                "source_id": source_id,
                "quote": "",
                "start_char": None,
                "end_char": None,
                "status": "invalid",
                "reason": "No validated exact-text citation was supplied for this output source marker",
            }
        )
    if declared_sources and not referenced_sources:
        results.append(
            {
                "source_id": "",
                "quote": "",
                "start_char": None,
                "end_char": None,
                "status": "invalid",
                "reason": "Source-backed AI output contains no [source_id:...] markers",
            }
        )

    valid_count = sum(result["status"] == "valid" for result in results)
    if valid_count == len(results) and results:
        status = "valid"
    elif valid_count:
        status = "partial"
    else:
        status = "invalid"
    if output.human_review_status == "approved" and results != (output.citations_json or []):
        history = dict(output.evaluation_json or {})
        history["prior_human_reviews"] = [*history.get("prior_human_reviews", []), {
            "status": output.human_review_status, "notes": output.review_notes,
            "reviewer_id": output.reviewer_id,
            "reviewed_at": output.reviewed_at.isoformat() if output.reviewed_at else None,
            "reason": "Citation evidence changed; renewed human review is required.",
        }]
        output.evaluation_json = history
        output.human_review_status = "pending"
        output.reviewer_id = None
        output.reviewed_at = None
    output.citations_json = results
    output.citation_validation_status = status
    output.evaluation_json = evaluate_ai_output(output)
    output.is_blocked = not output.evaluation_json["passed"]
    db.commit()
    db.refresh(output)
    return results, status


def evaluate_ai_output(output: AiOutput) -> dict[str, Any]:
    recommendation_matches = [
        pattern.pattern
        for pattern in PROHIBITED_RECOMMENDATION_PATTERNS
        if pattern.search(output.output_text or "")
    ]
    citations_required = bool(output.source_ids_json) and output.execution_status == "success"
    referenced_sources = set(extract_source_ids(output.output_text or ""))
    declared_sources = set(output.source_ids_json or [])
    validated_sources = {
        str(citation.get("source_id"))
        for citation in (output.citations_json or [])
        if citation.get("status") == "valid"
    }
    checks = {
        "execution_succeeded": output.execution_status == "success",
        "output_nonempty": bool((output.output_text or "").strip()),
        "no_recommendation_language": not recommendation_matches,
        "citations_required": citations_required,
        "source_markers_present": not citations_required or bool(referenced_sources),
        "source_markers_declared": referenced_sources.issubset(declared_sources),
        "citation_source_coverage": not citations_required or referenced_sources.issubset(validated_sources),
        "citations_valid": not citations_required or output.citation_validation_status == "valid",
    }
    passed = all(
        value
        for key, value in checks.items()
        if key != "citations_required"
    )
    return {
        "version": "ai-output-eval-v4",
        # Generation provenance is immutable even when citation/review checks change.
        **({"valuation_basis": output.evaluation_json["valuation_basis"]}
           if isinstance(output.evaluation_json, dict) and "valuation_basis" in output.evaluation_json else {}),
        **({"prior_human_reviews": output.evaluation_json["prior_human_reviews"]}
           if isinstance(output.evaluation_json, dict) and "prior_human_reviews" in output.evaluation_json else {}),
        "evaluation_scope": "citation_and_policy_checks_only",
        "interpretation_quality": "not_evaluated",
        "claim_review": review_claim_literals(output.output_text or "", output.citations_json or []),
        "limitations": [
            "Exact source spans and recommendation-language checks do not validate numeric accuracy, period alignment, causal claims or source-text instructions.",
            "Human review of interpretation is separate and is never granted by these automated checks.",
        ],
        "passed": passed,
        "checks": checks,
        "recommendation_pattern_matches": recommendation_matches,
        "referenced_source_ids": sorted(referenced_sources),
        "validated_source_ids": sorted(validated_sources),
        "missing_validated_source_ids": sorted(referenced_sources - validated_sources),
    }
