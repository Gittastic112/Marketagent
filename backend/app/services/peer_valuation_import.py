from __future__ import annotations

import csv
from hashlib import sha256
from io import StringIO
from math import isfinite
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import Company, PeerValuationSet
from app.services.peer_valuation_sets import (
    MAXIMUM_PEER_MEMBERS,
    PeerMemberInput,
    PeerTargetContextInput,
    PeerValuationSetCreate,
    PeerValuationSetService,
    _validate_members,
    peer_set_response,
)


MAXIMUM_PEER_CSV_BYTES = 1_000_000
LEGACY_PEER_CSV_COLUMNS = (
    "set_name",
    "set_notes",
    "identifier",
    "company_id",
    "name",
    "included",
    "source_name",
    "source_url",
    "source_as_of",
    "claim_type",
    "notes",
    "country",
    "currency",
    "fiscal_period_end",
    "accounting_standard",
    "market_cap",
    "revenue_growth_pct",
    "ebitda_margin_pct",
    "pe",
    "pbv",
    "ps",
    "ev_sales",
    "ev_ebitda",
    "ev_ebit",
)
TARGET_CSV_COLUMNS = (
    "target_source_name",
    "target_source_url",
    "target_source_as_of",
    "target_claim_type",
    "target_notes",
    "target_country",
    "target_currency",
    "target_fiscal_period_end",
    "target_accounting_standard",
    "target_market_cap",
    "target_revenue_growth_pct",
    "target_ebitda_margin_pct",
)
PEER_CSV_COLUMNS = (
    *LEGACY_PEER_CSV_COLUMNS[:2],
    *TARGET_CSV_COLUMNS,
    *LEGACY_PEER_CSV_COLUMNS[2:],
)


class PeerCsvPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    companyId: int = Field(ge=1)
    csvText: str = Field(min_length=1, max_length=MAXIMUM_PEER_CSV_BYTES)

    @field_validator("csvText")
    @classmethod
    def require_utf8(cls, value: str) -> str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ValueError("CSV must contain valid UTF-8 text") from exc
        return value


class PeerCsvApplyRequest(PeerCsvPreviewRequest):
    expectedSha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def _csv_hash(csv_text: str) -> str:
    return sha256(csv_text.encode("utf-8")).hexdigest()


def _existing_import(
    db: Session,
    *,
    user_id: str,
    company_id: int,
    import_sha256: str,
) -> PeerValuationSet | None:
    return db.scalar(
        select(PeerValuationSet)
        .options(
            selectinload(PeerValuationSet.member_records),
            selectinload(PeerValuationSet.target_profile),
        )
        .where(
            PeerValuationSet.user_id == user_id,
            PeerValuationSet.company_id == company_id,
            PeerValuationSet.import_sha256 == import_sha256,
        )
    )


def _import_response(peer_set: PeerValuationSet, *, disposition: str) -> dict[str, Any]:
    return {
        **peer_set_response(peer_set),
        "importDisposition": disposition,
    }


def _unescape_formula_cell(value: str) -> str:
    escaped = value.startswith("'") and value[1:].lstrip().startswith(("'", "=", "+", "-", "@"))
    return value[1:] if escaped else value


def _safe_formula_cell(value: Any) -> Any:
    if isinstance(value, str) and value.lstrip().startswith(("'", "=", "+", "-", "@")):
        return "'" + value
    return value


def peer_csv_template() -> dict[str, Any]:
    stream = StringIO(newline="")
    csv.writer(stream).writerow(PEER_CSV_COLUMNS)
    csv_text = stream.getvalue()
    return {
        "filename": "peer-valuation-set-template.csv",
        "csvText": csv_text,
        "sha256": _csv_hash(csv_text),
        "columns": list(PEER_CSV_COLUMNS),
        "targetColumns": list(TARGET_CSV_COLUMNS),
        "formatVersion": "2",
        "acceptsLegacyMemberOnlyFormat": True,
        "maximumRows": MAXIMUM_PEER_MEMBERS,
        "maximumBytes": MAXIMUM_PEER_CSV_BYTES,
        "claimType": "User Assumption",
    }


def _optional_text(row: dict[str, str], key: str) -> str | None:
    value = _unescape_formula_cell((row.get(key) or "").strip())
    return value or None


class CsvCellError(ValueError):
    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field


def _optional_float(row: dict[str, str], key: str) -> float | None:
    value = (row.get(key) or "").strip()
    if not value:
        return None
    try:
        numeric = float(value)
    except ValueError as exc:
        raise CsvCellError(key, "Enter a finite number") from exc
    if not isfinite(numeric):
        raise CsvCellError(key, "Enter a finite number")
    return numeric


