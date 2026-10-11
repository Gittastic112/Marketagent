"""Compare stored suggestions, not facts. No provider calls or database mutations."""
from collections import Counter, defaultdict
from datetime import UTC, datetime
from hashlib import sha256
import json

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, defer, raiseload

from app.models.ai import AiOutput
from app.models.brief_source import BriefSource
from app.models.company import Company
from app.schemas.brief_sources import BriefAnalysis, FIELD_LABELS
from app.schemas.brief_triage import BriefTriageFinding, BriefTriageGroup, BriefTriageRead, BriefTriageSource
from app.services.ai_citations import evaluate_ai_output

SOURCE_LIMIT = 50
IMPORTANCE = {"high": 0, "medium": 1, "low": 2}


def _checked_findings(source: BriefSource, output: AiOutput | None) -> list[BriefTriageFinding] | None:
    """Rebuild from constrained output and its saved exact-span receipts, not stored UI links.

    Source content is immutable. This checks the existing citation receipt, not a
    fresh semantic or source-authenticity evaluation. Full text/PDF stays deferred.
    """
    marker = f"brief_source:{source.id}"
    if (not output or output.user_id != source.user_id or output.reference_type != "brief_source"
            or output.reference_id != source.id or output.is_blocked or output.execution_status != "success"
            or output.source_ids_json != [marker] or output.citation_validation_status != "valid"
            or len(output.output_text) > 30_000):
        return None
    try:
        if not evaluate_ai_output(output)["passed"]:
            return None
        analysis = BriefAnalysis.model_validate_json(output.output_text)
        if analysis.source_marker != f"[source_id:{marker}]":
            return None
        citations = output.citations_json or []
        count = source.extraction_json.get("character_count")
        if type(count) is not int or count < 1:
            return None
        findings = []
        for finding in analysis.findings:
            matching = [c for c in citations if c.get("source_id") == marker and c.get("status") == "valid"
                        and c.get("quote") == finding.quote]
            spans = {(c.get("start_char"), c.get("end_char")) for c in matching}
            if len(spans) != 1:
                return None
            start, end = next(iter(spans))
            if type(start) is not int or type(end) is not int or not (0 <= start < end <= count) or end - start != len(finding.quote):
                return None
            page = next((span["page"] for span in source.extraction_json.get("page_spans", [])
                         if span["start_char"] <= start and end <= span["end_char"]), None)
            findings.append(BriefTriageFinding(**finding.model_dump(), start_char=start, end_char=end, page=page))
        return sorted(findings, key=lambda finding: IMPORTANCE[finding.importance])
    except (ValidationError, ValueError, TypeError, KeyError, AttributeError):
        return None


