from __future__ import annotations
from datetime import UTC, date, datetime
from typing import Any
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.models import Company, PeerValuationMemberRecord, PeerValuationRevisionMemberRecord, PeerValuationRevisionTargetProfile, PeerValuationSet, PeerValuationSetRevision, PeerValuationTargetProfile
from app.schemas.peer_valuation import (PEER_MULTIPLE_METHODS, MAXIMUM_PEER_MEMBERS, PeerMultiplesInput, PeerMemberInput, PeerTargetContextInput, PeerValuationSetCreate, PeerValuationSetUpdate, PeerValuationSetReview, PeerValuationSetMutation)
from app.services.peer_diagnostics import (MINIMUM_METHOD_PEERS, PEER_SOURCE_STALE_DAYS, PEER_SOURCE_DATE_SPAN_WARNING_DAYS, PEER_MULTIPLE_RATIO_WARNING, PEER_RELATIVE_MAD_WARNING, PEER_FISCAL_PERIOD_SPAN_WARNING_DAYS, PEER_MARKET_CAP_RATIO_WARNING, PEER_GROWTH_SPAN_WARNING_PCT, PEER_MARGIN_SPAN_WARNING_PCT, calculate_peer_aggregates, _source_date, _market_cap_context, calculate_peer_diagnostics, peer_review_receipt, peer_review_receipt_matches)

def _member_dict(member: PeerMemberInput) -> dict[str, Any]:
    return member.model_dump(mode="json", exclude_none=True)


def _target_dict(target: PeerTargetContextInput | None) -> dict[str, Any]:
    return target.model_dump(mode="json", exclude_none=True) if target else {}


def _target_record_kwargs(target: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_name": target["sourceName"],
        "source_url": target["sourceUrl"],
        "source_as_of": _source_date(target["sourceAsOf"]),
        "claim_type": target["claimType"],
        "notes": target.get("notes"),
        "country": target.get("country"),
        "currency": target.get("currency"),
        "fiscal_period_end": _source_date(target.get("fiscalPeriodEnd")),
        "accounting_standard": target.get("accountingStandard"),
        "market_cap": target.get("marketCap"),
        "revenue_growth_pct": target.get("revenueGrowthPct"),
        "ebitda_margin_pct": target.get("ebitdaMarginPct"),
    }


def _target_from_record(
    record: PeerValuationTargetProfile | PeerValuationRevisionTargetProfile,
) -> dict[str, Any]:
    target = {
        "sourceName": record.source_name,
        "sourceUrl": record.source_url,
        "sourceAsOf": record.source_as_of.isoformat(),
        "claimType": record.claim_type,
        "notes": record.notes,
        "country": record.country,
        "currency": record.currency,
        "fiscalPeriodEnd": (
            record.fiscal_period_end.isoformat() if record.fiscal_period_end else None
        ),
        "accountingStandard": record.accounting_standard,
        "marketCap": record.market_cap,
        "revenueGrowthPct": record.revenue_growth_pct,
        "ebitdaMarginPct": record.ebitda_margin_pct,
    }
    return {key: value for key, value in target.items() if value is not None}


def _record_kwargs(member: dict[str, Any], *, ordinal: int) -> dict[str, Any]:
    multiples = member.get("multiples") or {}
    return {
        "ordinal": ordinal,
        "identifier": member["identifier"],
        "peer_company_id": member.get("companyId"),
        "name": member.get("name"),
        "included": member.get("included", True),
        **{method: multiples.get(method) for method in PEER_MULTIPLE_METHODS},
        "source_name": member.get("sourceName"),
        "source_url": member.get("sourceUrl"),
        "source_as_of": _source_date(member.get("sourceAsOf")),
        "claim_type": member.get("claimType"),
        "notes": member.get("notes"),
        "country": member.get("country"),
        "currency": member.get("currency"),
        "fiscal_period_end": _source_date(member.get("fiscalPeriodEnd")),
        "accounting_standard": member.get("accountingStandard"),
        "market_cap": member.get("marketCap"),
        "revenue_growth_pct": member.get("revenueGrowthPct"),
        "ebitda_margin_pct": member.get("ebitdaMarginPct"),
    }


