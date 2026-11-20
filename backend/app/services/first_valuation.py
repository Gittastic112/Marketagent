"""Preview and atomically confirm the first version of an owned valuation."""
import json
from types import SimpleNamespace

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from app.models import Company
from app.models.dcf import DcfAssumptionSet, DcfDecisionLog
from app.services.assumption_versions import OUTPUT_FIELDS, _hash
from app.services.dcf import calculate_dcf, require_finite_dcf_result
from app.services.draft_source_proposal import dated_prior_blockers, resolve_selections
from app.services.valuation_context import company_calculation_context
from app.services.valuation_setup_draft import ValuationSetupDraftService as Draft


def attach_sources(db, draft, command):
    db.refresh(draft, with_for_update=True)
    Draft._assert_mutable(draft)
    Draft._assert_version(draft, command.expected_updated_at)
    refs = [item.model_dump() for item in command.selections]
    bindings = resolve_selections(db, draft.company_id, draft.assumptions_json.get("cash_flow_currency"),
                                  command.valuation_date, refs)
    metadata = dict(draft.source_metadata_json or {})
    if refs:
        metadata["dated_source_proposal"] = {"valuation_date": command.valuation_date.isoformat(),
            "knowledge": command.knowledge, "selections": refs, "bindings": bindings}
    else:
        metadata.pop("dated_source_proposal", None)
    draft.source_metadata_json = metadata
    db.commit()
    db.refresh(draft)
    return draft


def _prepare(db, draft, company, command):
    Draft._assert_mutable(draft)
    Draft._assert_version(draft, command.expected_updated_at)
    blockers, diagnostics = [], []
    values = dict(draft.assumptions_json or {})
    metadata = draft.source_metadata_json or {}
    selection = metadata.get("dated_source_proposal") or {}
    refs = selection.get("selections", [])
    bindings = resolve_selections(db, draft.company_id, values.get("cash_flow_currency"), command.valuation_date, refs)
    if refs and (selection["valuation_date"] != command.valuation_date.isoformat() or bindings != selection["bindings"]):
        blockers.append("The selected date or source revision changed. Inspect and apply the sources again.")
    reviewed = set(draft.reviewed_fields_json or [])
    for binding in bindings:
        target = binding["ref"]["target_field"]
        if target == "starting_revenue" and command.model_type == "financial_services":
            blockers.append("Starting revenue does not apply to a financial services model.")
        if binding["status"] == "eligible":
            values[target] = binding["normalized_value"]
            reviewed.add(target)
        else:
            values[target] = None
            blockers.append(binding["reason"])
    effective = SimpleNamespace(assumptions_json=values, source_metadata_json=metadata, reviewed_fields_json=reviewed)
    blockers.extend(Draft._unresolved_fields(effective, command.model_type))
    if Draft._source_basis_changed(db, draft, company, command.model_type):
        blockers.append("Draft sources or review requirements changed. Refresh and review the draft.")
    used = {k for k,v in values.items() if v is not None} - {r["target_field"] for r in refs}
    if command.model_type == "financial_services":
        used &= set(metadata.get("required_fields_by_model", {}).get("financial_services", [])) | {"current_market_price"}
    blockers.extend(dated_prior_blockers(db, draft, company.id, command.valuation_date, used))
    inputs, excluded, summary = {}, [], None
    if not blockers:
        try:
            inputs, excluded = Draft.calculation_inputs(values, command.model_type)
            output, projections, _ = calculate_dcf(DcfAssumptionSet(id=0, **inputs),
                model_type=command.model_type, include_sensitivity=False, **company_calculation_context(company))
            require_finite_dcf_result(output, projections, command.model_type)
            diagnostics = output.warnings_json or []
            blockers.extend(w.get("message") or "Blocking valuation diagnostic" for w in diagnostics
                            if w.get("severity") in {"critical", "blocking"})
            if not blockers:
                summary = {key: getattr(output, key) for key in OUTPUT_FIELDS}
        except HTTPException as exc:
            blockers.append(str(exc.detail))
        except (ValueError, ArithmeticError):
            blockers.append("The proposed valuation cannot produce a finite result. Review the inputs.")
    settings = command.model_dump(mode="json", exclude={"reason", "submission_id", "preview_hash"})
    basis = {"draft": draft.id, "settings": settings, "assumptions": values, "reviewed": sorted(reviewed),
             "provenance": draft.provenance_json, "source_metadata": metadata, "bindings": bindings,
             "classification": company_calculation_context(company), "blockers": blockers, "diagnostics": diagnostics,
             "proposed_output": summary}
    return dict(draft_id=draft.id, valuation_date=command.valuation_date, preview_hash=_hash(basis),
                ready=not blockers and summary is not None, blockers=blockers, assumptions=values,
                sources=bindings, diagnostics=diagnostics, proposed_output=summary,
                currency=values.get("cash_flow_currency")), inputs, excluded


def preview_first_model(db, draft, command):
    return _prepare(db, draft, db.get(Company, draft.company_id), command)[0]


def confirm_first_model(db, draft, command):
    # Financial publication takes the company lock first. Both transactions use the
    # same order, including when a newer eligible revision has the same value.
    company = db.scalar(select(Company).where(Company.id == draft.company_id).with_for_update()
                        .execution_options(populate_existing=True))
    db.refresh(draft, with_for_update=True)
    request_hash = _hash(command.model_dump(mode="json"))
    key = f"version_save:{command.submission_id}"
    if draft.promoted_model_id:
        receipt = db.scalar(select(DcfDecisionLog).where(
            DcfDecisionLog.valuation_model_id == draft.promoted_model_id, DcfDecisionLog.decision_type == key))
        if receipt:
            stored = json.loads(receipt.user_note or "{}")
            if stored.get("draft_id") == draft.id and stored.get("request_hash") == request_hash:
                return dict(model_id=draft.promoted_model_id, assumption_set_id=receipt.assumption_set_id, replayed=True)
        raise HTTPException(409, "This draft was already saved with a different submission.")
    preview, inputs, excluded = _prepare(db, draft, company, command)
    if not preview["ready"]:
        raise HTTPException(409, "Resolve the first-model preview: " + ", ".join(preview["blockers"]))
    if preview["preview_hash"] != command.preview_hash:
        raise HTTPException(409, "The first-model preview changed or has unresolved inputs. Preview again.")
    snapshot = {"draft_id": draft.id, "request_hash": request_hash, "previous_assumption_set_id": None,
                "valuation_date": command.valuation_date.isoformat(), "preview_hash": command.preview_hash,
                "reason": command.reason, "sources": preview["sources"], "knowledge": command.knowledge,
                "assumption_provenance": jsonable_encoder(draft.provenance_json or {})}
    for source in preview["sources"]:
        field = source["ref"]["target_field"]
        snapshot["assumption_provenance"][field] = {"source_type": "dated_financial_revision", "binding": source}
    model, assumption_id = Draft.store_first_model(db, draft, company, command.name, command.description,
        command.model_type, inputs, excluded, (key, snapshot))
    return dict(model_id=model.id, assumption_set_id=assumption_id, replayed=False)