def _optional_int(row: dict[str, str], key: str) -> int | None:
    value = (row.get(key) or "").strip()
    try:
        return int(value) if value else None
    except ValueError as exc:
        raise CsvCellError(key, "Enter a whole-number company ID") from exc


def _included_value(row: dict[str, str]) -> bool:
    value = (row.get("included") or "true").strip().casefold()
    if value in {"true", "1", "yes"}:
        return True
    if value in {"false", "0", "no"}:
        return False
    raise ValueError("included must be true or false")


def _row_member(row: dict[str, str]) -> PeerMemberInput:
    return PeerMemberInput.model_validate(
        {
            "identifier": _unescape_formula_cell((row.get("identifier") or "").strip()),
            "companyId": _optional_int(row, "company_id"),
            "name": _optional_text(row, "name"),
            "included": _included_value(row),
            "multiples": {
                key: value
                for key in ("pe", "pbv", "ps", "ev_sales", "ev_ebitda", "ev_ebit")
                if (value := _optional_float(row, key)) is not None
            },
            "sourceName": _unescape_formula_cell((row.get("source_name") or "").strip()),
            "sourceUrl": (row.get("source_url") or "").strip(),
            "sourceAsOf": (row.get("source_as_of") or "").strip(),
            "claimType": (row.get("claim_type") or "Fact").strip(),
            "notes": _optional_text(row, "notes"),
            "country": _optional_text(row, "country"),
            "currency": _optional_text(row, "currency"),
            "fiscalPeriodEnd": _optional_text(row, "fiscal_period_end"),
            "accountingStandard": _optional_text(row, "accounting_standard"),
            "marketCap": _optional_float(row, "market_cap"),
            "revenueGrowthPct": _optional_float(row, "revenue_growth_pct"),
            "ebitdaMarginPct": _optional_float(row, "ebitda_margin_pct"),
        }
    )


def _row_target(row: dict[str, str]) -> PeerTargetContextInput:
    return PeerTargetContextInput.model_validate(
        {
            "sourceName": _optional_text(row, "target_source_name"),
            "sourceUrl": (row.get("target_source_url") or "").strip(),
            "sourceAsOf": (row.get("target_source_as_of") or "").strip(),
            "claimType": (row.get("target_claim_type") or "Fact").strip(),
            "notes": _optional_text(row, "target_notes"),
            "country": _optional_text(row, "target_country"),
            "currency": _optional_text(row, "target_currency"),
            "fiscalPeriodEnd": _optional_text(row, "target_fiscal_period_end"),
            "accountingStandard": _optional_text(row, "target_accounting_standard"),
            "marketCap": _optional_float(row, "target_market_cap"),
            "revenueGrowthPct": _optional_float(row, "target_revenue_growth_pct"),
            "ebitdaMarginPct": _optional_float(row, "target_ebitda_margin_pct"),
        }
    )


def _target_cell(row: dict[str, str], column: str) -> str:
    return _unescape_formula_cell((row.get(column) or "").strip())