def _member_from_record(
    record: PeerValuationMemberRecord | PeerValuationRevisionMemberRecord,
) -> dict[str, Any]:
    member: dict[str, Any] = {
        "identifier": record.identifier,
        "companyId": record.peer_company_id,
        "name": record.name,
        "included": record.included,
        "multiples": {
            method: getattr(record, method)
            for method in PEER_MULTIPLE_METHODS
            if getattr(record, method) is not None
        },
        "sourceName": record.source_name,
        "sourceUrl": record.source_url,
        "sourceAsOf": record.source_as_of.isoformat() if record.source_as_of else None,
        "claimType": record.claim_type,
        "notes": record.notes,
        "country": record.country,
        "currency": record.currency,
        "fiscalPeriodEnd": (
            record.fiscal_period_end.isoformat() if record.fiscal_period_end else None
        ),
        "accountingStandard": record.accounting_standard,
        "marketCap": record.market_cap,
        "revenueGrowthPct": record.revenue_growth_pct,
        "ebitdaMarginPct": record.ebitda_margin_pct,
    }
    return {key: value for key, value in member.items() if value is not None}


def _sync_current_member_records(
    db: Session,
    peer_set: PeerValuationSet,
    members: list[dict[str, Any]],
) -> None:
    for record in list(peer_set.member_records):
        db.delete(record)
    peer_set.member_records = []
    db.flush()
    peer_set.member_records = [
        PeerValuationMemberRecord(**_record_kwargs(member, ordinal=ordinal))
        for ordinal, member in enumerate(members)
    ]


def _sync_revision_member_records(
    revision: PeerValuationSetRevision,
    members: list[dict[str, Any]],
) -> None:
    revision.member_records = [
        PeerValuationRevisionMemberRecord(**_record_kwargs(member, ordinal=ordinal))
        for ordinal, member in enumerate(members)
    ]


def _sync_current_target_profile(
    db: Session,
    peer_set: PeerValuationSet,
    target: dict[str, Any],
) -> None:
    if peer_set.target_profile is not None:
        db.delete(peer_set.target_profile)
        peer_set.target_profile = None
        db.flush()
    if target:
        peer_set.target_profile = PeerValuationTargetProfile(**_target_record_kwargs(target))


def _sync_revision_target_profile(
    revision: PeerValuationSetRevision,
    target: dict[str, Any],
) -> None:
    if target:
        revision.target_profile = PeerValuationRevisionTargetProfile(
            **_target_record_kwargs(target)
        )


def _storage_consistency(
    json_members: list[dict[str, Any]],
    normalized_members: list[dict[str, Any]],
) -> dict[str, Any]:
    def canonical(member: dict[str, Any]) -> dict[str, Any]:
        compact = {key: value for key, value in member.items() if value is not None}
        compact["included"] = compact.get("included", True)
        compact["multiples"] = {
            key: value
            for key, value in (compact.get("multiples") or {}).items()
            if value is not None
        }
        return compact

    canonical_json = [canonical(member) for member in json_members]
    canonical_normalized = [canonical(member) for member in normalized_members]
    if not normalized_members and json_members:
        return {
            "status": "legacy_json_only",
            "jsonMemberCount": len(json_members),
            "normalizedMemberCount": 0,
        }
    return {
        "status": "consistent" if canonical_normalized == canonical_json else "mismatch",
        "jsonMemberCount": len(json_members),
        "normalizedMemberCount": len(normalized_members),
    }


def peer_set_members(peer_set: PeerValuationSet) -> list[dict[str, Any]]:
    normalized_members = [_member_from_record(record) for record in peer_set.member_records]
    return normalized_members or (peer_set.peer_identifiers_json or [])


def peer_set_storage_consistency(peer_set: PeerValuationSet) -> dict[str, Any]:
    return _storage_consistency(
        peer_set.peer_identifiers_json or [],
        [_member_from_record(record) for record in peer_set.member_records],
    )


def _target_storage_consistency(
    json_target: dict[str, Any],
    normalized_target: dict[str, Any],
) -> dict[str, Any]:
    if json_target and not normalized_target:
        status = "legacy_json_only"
    elif json_target == normalized_target:
        status = "consistent"
    else:
        status = "mismatch"
    return {
        "status": status,
        "jsonTargetPresent": bool(json_target),
        "normalizedTargetPresent": bool(normalized_target),
    }