def compare_sources(db: Session, user_id: str, company_id: int, *, include_mock: bool = False) -> BriefTriageRead:
    company = db.execute(select(Company.name, Company.ticker).where(Company.id == company_id)).first()
    if company is None:
        raise HTTPException(404, "Company not found")
    scope = (BriefSource.user_id == user_id, BriefSource.company_id == company_id)
    counts = dict(db.execute(select(BriefSource.archived_at.is_not(None), func.count())
                            .where(*scope).group_by(BriefSource.archived_at.is_not(None))).all())
    rows = db.execute(select(BriefSource, AiOutput).outerjoin(AiOutput, and_(AiOutput.id == BriefSource.ai_output_id,
            AiOutput.user_id == user_id)).where(*scope, BriefSource.archived_at.is_(None))
        .options(raiseload("*"), defer(BriefSource.analysis_json))
        .order_by(BriefSource.id.desc()).limit(SOURCE_LIMIT)).all()
    excluded: Counter = Counter()
    sources, hashes, refs, unmapped = [], {}, defaultdict(list), []
    now = datetime.now(UTC)
    for source, output in rows:
        if source.analysis_status != "complete":
            excluded[source.analysis_status if source.analysis_status in {"not_scanned", "scanning", "failed"} else "unusable"] += 1
            continue
        findings = _checked_findings(source, output)
        if findings is None:
            excluded["unusable"] += 1
            continue
        if output.human_review_status not in {"pending", "approved"}:
            excluded[output.human_review_status if output.human_review_status in {"rejected", "needs_revision"} else "unusable"] += 1
            continue
        if output.is_mock and not include_mock:
            excluded["mock"] += 1
            continue
        warnings = list(source.extraction_json.get("warnings", []))
        if source.as_of_date is None:
            warnings.append("Source date unknown. Do not infer freshness from upload or scan time.")
        elif source.as_of_date < now.date():
            warnings.append("Historical source, not a current-data timestamp.")
        sources.append(BriefTriageSource(id=source.id, title=source.title, source_kind=source.source_kind,
            as_of_date=source.as_of_date, source_sha256=source.source_sha256, created_at=source.created_at,
            ai_output_id=output.id, provider=output.provider_name, model=output.model_name,
            prompt_version=output.prompt_version, input_hash=output.input_hash, generated_at=output.created_at,
            is_mock=output.is_mock, review_status=output.human_review_status, reviewed_at=output.reviewed_at,
            lifecycle_version=source.lifecycle_version, warnings=warnings, findings=findings))
        hashes[source.id] = source.extraction_json.get("text_sha256") or source.source_sha256
        for finding_index, finding in enumerate(findings):
            if not finding.valuation_inputs:
                unmapped.append({"source_id": source.id, "finding_index": finding_index})
            for suggestion_index, suggestion in enumerate(finding.valuation_inputs):
                refs[suggestion.field].append({"source_id": source.id, "finding_index": finding_index, "suggestion_index": suggestion_index})
    by_id = {source.id: source for source in sources}
    groups = []
    for field, items in refs.items():
        # Never interpret Mock Data and non-mock opposition as a real conflict.
        directions = {False: defaultdict(set), True: defaultdict(set)}
        importance = []
        for item in items:
            source = by_id[item["source_id"]]
            finding = source.findings[item["finding_index"]]
            suggestion = finding.valuation_inputs[item["suggestion_index"]]
            directions[source.is_mock][suggestion.direction].add(hashes[source.id])
            importance.append(finding.importance)
        opposing, mixed = [], False
        for mock, lane in directions.items():
            if lane["increase"] and lane["decrease"]:
                if any(a != b for a in lane["increase"] for b in lane["decrease"]):
                    opposing.append("mock_data" if mock else "stored_sources")
                else:
                    mixed = True
        anchor = "revenue-growth" if field == "revenue_growth_years_json" else field
        groups.append(BriefTriageGroup(field=field, label=FIELD_LABELS[field],
            review_href=f"/companies/{company_id}/valuation/draft#{anchor}",
            status="opposing_directions" if opposing else "mixed_within_content" if mixed else "no_opposition_detected",
            opposition_basis=opposing, source_count=len({item["source_id"] for item in items}),
            distinct_content_count=len({hashes[item["source_id"]] for item in items}),
            highest_importance=min(importance, key=IMPORTANCE.get), items=items))
    order = list(FIELD_LABELS)
    groups.sort(key=lambda group: (group.status != "opposing_directions", IMPORTANCE[group.highest_importance], order.index(group.field)))
    not_examined = max(0, counts.get(False, 0) - len(rows))
    warnings = [
        "Opposing AI suggestions are not a verified contradiction. Check dates, forecast horizons, units and business scope in the originals.",
        "No detected opposition is not agreement or complete coverage. Review-only suggestions have no inferred direction.",
        "Source counts are not independent corroboration. Exact text copies share a content hash when available; syndicated or paraphrased copies may not.",
        "This local comparison makes no AI calls and changes no review status, valuation input or saved model.",
    ]
    if include_mock:
        warnings.append("Mock Data is included explicitly and compared only with other Mock Data, never against non-mock sources.")
    if not_examined:
        warnings.append(f"Only the newest {SOURCE_LIMIT} active sources were examined; {not_examined} older sources are outside this comparison.")
    result = BriefTriageRead(company_id=company_id, company_name=company.name, ticker=company.ticker,
        computed_at=now, include_mock=include_mock, sources=sources, groups=groups, unmapped_findings=unmapped,
        coverage={"active_sources": counts.get(False, 0), "archived_sources": counts.get(True, 0),
            "examined_sources": len(rows), "included_sources": len(sources), "not_examined": not_examined,
            "source_limit": SOURCE_LIMIT, "excluded": dict(excluded)}, warnings=warnings)
    # Hash the bounded evidence and coverage, not wall-clock display warnings or
    # saved dispositions. Lifecycle/review changes invalidate even a restored view.
    basis = result.model_dump(mode="json", exclude={"computed_at", "warnings", "evidence_hash", "reviews"})
    for source in basis["sources"]:
        source.pop("warnings", None)
    basis["owner"] = user_id
    result.evidence_hash = sha256(json.dumps(basis, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return result