def preview_peer_csv(
    db: Session,
    *,
    payload: PeerCsvPreviewRequest,
) -> dict[str, Any]:
    def blocked(field: str, message: str, row: int | None = None) -> dict[str, Any]:
        return {
            "isValid": False, "sha256": _csv_hash(payload.csvText),
            "setName": None, "setNotes": None, "formatVersion": None,
            "legacyFormat": False, "targetContext": None, "memberCount": 0,
            "members": [], "errors": [{"row": row, "field": field, "message": message}],
            "warnings": [],
        }

    csv_bytes = payload.csvText.encode("utf-8")
    errors: list[dict[str, Any]] = []
    if len(csv_bytes) > MAXIMUM_PEER_CSV_BYTES:
        return blocked("file", "CSV exceeds the 1 MB limit")
    if "\x00" in payload.csvText:
        return blocked("file", "CSV must not contain NUL bytes")
    stream = StringIO(payload.csvText.removeprefix("\ufeff"), newline="")
    reader = csv.reader(stream, strict=True)
    try:
        headers = tuple(next(reader, []))
    except csv.Error:
        return blocked("header", "Malformed CSV header", 1)
    legacy_format = headers == LEGACY_PEER_CSV_COLUMNS
    if headers not in {PEER_CSV_COLUMNS, LEGACY_PEER_CSV_COLUMNS}:
        return blocked("header", "CSV header must exactly match the published peer template", 1)

    rows: list[dict[str, str]] = []
    row_numbers: list[int] = []
    try:
        for cells in reader:
            if not cells:
                continue
            if len(rows) >= MAXIMUM_PEER_MEMBERS:
                return blocked("file", f"CSV contains more than {MAXIMUM_PEER_MEMBERS} peer rows")
            if len(cells) != len(headers):
                return blocked("row", "CSV row must have exactly the header's column count", reader.line_num)
            rows.append(dict(zip(headers, cells)))
            row_numbers.append(reader.line_num)
    except csv.Error:
        return blocked("file", "Malformed CSV or field exceeds the parser limit", reader.line_num)
    if db.get(Company, payload.companyId) is None:
        errors.append({"row": None, "field": "companyId", "message": "Target company was not found"})
    if not rows:
        errors.append({"row": None, "field": "file", "message": "CSV must contain at least one peer row"})

    set_name_values = [
        _unescape_formula_cell((row.get("set_name") or "").strip()) for row in rows
    ]
    set_note_values = [
        _unescape_formula_cell((row.get("set_notes") or "").strip()) for row in rows
    ]
    set_names = set(set_name_values)
    set_notes = set(set_note_values)
    if not set_name_values or any(not value for value in set_name_values) or len(set_names) != 1:
        errors.append(
            {"row": None, "field": "set_name", "message": "Every row must use one non-empty set_name"}
        )
    if len(set_notes) > 1:
        errors.append(
            {"row": None, "field": "set_notes", "message": "set_notes must be identical on every row"}
        )

    target: PeerTargetContextInput | None = None
    if not legacy_format and rows:
        target_rows = [
            tuple(_target_cell(row, column) for column in TARGET_CSV_COLUMNS)
            for row in rows
        ]
        target_present = any(any(value for value in target_row) for target_row in target_rows)
        if target_present and any(target_row != target_rows[0] for target_row in target_rows[1:]):
            errors.append(
                {
                    "row": None,
                    "field": "target_context",
                    "message": "Target-company columns must be identical on every peer row",
                }
            )
        elif target_present:
            try:
                target = _row_target(rows[0])
            except (ValueError, ValidationError) as exc:
                if isinstance(exc, ValidationError):
                    for item in exc.errors():
                        errors.append(
                            {
                                "row": row_numbers[0],
                                "field": "targetContext."
                                + ".".join(str(part) for part in item["loc"]),
                                "message": item["msg"],
                            }
                        )
                else:
                    errors.append(
                        {"row": row_numbers[0], "field": getattr(exc, "field", "targetContext"), "message": str(exc)}
                    )

    members: list[PeerMemberInput] = []
    for row_number, row in zip(row_numbers, rows):
        try:
            members.append(_row_member(row))
        except (ValueError, ValidationError) as exc:
            if isinstance(exc, ValidationError):
                for item in exc.errors():
                    errors.append(
                        {
                            "row": row_number,
                            "field": ".".join(str(part) for part in item["loc"]),
                            "message": item["msg"],
                        }
                    )
            else:
                errors.append({"row": row_number, "field": getattr(exc, "field", "row"), "message": str(exc)})

    if not errors:
        try:
            PeerValuationSetCreate(
                companyId=payload.companyId,
                name=set_name_values[0],
                notes=set_note_values[0] or None,
                targetContext=target,
                members=members,
            )
            _validate_members(db, target_company_id=payload.companyId, members=members)
        except ValidationError as exc:
            for item in exc.errors():
                field = ".".join(str(part) for part in item["loc"])
                errors.append({"row": None, "field": {"name": "set_name", "notes": "set_notes"}.get(field, field), "message": item["msg"]})
        except HTTPException as exc:
            errors.append({"row": None, "field": "members", "message": str(exc.detail)})

    warnings = [
        "CSV source facts are user-supplied and are not independently verified.",
        "Applying a valid preview creates a Draft peer set that still requires explicit review.",
    ]
    if legacy_format:
        warnings.append("Legacy peer-only CSV accepted; target-company context is missing.")
    elif target is None:
        warnings.append(
            "No target-company profile is included; target-relative diagnostics remain limited."
        )
    return {
        "isValid": not errors,
        "sha256": _csv_hash(payload.csvText),
        "setName": next(iter(set_names), None),
        "setNotes": next(iter(set_notes), None) or None,
        "formatVersion": "1" if legacy_format else "2",
        "legacyFormat": legacy_format,
        "targetContext": target.model_dump(mode="json", exclude_none=True) if target else None,
        "memberCount": len(members),
        "members": [member.model_dump(mode="json", exclude_none=True) for member in members],
        "errors": errors,
        "warnings": warnings,
    }


