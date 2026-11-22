"""Resolve an analyst's explicit dated selection from preserved company evidence."""
from math import isfinite

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from app.models import FinancialExtractionCandidate, RawDocument, SourceFactRevision
from app.services.dated_financial_inputs import dated_financial_inputs
from app.services.assumption_versions import _hash

# Composite bridge inputs require separate evidence for their full economic scope.
# Do not infer that scope from the name of an extracted component.
SUPPORTED = {"starting_revenue": ("revenue", "annual"), "net_income": ("net_income", "annual")}
REVENUE_CONCEPTS = {"Revenues", "SalesRevenueNet", "RevenueFromContractWithCustomerExcludingAssessedTax"}


def resolve_selections(db, company_id, currency, day, selections):
    if not selections:
        return []
    report = dated_financial_inputs(db, company_id, valuation_date=day)
    rows = {row["metric"]: row for row in report["rows"]}
    result = []
    for ref in selections:
        target = ref["target_field"]
        metric, scope = SUPPORTED.get(target, (target, None))
        row = rows.get(metric) or {}
        item = next((s for s in row.get("sources", []) if s["revision_id"] == ref["id"]), None)
        binding = {"ref": ref, "company_id": company_id, "metric": metric, "valuation_date": day.isoformat(),
                   "knowledge": "available_by_date", "timezone": "America/New_York", "status": "held"}
        result.append(binding)
        if item is None:
            binding["reason"] = f"{target}: the chosen revision is unavailable for this company, metric or period."
            continue
        binding["source"] = jsonable_encoder(item)
        candidate = db.get(FinancialExtractionCandidate, item["candidate_id"])
        document = db.get(RawDocument, item["document_id"])
        revision = db.get(SourceFactRevision, ref["id"])
        if not candidate or not document or not revision or candidate.raw_document_id != document.id:
            binding["reason"] = f"{target}: the source and candidate identities disagree."
            continue
        locator, period = item["locator"], item["period"]
        binding.update(document_hash=document.content_hash, review_status=candidate.review_status,
                       review_value=revision.value, claim_type=item["claim_type"])
        if not scope:
            binding["reason"] = f"{target}: this component has no verified mapping to the complete model input."
        elif report["truncated"] or row["status"] != "available" or row["selected_revision_id"] != ref["id"]:
            binding["reason"] = f"{target}: the selected revision conflicts with or has been replaced by other eligible evidence."
        elif item["claim_type"] == "User Assumption":
            binding["reason"] = f"{target}: this revision contains an analyst override. Record its rationale as an explicit assumption."
        elif candidate.review_status != "promoted" or item["availability"] != "available_by_date":
            binding["reason"] = f"{target}: the revision requires review or was unavailable on the selected date."
        elif (period.get("scope") != scope or not period.get("start") or not period.get("duration_days")
              or not 350 <= period["duration_days"] <= 380 or period.get("end_basis") != "source"
              or not period.get("accounting_basis") or str(period.get("end")) != str(row["effective_at"])):
            binding["reason"] = f"{target}: the original needs a complete annual period and accounting basis."
        elif (locator.get("dimensions") or locator.get("segment") or
              not (locator.get("consolidation_scope") == "consolidated" or
                   (document.document_type == "xbrl_facts" and locator.get("type") == "xbrl_fact"
                    and locator.get("concept") in (REVENUE_CONCEPTS if target == "starting_revenue" else {"NetIncomeLoss"})))):
            binding["reason"] = f"{target}: the original does not establish a consolidated company total."
        elif row["normalized_unit"] != currency or row["normalized_value"] is None or not isfinite(row["normalized_value"]):
            binding["reason"] = f"{target}: the amount must convert to full units in the model currency."
        else:
            binding.update(status="eligible", normalized_value=row["normalized_value"], normalized_unit=currency,
                           conversion=row["conversion"])
        binding["fingerprint"] = _hash(binding)
    return result


def _benchmark_sources(provenance):
    if not isinstance(provenance, dict):
        return
    kind = provenance.get("source_type")
    if kind in {"industry_benchmark", "industry_benchmark_blend", "damodaran_benchmark", "damodaran_methodology"} or (
        kind == "methodology_engine" and provenance.get("dataset_file_id") is not None
    ):
        yield provenance
    for leg in (provenance.get("projection_basis") or {}).values():
        if isinstance(leg, dict):
            yield from _benchmark_sources(leg.get("source"))


def _published_datasets(db, provenance, day):
    from app.models import DamodaranDatasetFile

    module = provenance.get("benchmark_module")
    groups = provenance.get("source_summary") or [provenance]
    if not isinstance(groups, list):
        return False
    for group in groups:
        if not isinstance(group, dict):
            return False
        sources = [item for item in group.get("sources", [group]) if isinstance(item, dict)
                   and (module is None or item.get("module") == module)]
        if not sources:
            return False
        for source in sources:
            dataset_id = source.get("dataset_file_id")
            dataset = db.get(DamodaranDatasetFile, dataset_id) if dataset_id else None
            if (not dataset or not dataset.source_sha256 or not dataset.publication_source
                    or not dataset.publication_date or dataset.publication_date > day):
                return False
    return True


def _published_weights(db, company_id, day):
    from datetime import datetime
    from app.models import CompanyIndustryMix
    from app.schemas.publication import document_publication
    from app.services.dated_financial_inputs import RESEARCH_ZONE

    mix = db.scalar(select(CompanyIndustryMix).where(CompanyIndustryMix.company_id == company_id))
    if not mix or not mix.as_of_date or mix.as_of_date > day or not mix.source_document_id:
        return False
    doc = db.get(RawDocument, mix.source_document_id)
    if not doc or doc.company_id != company_id:
        return False
    meta = doc.raw_payload_json or {}
    published = document_publication(doc.published_at, doc.document_type, meta.get("source_kind"),
                                     meta.get("publication_precision"))
    publication_day = published.astimezone(RESEARCH_ZONE).date() if isinstance(published, datetime) else published
    return publication_day is not None and publication_day <= day


def dated_prior_blockers(db, draft, company_id, day, used_fields):
    problems = []
    for field in sorted(used_fields):
        inputs = list(_benchmark_sources((draft.provenance_json or {}).get(field)))
        if any(not _published_datasets(db, source, day) for source in inputs):
            problems.append(f"{field}: benchmark publication by the valuation date is unverified. Review a dated source or enter an explicit assumption.")
        if any(source.get("source_type") == "industry_benchmark_blend" for source in inputs):
            if not _published_weights(db, company_id, day):
                problems.append(f"{field}: the industry weights lack a matching original available by the valuation date.")
    return problems
