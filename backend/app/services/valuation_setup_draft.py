from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.dcf import DcfAssumptionSet, ValuationModel, ValuationSetupDraft
from app.api.schemas import DcfAssumptionSetWrite
from app.services.assumption_autofill_engine import AssumptionAutofillEngine
from app.services.dcf import calculate_dcf
from app.services.industry_mapping import IndustryMappingService


class ValuationSetupDraftService:
    POSITIVE_FIELDS = {
        "starting_revenue",
        "sales_to_capital_ratio",
        "starting_invested_capital",
        "diluted_shares",
        "cost_of_equity",
        "wacc_start",
        "wacc_terminal",
    }
    NONNEGATIVE_FIELDS = {
        "cash",
        "debt",
        "minority_interests",
        "preferred_stock",
        "employee_options_value",
    }
    ASSUMPTION_FIELDS = {
        "scenario",
        "story_text",
        "growth_story",
        "margin_story",
        "reinvestment_story",
        "risk_story",
        "projection_years_count",
        "starting_revenue",
        "revenue_growth_years_json",
        "target_operating_margin",
        "current_operating_margin",
        "tax_rate",
        "sales_to_capital_ratio",
        "reinvestment_method",
        "starting_invested_capital",
        "risk_free_rate",
        "equity_risk_premium",
        "beta",
        "cost_of_equity",
        "pre_tax_cost_of_debt",
        "debt_to_capital",
        "equity_to_capital",
        "wacc_start",
        "wacc_terminal",
        "terminal_growth_rate",
        "terminal_roic",
        "cash",
        "minority_interests",
        "preferred_stock",
        "debt",
        "employee_options_value",
        "diluted_shares",
        "basic_shares",
        "current_market_price",
        "net_income",
        "capex",
        "depreciation",
        "change_in_nwc",
        "new_debt_issued",
        "debt_repaid",
        "dividends",
        "buybacks",
        "stock_issuances",
        "company_age",
        "probability_of_failure",
        "distress_sale_proceeds",
        "book_value_of_equity",
        "target_roe",
    }

    @classmethod
    def get_owned(cls, db: Session, draft_id: int, user_id: str) -> ValuationSetupDraft:
        draft = db.scalar(
            select(ValuationSetupDraft)
            .where(ValuationSetupDraft.id == draft_id)
            .where(ValuationSetupDraft.user_id == user_id)
        )
        if draft is None:
            raise HTTPException(status_code=404, detail="Valuation setup draft not found")
        return draft

    @classmethod
    def create_or_reopen(cls, db: Session, company_id: int, user_id: str) -> ValuationSetupDraft:
        company = db.get(Company, company_id)
        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")
        existing = db.scalar(
            select(ValuationSetupDraft)
            .where(ValuationSetupDraft.company_id == company_id)
            .where(ValuationSetupDraft.user_id == user_id)
            .where(ValuationSetupDraft.status.in_(["draft", "ready_to_value"]))
            .order_by(ValuationSetupDraft.updated_at.desc(), ValuationSetupDraft.id.desc())
        )
        if existing is not None:
            industry_mix = IndustryMappingService.industry_mix_context(db, company_id)
            current_mix_signature = industry_mix["signature"] if industry_mix else None
            stored_mix_signature = (existing.source_metadata_json or {}).get("industry_mix_signature")
            current_financial_signature = AssumptionAutofillEngine.financial_history_signature(db, company_id)
            stored_financial_signature = (existing.source_metadata_json or {}).get("financial_history_signature")
            if (
                existing.industry_name != company.damodaran_industry
                or stored_mix_signature != current_mix_signature
                or stored_financial_signature != current_financial_signature
            ):
                return cls.refresh(db, existing)
            return existing

        generated = AssumptionAutofillEngine.draft_assumptions(db, company_id, {})
        assumptions = cls._normalize_assumptions(generated["assumptions"])
        draft = ValuationSetupDraft(
            user_id=user_id,
            company_id=company_id,
            industry_name=company.damodaran_industry,
            assumptions_json=assumptions,
            provenance_json=generated["provenance"],
            source_metadata_json=generated["source_metadata"],
            warnings_json=generated["warnings"],
            reviewed_fields_json=[],
            edited_fields_json=[],
        )
        cls._update_status(draft)
        db.add(draft)
        db.commit()
        db.refresh(draft)
        return draft

    @classmethod
    def update(
        cls,
        db: Session,
        draft: ValuationSetupDraft,
        assumptions_patch: dict[str, Any],
        reviewed_fields: list[str],
        expected_updated_at: datetime | None = None,
    ) -> ValuationSetupDraft:
        cls._assert_mutable(draft)
        cls._assert_version(draft, expected_updated_at)
        unknown = sorted(set(assumptions_patch) - cls.ASSUMPTION_FIELDS)
        if unknown:
            raise HTTPException(status_code=422, detail=f"Unknown assumption fields: {', '.join(unknown)}")
        unknown_reviews = sorted(set(reviewed_fields) - set(draft.assumptions_json or {}))
        if unknown_reviews:
            raise HTTPException(status_code=422, detail=f"Unknown reviewed fields: {', '.join(unknown_reviews)}")

        assumptions = dict(draft.assumptions_json or {})
        assumptions.update(cls._normalize_assumptions(assumptions_patch))
        provenance = dict(draft.provenance_json or {})
        source_metadata = dict(draft.source_metadata_json or {})
        edited_fields = set(draft.edited_fields_json or [])
        edited_fields.update(assumptions_patch)
        required_review = set(source_metadata.get("review_fields", []))
        for field in assumptions_patch:
            previous = provenance.get(field, {})
            provenance[field] = {
                "source_type": "user_input",
                "label": "User Edited Draft",
                "confidence": "high",
                "claim_type": "User Assumption",
                "is_placeholder": False,
                "requires_review": field in required_review,
                "replaces": previous,
            }

        draft.assumptions_json = assumptions
        draft.provenance_json = provenance
        draft.reviewed_fields_json = sorted(set(reviewed_fields))
        draft.edited_fields_json = sorted(edited_fields)
        source_metadata = cls._merge_source_metadata(
            source_metadata,
            AssumptionAutofillEngine._source_metadata(provenance),
        )
        draft.source_metadata_json = source_metadata
        if not source_metadata["stale_source_fields"]:
            draft.warnings_json = [
                warning
                for warning in (draft.warnings_json or [])
                if not warning.lower().startswith("stale source data")
            ]
        if not source_metadata["freshness_unknown_fields"]:
            draft.warnings_json = [
                warning
                for warning in (draft.warnings_json or [])
                if not warning.lower().startswith("source freshness could not be verified")
            ]
        cls._update_status(draft)
        db.commit()
        db.refresh(draft)
        return draft

    @classmethod
    def refresh(
        cls,
        db: Session,
        draft: ValuationSetupDraft,
        expected_updated_at: datetime | None = None,
    ) -> ValuationSetupDraft:
        cls._assert_mutable(draft)
        cls._assert_version(draft, expected_updated_at)
        company = db.get(Company, draft.company_id)
        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")

        old_assumptions = dict(draft.assumptions_json or {})
        old_provenance = dict(draft.provenance_json or {})
        old_reviewed = set(draft.reviewed_fields_json or [])
        edited_fields = set(draft.edited_fields_json or [])
        base_assumptions = {field: old_assumptions[field] for field in edited_fields if field in old_assumptions}
        generated = AssumptionAutofillEngine.draft_assumptions(db, draft.company_id, base_assumptions)
        assumptions = cls._normalize_assumptions(generated["assumptions"])
        provenance = generated["provenance"]
        reviewed_fields: set[str] = set()
        for field in old_reviewed:
            if field in edited_fields:
                reviewed_fields.add(field)
            elif old_assumptions.get(field) == assumptions.get(field) and old_provenance.get(field) == provenance.get(field):
                reviewed_fields.add(field)

        old_source_metadata = dict(draft.source_metadata_json or {})
        old_required = set(old_source_metadata.get("review_fields", []))
        pending_edited_review = (edited_fields & old_required) - old_reviewed
        source_metadata = cls._merge_source_metadata(
            old_source_metadata,
            generated["source_metadata"],
        )
        source_metadata["review_fields"] = sorted(
            set(source_metadata.get("review_fields", [])) | pending_edited_review
        )
        source_metadata["requires_review"] = bool(source_metadata["review_fields"])

        draft.industry_name = company.damodaran_industry
        draft.assumptions_json = assumptions
        draft.provenance_json = provenance
        draft.source_metadata_json = source_metadata
        draft.warnings_json = generated["warnings"]
        draft.reviewed_fields_json = sorted(reviewed_fields)
        cls._update_status(draft)
        db.commit()
        db.refresh(draft)
        return draft

    @staticmethod
    def _merge_source_metadata(
        existing: dict[str, Any] | None,
        generated: dict[str, Any],
    ) -> dict[str, Any]:
        """Refresh generated fields without discarding attached source context."""
        merged = dict(existing or {})
        merged.update(generated)
        return merged

    @classmethod
    def reset_fields(
        cls,
        db: Session,
        draft: ValuationSetupDraft,
        fields: list[str],
        expected_updated_at: datetime | None = None,
    ) -> ValuationSetupDraft:
        cls._assert_mutable(draft)
        cls._assert_version(draft, expected_updated_at)
        requested = set(fields)
        unknown = sorted(requested - cls.ASSUMPTION_FIELDS)
        if unknown:
            raise HTTPException(status_code=422, detail=f"Unknown reset fields: {', '.join(unknown)}")
        if not requested:
            raise HTTPException(status_code=422, detail="At least one reset field is required")

        draft.edited_fields_json = sorted(set(draft.edited_fields_json or []) - requested)
        draft.reviewed_fields_json = sorted(set(draft.reviewed_fields_json or []) - requested)
        return cls.refresh(db, draft)

    @classmethod
    def archive(
        cls,
        db: Session,
        draft: ValuationSetupDraft,
        expected_updated_at: datetime | None = None,
    ) -> ValuationSetupDraft:
        cls._assert_mutable(draft)
        cls._assert_version(draft, expected_updated_at)
        draft.status = "archived"
        source_metadata = dict(draft.source_metadata_json or {})
        source_metadata["promotion_ready"] = False
        source_metadata["archived_at"] = datetime.now(UTC).isoformat()
        draft.source_metadata_json = source_metadata
        db.commit()
        db.refresh(draft)
        return draft

    @classmethod
    def promote(
        cls,
        db: Session,
        draft: ValuationSetupDraft,
        name: str,
        description: str | None,
        model_type: str,
        expected_updated_at: datetime | None = None,
    ) -> ValuationModel:
        cls._assert_version(draft, expected_updated_at)
        if draft.status == "promoted":
            raise HTTPException(status_code=409, detail="Draft has already been promoted")
        cls._update_status(draft)
        if draft.status != "ready_to_value":
            unresolved = cls._unresolved_fields(draft)
            raise HTTPException(
                status_code=409,
                detail=f"Draft review is incomplete: {', '.join(unresolved)}",
            )
        if model_type not in {"fcff_dcf", "distressed", "financial_services"}:
            raise HTTPException(status_code=422, detail="Unsupported valuation model type")
        try:
            model = ValuationModel(
                user_id=draft.user_id,
                company_id=draft.company_id,
                name=name,
                description=description,
                model_type=model_type,
            )
            db.add(model)
            db.flush()
            payload = {
                key: value
                for key, value in cls._normalize_assumptions(draft.assumptions_json).items()
                if key in cls.ASSUMPTION_FIELDS
            }
            try:
                validated = DcfAssumptionSetWrite.model_validate(payload)
            except ValidationError as exc:
                problems = "; ".join(
                    f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
                    for error in exc.errors()[:6]
                )
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid DCF assumptions: {problems}",
                ) from exc
            payload = validated.model_dump(exclude={"valuation_model_id"})
            assumption_set = DcfAssumptionSet(valuation_model_id=model.id, **payload)
            db.add(assumption_set)
            db.flush()
            output, projection_years, sensitivity_tables = calculate_dcf(
                assumption_set,
                model_type=model_type,
            )
            db.add(output)
            db.add_all(projection_years)
            db.add_all(sensitivity_tables)
            draft.status = "promoted"
            draft.promoted_model_id = model.id
            db.commit()
            db.refresh(model)
            return model
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def _assert_mutable(draft: ValuationSetupDraft) -> None:
        if draft.status in {"promoted", "archived"}:
            raise HTTPException(status_code=409, detail=f"{draft.status.title()} drafts cannot be changed")

    @staticmethod
    def _assert_version(draft: ValuationSetupDraft, expected_updated_at: datetime | None) -> None:
        if expected_updated_at is None:
            return

        def as_utc(value: datetime) -> datetime:
            return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

        if as_utc(draft.updated_at) != as_utc(expected_updated_at):
            raise HTTPException(
                status_code=409,
                detail="Valuation setup draft changed since it was loaded. Reload before saving.",
            )

    @classmethod
    def _update_status(cls, draft: ValuationSetupDraft) -> None:
        unresolved = cls._unresolved_fields(draft)
        draft.status = "ready_to_value" if not unresolved else "draft"
        source_metadata = dict(draft.source_metadata_json or {})
        source_metadata["promotion_ready"] = not unresolved
        source_metadata["requires_review"] = bool(unresolved)
        source_metadata["unresolved_fields"] = unresolved
        draft.source_metadata_json = source_metadata

    @classmethod
    def _unresolved_fields(cls, draft: ValuationSetupDraft) -> list[str]:
        required = (draft.source_metadata_json or {}).get("review_fields", [])
        reviewed = set(draft.reviewed_fields_json or [])
        assumptions = draft.assumptions_json or {}
        return [
            field
            for field in required
            if field not in reviewed or not cls._valid_value(field, assumptions.get(field))
        ]

    @classmethod
    def _valid_value(cls, field: str, value: Any) -> bool:
        if isinstance(value, list):
            return bool(value) and all(isinstance(item, (int, float)) for item in value)
        if isinstance(value, dict):
            return bool(value) and all(isinstance(item, (int, float)) for item in value.values())
        try:
            number = float(value)
        except (TypeError, ValueError):
            return False
        if field in cls.POSITIVE_FIELDS:
            return number > 0
        if field in cls.NONNEGATIVE_FIELDS:
            return number >= 0
        return True

    @staticmethod
    def _normalize_assumptions(assumptions: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(assumptions)
        growth = normalized.get("revenue_growth_years_json")
        if isinstance(growth, list):
            normalized["revenue_growth_years_json"] = {
                str(index): value for index, value in enumerate(growth, start=1)
            }
        normalized.setdefault("projection_years_count", 10)
        normalized.setdefault("reinvestment_method", "sales_to_capital")
        normalized.setdefault("scenario", "Base")
        return normalized