def peer_set_target_context(peer_set: PeerValuationSet) -> dict[str, Any] | None:
    normalized = _target_from_record(peer_set.target_profile) if peer_set.target_profile else {}
    return normalized or (peer_set.target_context_json or {}) or None


def peer_set_target_storage_consistency(peer_set: PeerValuationSet) -> dict[str, Any]:
    normalized = _target_from_record(peer_set.target_profile) if peer_set.target_profile else {}
    return _target_storage_consistency(peer_set.target_context_json or {}, normalized)


def _validate_members(
    db: Session,
    *,
    target_company_id: int,
    members: list[PeerMemberInput],
) -> None:
    identifiers: set[str] = set()
    for member in members:
        if member.identifier in identifiers:
            raise HTTPException(
                status_code=422,
                detail=f"Duplicate peer identifier: {member.identifier}",
            )
        identifiers.add(member.identifier)
        if member.companyId is None:
            continue
        if member.companyId == target_company_id:
            raise HTTPException(status_code=422, detail="Target company cannot be its own peer")
        if db.get(Company, member.companyId) is None:
            raise HTTPException(
                status_code=422,
                detail=f"Peer company {member.companyId} was not found",
            )


def peer_set_calculation_eligibility(
    peer_set: PeerValuationSet,
    *,
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Peer evidence eligibility only; company financial inputs are checked at run time."""
    members = peer_set_members(peer_set)
    diagnostics = diagnostics or calculate_peer_diagnostics(
        members, target_context=peer_set_target_context(peer_set),
    )
    receipt_missing = (
        not peer_set.review_diagnostics_sha256
        or peer_set.review_warning_codes_json is None
        or peer_set.review_diagnostics_as_of is None
    )
    receipt_status = "missing" if receipt_missing else (
        "current" if peer_review_receipt_matches(
            diagnostics_sha256=peer_set.review_diagnostics_sha256,
            warning_codes=peer_set.review_warning_codes_json,
            diagnostics_as_of=peer_set.review_diagnostics_as_of,
            current_diagnostics=diagnostics,
        ) else "stale"
    )
    blockers: list[str] = []
    if not peer_set.is_active:
        blockers.append("archived")
    if peer_set.review_status != "reviewed":
        blockers.append("review_required")
    if peer_set_storage_consistency(peer_set)["status"] == "mismatch":
        blockers.append("member_storage_mismatch")
    if peer_set_target_storage_consistency(peer_set)["status"] == "mismatch":
        blockers.append("target_storage_mismatch")
    if receipt_status != "current":
        blockers.append(f"receipt_{receipt_status}")
    usable_methods = [
        method for method, result in calculate_peer_aggregates(members)["methods"].items()
        if result["multiple"] is not None
    ]
    if not usable_methods:
        blockers.append("insufficient_method_coverage")
    return {
        "canCalculate": not blockers,
        "receiptStatus": receipt_status,
        "usableMethods": usable_methods,
        "blockers": blockers,
        "asOf": diagnostics["asOf"],
    }


def _owned_set(db: Session, peer_set_id: int, user_id: str) -> PeerValuationSet:
    peer_set = db.scalar(
        select(PeerValuationSet).where(
            PeerValuationSet.id == peer_set_id,
            PeerValuationSet.user_id == user_id,
        )
    )
    if peer_set is None:
        raise HTTPException(status_code=404, detail="Peer valuation set not found")
    return peer_set


def _require_version(peer_set: PeerValuationSet, expected_version: int) -> None:
    if peer_set.version != expected_version:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Peer valuation set changed from version {expected_version} "
                f"to {peer_set.version}; reload before saving."
            ),
        )


def _record_revision(
    db: Session,
    *,
    peer_set: PeerValuationSet,
    action: str,
    changed_fields: list[str],
) -> PeerValuationSetRevision:
    revision = PeerValuationSetRevision(
        peer_set_id=peer_set.id,
        user_id=peer_set.user_id,
        version=peer_set.version,
        action=action,
        changed_fields_json=changed_fields,
        name=peer_set.name,
        notes=peer_set.notes,
        is_active=peer_set.is_active,
        review_status=peer_set.review_status,
        reviewed_at=peer_set.reviewed_at,
        reviewed_by_user_id=peer_set.reviewed_by_user_id,
        review_diagnostics_sha256=peer_set.review_diagnostics_sha256,
        review_warning_codes_json=peer_set.review_warning_codes_json,
        review_diagnostics_as_of=peer_set.review_diagnostics_as_of,
        aggregation_method=peer_set.aggregation_method,
        members_json=peer_set.peer_identifiers_json or [],
        target_context_json=peer_set.target_context_json or {},
        aggregate_metrics_json=peer_set.aggregate_metrics_json or {},
    )
    db.add(revision)
    db.flush()
    _sync_revision_member_records(revision, peer_set.peer_identifiers_json or [])
    _sync_revision_target_profile(revision, peer_set.target_context_json or {})
    return revision


def peer_set_revision_response(revision: PeerValuationSetRevision) -> dict[str, Any]:
    json_members = revision.members_json or []
    normalized_members = [_member_from_record(record) for record in revision.member_records]
    members = normalized_members or json_members
    json_target = revision.target_context_json or {}
    normalized_target = (
        _target_from_record(revision.target_profile) if revision.target_profile else {}
    )
    target = normalized_target or json_target or None
    diagnostics = calculate_peer_diagnostics(
        members,
        target_context=target,
        as_of=revision.review_diagnostics_as_of,
    )
    return {
        "id": revision.id,
        "peerSetId": revision.peer_set_id,
        "version": revision.version,
        "action": revision.action,
        "changedFields": revision.changed_fields_json or [],
        "name": revision.name,
        "notes": revision.notes,
        "isActive": revision.is_active,
        "reviewStatus": revision.review_status,
        "reviewedAt": revision.reviewed_at,
        "aggregationMethod": revision.aggregation_method,
        "memberCount": len(members),
        "includedMemberCount": sum(1 for member in members if member.get("included", True)),
        "members": members,
        "targetContext": target,
        "aggregates": revision.aggregate_metrics_json or calculate_peer_aggregates(members),
        "diagnostics": diagnostics,
        "reviewReceipt": peer_review_receipt(
            diagnostics_sha256=revision.review_diagnostics_sha256,
            warning_codes=revision.review_warning_codes_json,
            diagnostics_as_of=revision.review_diagnostics_as_of,
            current_diagnostics=diagnostics,
        ),
        "storageConsistency": _storage_consistency(json_members, normalized_members),
        "targetStorageConsistency": _target_storage_consistency(
            json_target, normalized_target
        ),
        "createdAt": revision.created_at,
    }


def _member_sources(peer_set: PeerValuationSet, identifiers: list[str]) -> list[dict[str, Any]]:
    wanted = set(identifiers)
    return [
        {
            "identifier": member["identifier"],
            "companyId": member.get("companyId"),
            "name": member.get("name"),
            "sourceName": member["sourceName"],
            "sourceUrl": member["sourceUrl"],
            "sourceAsOf": member["sourceAsOf"],
            "claimType": member["claimType"],
        }
        for member in peer_set_members(peer_set)
        if member.get("identifier") in wanted
    ]


def peer_set_response(peer_set: PeerValuationSet, *, include_members: bool = True) -> dict[str, Any]:
    json_members = peer_set.peer_identifiers_json or []
    normalized_members = [_member_from_record(record) for record in peer_set.member_records]
    members = normalized_members or json_members
    target = peer_set_target_context(peer_set)
    diagnostics = calculate_peer_diagnostics(members, target_context=target)
    response = {
        "id": peer_set.id,
        "companyId": peer_set.company_id,
        "name": peer_set.name,
        "notes": peer_set.notes,
        "isActive": peer_set.is_active,
        "reviewStatus": peer_set.review_status,
        "reviewedAt": peer_set.reviewed_at,
        "aggregationMethod": peer_set.aggregation_method,
        "version": peer_set.version,
        "aggregates": calculate_peer_aggregates(members),
        "diagnostics": diagnostics,
        "calculationEligibility": peer_set_calculation_eligibility(peer_set, diagnostics=diagnostics),
        "reviewReceipt": peer_review_receipt(
            diagnostics_sha256=peer_set.review_diagnostics_sha256,
            warning_codes=peer_set.review_warning_codes_json,
            diagnostics_as_of=peer_set.review_diagnostics_as_of,
            current_diagnostics=diagnostics,
        ),
        "storageConsistency": _storage_consistency(json_members, normalized_members),
        "targetStorageConsistency": peer_set_target_storage_consistency(peer_set),
        "targetContext": target,
        "importSha256": peer_set.import_sha256,
        "memberCount": len(members),
        "includedMemberCount": sum(1 for member in members if member.get("included", True)),
        "createdAt": peer_set.created_at,
        "updatedAt": peer_set.updated_at,
    }
    if include_members:
        response["members"] = members
    return response


class PeerValuationSetService:
    @staticmethod
    def list_sets(
        db: Session,
        *,
        user_id: str,
        company_id: int | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        query = (
            select(PeerValuationSet)
            .options(
                selectinload(PeerValuationSet.member_records),
                selectinload(PeerValuationSet.target_profile),
            )
            .where(PeerValuationSet.user_id == user_id)
        )
        if company_id is not None:
            query = query.where(PeerValuationSet.company_id == company_id)
        if not include_archived:
            query = query.where(PeerValuationSet.is_active.is_(True))
        rows = db.scalars(query.order_by(PeerValuationSet.updated_at.desc(), PeerValuationSet.id.desc()))
        return [peer_set_response(row, include_members=False) for row in rows]

    @staticmethod
    def get_set(db: Session, *, peer_set_id: int, user_id: str) -> PeerValuationSet:
        peer_set = db.scalar(
            select(PeerValuationSet)
            .options(
                selectinload(PeerValuationSet.member_records),
                selectinload(PeerValuationSet.target_profile),
            )
            .where(
                PeerValuationSet.id == peer_set_id,
                PeerValuationSet.user_id == user_id,
            )
        )
        if peer_set is None:
            raise HTTPException(status_code=404, detail="Peer valuation set not found")
        return peer_set

    @staticmethod
    def create_set(
        db: Session,
        *,
        user_id: str,
        payload: PeerValuationSetCreate,
        revision_action: str = "create",
        import_sha256: str | None = None,
    ) -> PeerValuationSet:
        if db.get(Company, payload.companyId) is None:
            raise HTTPException(status_code=404, detail="Target company not found")
        _validate_members(
            db,
            target_company_id=payload.companyId,
            members=payload.members,
        )
        members = [_member_dict(member) for member in payload.members]
        target = _target_dict(payload.targetContext)
        peer_set = PeerValuationSet(
            company_id=payload.companyId,
            user_id=user_id,
            name=payload.name,
            notes=payload.notes,
            peer_identifiers_json=members,
            target_context_json=target,
            import_sha256=import_sha256,
            aggregate_metrics_json=calculate_peer_aggregates(members),
            aggregation_method="median",
            review_status="draft",
            is_active=True,
            version=1,
        )
        _sync_current_member_records(db, peer_set, members)
        _sync_current_target_profile(db, peer_set, target)
        db.add(peer_set)
        db.flush()
        _record_revision(
            db,
            peer_set=peer_set,
            action=revision_action,
            changed_fields=["name", "notes", "members"]
            + (["targetContext"] if target else []),
        )
        db.commit()
        db.refresh(peer_set)
        return peer_set

    @staticmethod
    def update_set(
        db: Session,
        *,
        peer_set_id: int,
        user_id: str,
        payload: PeerValuationSetUpdate,
    ) -> PeerValuationSet:
        peer_set = _owned_set(db, peer_set_id, user_id)
        if not peer_set.is_active:
            raise HTTPException(status_code=409, detail="Archived peer valuation set cannot be edited")
        _require_version(peer_set, payload.expectedVersion)
        changes = payload.model_dump(exclude_unset=True)
        changed_fields: list[str] = []
        if "name" in changes and peer_set.name != changes["name"]:
            peer_set.name = changes["name"]
            changed_fields.append("name")
        if "notes" in changes and peer_set.notes != changes["notes"]:
            peer_set.notes = changes["notes"]
            changed_fields.append("notes")
        if payload.members is not None:
            _validate_members(
                db,
                target_company_id=peer_set.company_id,
                members=payload.members,
            )
            members = [_member_dict(member) for member in payload.members]
            if members != (peer_set.peer_identifiers_json or []):
                peer_set.peer_identifiers_json = members
                peer_set.aggregate_metrics_json = calculate_peer_aggregates(members)
                _sync_current_member_records(db, peer_set, members)
                changed_fields.append("members")
        if "targetContext" in changes:
            target = _target_dict(payload.targetContext)
            if target != (peer_set.target_context_json or {}):
                peer_set.target_context_json = target
                _sync_current_target_profile(db, peer_set, target)
                changed_fields.append("targetContext")
        if not changed_fields:
            raise HTTPException(status_code=409, detail="Peer valuation set update contains no changes")
        had_review = peer_set.review_status == "reviewed"
        had_receipt = bool(peer_set.review_diagnostics_sha256)
        if had_review:
            changed_fields.append("reviewStatus")
        if had_receipt:
            changed_fields.append("reviewReceipt")
        peer_set.review_status = "draft"
        peer_set.reviewed_at = None
        peer_set.reviewed_by_user_id = None
        peer_set.review_diagnostics_sha256 = None
        peer_set.review_warning_codes_json = None
        peer_set.review_diagnostics_as_of = None
        peer_set.version += 1
        _record_revision(
            db,
            peer_set=peer_set,
            action="update",
            changed_fields=changed_fields,
        )
        db.commit()
        db.refresh(peer_set)
        return peer_set

    @staticmethod
    def review_set(
        db: Session,
        *,
        peer_set_id: int,
        user_id: str,
        payload: PeerValuationSetReview,
    ) -> PeerValuationSet:
        peer_set = _owned_set(db, peer_set_id, user_id)
        if not peer_set.is_active:
            raise HTTPException(status_code=409, detail="Archived peer valuation set cannot be reviewed")
        _require_version(peer_set, payload.expectedVersion)
        if not payload.acknowledged:
            raise HTTPException(status_code=422, detail="Peer evidence review must be acknowledged")
        consistency = peer_set_storage_consistency(peer_set)
        if consistency["status"] == "mismatch":
            raise HTTPException(
                status_code=409,
                detail="Peer member storage mismatch must be repaired before review",
            )
        target_consistency = peer_set_target_storage_consistency(peer_set)
        if target_consistency["status"] == "mismatch":
            raise HTTPException(
                status_code=409,
                detail="Target profile storage mismatch must be repaired before review",
            )
        members = peer_set_members(peer_set)
        included_count = sum(1 for member in members if member.get("included", True))
        if included_count < MINIMUM_METHOD_PEERS:
            raise HTTPException(
                status_code=422,
                detail=f"At least {MINIMUM_METHOD_PEERS} included peers are required for review",
            )
        aggregates = calculate_peer_aggregates(members)
        if not any(
            method["multiple"] is not None
            for method in aggregates["methods"].values()
        ):
            raise HTTPException(
                status_code=422,
                detail=f"At least one multiple needs {MINIMUM_METHOD_PEERS} eligible peer values",
            )
        diagnostics = calculate_peer_diagnostics(
            members,
            target_context=peer_set_target_context(peer_set),
        )
        if payload.expectedDiagnosticsSha256 != diagnostics["acknowledgementSha256"]:
            raise HTTPException(
                status_code=409,
                detail="Peer diagnostics changed; reload and review the current warnings.",
            )
        if payload.acknowledgedWarningCodes != diagnostics["warningCodes"]:
            raise HTTPException(
                status_code=422,
                detail="Acknowledged warning codes must exactly match the current diagnostics.",
            )
        if (
            peer_set.review_status == "reviewed"
            and peer_review_receipt_matches(
                diagnostics_sha256=peer_set.review_diagnostics_sha256,
                warning_codes=peer_set.review_warning_codes_json,
                diagnostics_as_of=peer_set.review_diagnostics_as_of,
                current_diagnostics=diagnostics,
            )
        ):
            raise HTTPException(status_code=409, detail="Peer valuation set is already reviewed")
        was_reviewed = peer_set.review_status == "reviewed"
        peer_set.aggregate_metrics_json = aggregates
        peer_set.review_status = "reviewed"
        peer_set.reviewed_at = datetime.now(UTC)
        peer_set.reviewed_by_user_id = user_id
        peer_set.review_diagnostics_sha256 = diagnostics["acknowledgementSha256"]
        peer_set.review_warning_codes_json = diagnostics["warningCodes"]
        peer_set.review_diagnostics_as_of = date.fromisoformat(diagnostics["asOf"])
        peer_set.version += 1
        _record_revision(
            db,
            peer_set=peer_set,
            action="review",
            changed_fields=([] if was_reviewed else ["reviewStatus"])
            + ["reviewedAt", "reviewedByUserId", "reviewReceipt"],
        )
        db.commit()
        db.refresh(peer_set)
        return peer_set

    @staticmethod
    def archive_set(
        db: Session,
        *,
        peer_set_id: int,
        user_id: str,
        expected_version: int,
    ) -> PeerValuationSet:
        peer_set = _owned_set(db, peer_set_id, user_id)
        _require_version(peer_set, expected_version)
        if not peer_set.is_active:
            raise HTTPException(status_code=409, detail="Peer valuation set is already archived")
        peer_set.is_active = False
        peer_set.version += 1
        _record_revision(
            db,
            peer_set=peer_set,
            action="archive",
            changed_fields=["isActive"],
        )
        db.commit()
        db.refresh(peer_set)
        return peer_set

    @staticmethod
    def restore_set(
        db: Session,
        *,
        peer_set_id: int,
        user_id: str,
        payload: PeerValuationSetMutation,
    ) -> PeerValuationSet:
        peer_set = _owned_set(db, peer_set_id, user_id)
        _require_version(peer_set, payload.expectedVersion)
        if peer_set.is_active:
            raise HTTPException(status_code=409, detail="Peer valuation set is already active")
        changed_fields = ["isActive"]
        peer_set.is_active = True
        if peer_set.review_status != "draft":
            changed_fields.extend(["reviewStatus", "reviewedAt", "reviewedByUserId"])
        if peer_set.review_diagnostics_sha256:
            changed_fields.append("reviewReceipt")
        peer_set.review_status = "draft"
        peer_set.reviewed_at = None
        peer_set.reviewed_by_user_id = None
        peer_set.review_diagnostics_sha256 = None
        peer_set.review_warning_codes_json = None
        peer_set.review_diagnostics_as_of = None
        peer_set.version += 1
        _record_revision(
            db,
            peer_set=peer_set,
            action="restore",
            changed_fields=changed_fields,
        )
        db.commit()
        db.refresh(peer_set)
        return peer_set

    @staticmethod
    def list_revisions(
        db: Session,
        *,
        peer_set_id: int,
        user_id: str,
    ) -> list[dict[str, Any]]:
        _owned_set(db, peer_set_id, user_id)
        revisions = db.scalars(
            select(PeerValuationSetRevision)
            .options(
                selectinload(PeerValuationSetRevision.member_records),
                selectinload(PeerValuationSetRevision.target_profile),
            )
            .where(
                PeerValuationSetRevision.peer_set_id == peer_set_id,
                PeerValuationSetRevision.user_id == user_id,
            )
            .order_by(PeerValuationSetRevision.version.desc())
        )
        return [peer_set_revision_response(revision) for revision in revisions]

    @staticmethod
    def method_source(peer_set: PeerValuationSet, method: str) -> dict[str, Any] | None:
        members = peer_set_members(peer_set)
        method_result = calculate_peer_aggregates(members).get("methods", {}).get(method)
        if not method_result or method_result.get("multiple") is None:
            return None
        identifiers = list(method_result.get("eligibleMemberIdentifiers") or [])
        target = peer_set_target_context(peer_set)
        diagnostics = calculate_peer_diagnostics(members, target_context=target)
        return {
            "peerSetId": peer_set.id,
            "peerSetName": peer_set.name,
            "reviewStatus": peer_set.review_status,
            "reviewedAt": peer_set.reviewed_at,
            "aggregationMethod": peer_set.aggregation_method,
            "eligibleCount": method_result["eligibleCount"],
            "eligibleMemberIdentifiers": identifiers,
            "memberSources": _member_sources(peer_set, identifiers),
            "targetContext": target,
            "formula": method_result["formula"],
            "diagnostics": diagnostics["methods"][method],
            "warnings": [
                warning
                for warning in diagnostics["warnings"]
                if warning.get("method") in (None, method)
            ],
            "claimType": "Calculation",
        }