def apply_peer_csv(
    db: Session,
    *,
    user_id: str,
    payload: PeerCsvApplyRequest,
) -> dict[str, Any]:
    actual_hash = _csv_hash(payload.csvText)
    if actual_hash != payload.expectedSha256:
        raise HTTPException(status_code=409, detail="CSV changed after preview; preview the exact file again")
    existing = _existing_import(
        db,
        user_id=user_id,
        company_id=payload.companyId,
        import_sha256=actual_hash,
    )
    if existing is not None:
        return _import_response(existing, disposition="reused")
    preview = preview_peer_csv(
        db,
        payload=PeerCsvPreviewRequest(companyId=payload.companyId, csvText=payload.csvText),
    )
    if not preview["isValid"]:
        raise HTTPException(status_code=422, detail="CSV preview contains validation errors")
    try:
        peer_set = PeerValuationSetService.create_set(
            db,
            user_id=user_id,
            payload=PeerValuationSetCreate(
                companyId=payload.companyId,
                name=preview["setName"],
                notes=preview["setNotes"],
                targetContext=(
                    PeerTargetContextInput.model_validate(preview["targetContext"])
                    if preview["targetContext"]
                    else None
                ),
                members=[PeerMemberInput.model_validate(member) for member in preview["members"]],
            ),
            revision_action="import",
            import_sha256=actual_hash,
        )
    except IntegrityError:
        db.rollback()
        existing = _existing_import(
            db,
            user_id=user_id,
            company_id=payload.companyId,
            import_sha256=actual_hash,
        )
        if existing is None:
            raise
        return _import_response(existing, disposition="reused")
    return _import_response(peer_set, disposition="created")


def export_peer_csv(peer_set_response_data: dict[str, Any]) -> dict[str, Any]:
    for audit in ("storageConsistency", "targetStorageConsistency"):
        if (peer_set_response_data.get(audit) or {}).get("status") == "mismatch":
            raise HTTPException(status_code=409, detail="Storage mismatch must be repaired before CSV export")
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=PEER_CSV_COLUMNS)
    writer.writeheader()
    target = peer_set_response_data.get("targetContext") or {}
    target_row = {
        "target_source_name": target.get("sourceName") or "",
        "target_source_url": target.get("sourceUrl") or "",
        "target_source_as_of": target.get("sourceAsOf") or "",
        "target_claim_type": target.get("claimType") or "",
        "target_notes": target.get("notes") or "",
        "target_country": target.get("country") or "",
        "target_currency": target.get("currency") or "",
        "target_fiscal_period_end": target.get("fiscalPeriodEnd") or "",
        "target_accounting_standard": target.get("accountingStandard") or "",
        "target_market_cap": target.get("marketCap") or "",
        "target_revenue_growth_pct": (
            target.get("revenueGrowthPct")
            if target.get("revenueGrowthPct") is not None
            else ""
        ),
        "target_ebitda_margin_pct": (
            target.get("ebitdaMarginPct")
            if target.get("ebitdaMarginPct") is not None
            else ""
        ),
    }
    for member in peer_set_response_data.get("members") or []:
        multiples = member.get("multiples") or {}
        row = {
            "set_name": peer_set_response_data["name"],
            "set_notes": peer_set_response_data.get("notes") or "",
            **target_row,
            "identifier": member.get("identifier") or "",
            "company_id": member.get("companyId") or "",
            "name": member.get("name") or "",
            "included": "true" if member.get("included", True) else "false",
            "source_name": member.get("sourceName") or "",
            "source_url": member.get("sourceUrl") or "",
            "source_as_of": member.get("sourceAsOf") or "",
            "claim_type": member.get("claimType") or "",
            "notes": member.get("notes") or "",
            "country": member.get("country") or "",
            "currency": member.get("currency") or "",
            "fiscal_period_end": member.get("fiscalPeriodEnd") or "",
            "accounting_standard": member.get("accountingStandard") or "",
            "market_cap": member.get("marketCap") or "",
            "revenue_growth_pct": member.get("revenueGrowthPct") if member.get("revenueGrowthPct") is not None else "",
            "ebitda_margin_pct": member.get("ebitdaMarginPct") if member.get("ebitdaMarginPct") is not None else "",
            **{method: multiples.get(method) or "" for method in ("pe", "pbv", "ps", "ev_sales", "ev_ebitda", "ev_ebit")},
        }
        writer.writerow({key: _safe_formula_cell(value) for key, value in row.items()})
    csv_text = stream.getvalue()
    return {
        "filename": f"peer-set-{peer_set_response_data['id']}-v{peer_set_response_data['version']}.csv",
        "csvText": csv_text,
        "sha256": _csv_hash(csv_text),
        "rowCount": len(peer_set_response_data.get("members") or []),
        "formatVersion": "2",
        "targetContextIncluded": bool(target),
        "claimType": "User Assumption",
        "warnings": [
            "Spreadsheet formula-leading text cells are apostrophe-escaped.",
            *([] if target else ["No target-company profile is included in this export."]),
        ],
    }
