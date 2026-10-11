import hashlib
import json
from datetime import date
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.financial import (
    FinancialMetric,
    FinancialStatementPeriod,
    NormalizedFinancialMetric,
    NormalizedFinancialSnapshot,
)
from app.services.industry_assumption import IndustryAssumptionService
from app.services.industry_mapping import IndustryMappingService
from app.services.financial_statement_identity import FinancialStatementIdentityService
from app.services.valuation_source_inputs import (
    sec_draft_inputs, source_input_signature, stored_market_price, stored_usd_risk_free_rate,
)

class AssumptionAutofillEngine:
    INPUT_CONTRACT = {
        "story_text": ("narrative", False, "all"),
        "growth_story": ("narrative", False, "all"),
        "margin_story": ("narrative", False, "all"),
        "reinvestment_story": ("narrative", False, "all"),
        "risk_story": ("narrative", False, "all"),
        "projection_years_count": ("operating", True, "all"),
        "starting_revenue": ("operating", True, "all"),
        "revenue_growth_years_json": ("operating", True, "all"),
        "target_operating_margin": ("operating", True, "all"),
        "current_operating_margin": ("operating", True, "all"),
        "tax_rate": ("operating", True, "all"),
        "sales_to_capital_ratio": ("operating", True, "fcff_dcf"),
        "reinvestment_method": ("operating", True, "fcff_dcf"),
        "starting_invested_capital": ("operating", True, "fcff_dcf"),
        "risk_free_rate": ("discount_rate", True, "all"),
        "equity_risk_premium": ("discount_rate", True, "all"),
        "beta": ("discount_rate", True, "all"),
        "cost_of_equity": ("discount_rate", True, "all"),
        "pre_tax_cost_of_debt": ("discount_rate", True, "fcff_dcf"),
        "debt_to_capital": ("discount_rate", True, "fcff_dcf"),
        "equity_to_capital": ("discount_rate", True, "fcff_dcf"),
        "wacc_start": ("discount_rate", True, "fcff_dcf"),
        "wacc_terminal": ("discount_rate", True, "fcff_dcf"),
        "terminal_growth_rate": ("terminal_value", True, "all"),
        "terminal_roic": ("terminal_value", True, "fcff_dcf"),
        "cash": ("equity_bridge", True, "all"),
        "cross_holdings": ("equity_bridge", False, "all"),
        "minority_interests": ("equity_bridge", True, "all"),
        "preferred_stock": ("equity_bridge", True, "all"),
        "debt": ("equity_bridge", True, "all"),
        "operating_leases": ("equity_bridge", False, "all"),
        "employee_options_value": ("equity_bridge", True, "all"),
        "diluted_shares": ("equity_bridge", True, "all"),
        "basic_shares": ("equity_bridge", False, "all"),
        "current_market_price": ("market_context", True, "all"),
        "cash_flow_currency": ("currency", True, "all"),
        "discount_rate_currency": ("currency", True, "all"),
        "currency_override_note": ("currency", False, "all"),
        "net_income": ("equity_cash_flow", False, "fcfe_ddm"),
        "capex": ("equity_cash_flow", False, "fcfe_ddm"),
        "depreciation": ("equity_cash_flow", False, "fcfe_ddm"),
        "change_in_nwc": ("equity_cash_flow", False, "fcfe_ddm"),
        "new_debt_issued": ("equity_cash_flow", False, "fcfe_ddm"),
        "debt_repaid": ("equity_cash_flow", False, "fcfe_ddm"),
        "dividends": ("equity_cash_flow", False, "fcfe_ddm"),
        "buybacks": ("equity_cash_flow", False, "fcfe_ddm"),
        "stock_issuances": ("equity_cash_flow", False, "fcfe_ddm"),
        "company_age": ("lifecycle", False, "special_case"),
        "probability_of_failure": ("distress", False, "distressed"),
        "distress_sale_proceeds": ("distress", False, "distressed"),
        "book_value_of_equity": ("financial_services", False, "financial_services"),
        "target_roe": ("financial_services", False, "financial_services"),
    }
    PLACEHOLDER_SOURCE_TYPES = {
        "missing_actual_default",
        "generic_market_default",
        "country_default",
    }
    DERIVED_NORMALIZED_METRICS = {
        "ebitda",
        "effective_tax_rate",
        "nopat",
        "net_debt",
        "working_capital",
        "reinvestment",
        "fcff",
        "fcfe",
        "invested_capital",
        "roic",
        "roe",
    }

    @staticmethod
    def financial_history_signature(db: Session, company_id: int) -> str:
        rows = db.execute(
            select(
                FinancialStatementPeriod.year,
                FinancialStatementPeriod.period_type,
                FinancialStatementPeriod.report_date,
                FinancialStatementPeriod.currency,
                FinancialMetric.metric_name,
                FinancialMetric.value,
                FinancialMetric.unit,
            )
            .join(FinancialMetric, FinancialMetric.period_id == FinancialStatementPeriod.id)
            .where(FinancialStatementPeriod.company_id == company_id)
            .order_by(
                FinancialStatementPeriod.year,
                FinancialStatementPeriod.period_type,
                FinancialMetric.metric_name,
            )
        ).all()
        source_payload = [
            [year, period_type, report_date.isoformat(), currency, metric_name, value, unit]
            for year, period_type, report_date, currency, metric_name, value, unit in rows
        ]
        normalized_payload = [
            list(row)
            for row in db.execute(
                select(
                    FinancialStatementPeriod.year,
                    FinancialStatementPeriod.period_type,
                    NormalizedFinancialMetric.metric_code,
                    NormalizedFinancialMetric.value,
                    NormalizedFinancialMetric.unit,
                    NormalizedFinancialMetric.warnings,
                )
                .join(
                    NormalizedFinancialSnapshot,
                    NormalizedFinancialSnapshot.period_id == FinancialStatementPeriod.id,
                )
                .join(
                    NormalizedFinancialMetric,
                    NormalizedFinancialMetric.snapshot_id == NormalizedFinancialSnapshot.id,
                )
                .where(FinancialStatementPeriod.company_id == company_id)
                .order_by(
                    FinancialStatementPeriod.year,
                    FinancialStatementPeriod.period_type,
                    NormalizedFinancialMetric.metric_code,
                )
            ).all()
        ]
        payload = {"source": source_payload, "normalized": normalized_payload}
        return hashlib.sha256(
            json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _freshness_metadata(source_as_of: str | None, max_age_days: int) -> Dict[str, Any]:
        if not source_as_of:
            return {
                "source_as_of": None,
                "max_age_days": max_age_days,
                "age_days": None,
                "is_stale": False,
                "freshness_unknown": True,
                "requires_review": True,
            }
        try:
            parsed = date.fromisoformat(source_as_of[:10])
        except ValueError:
            return {
                "source_as_of": source_as_of,
                "max_age_days": max_age_days,
                "age_days": None,
                "is_stale": False,
                "freshness_unknown": True,
                "requires_review": True,
            }
        age_days = max((date.today() - parsed).days, 0)
        is_stale = age_days > max_age_days
        return {
            "source_as_of": parsed.isoformat(),
            "max_age_days": max_age_days,
            "age_days": age_days,
            "is_stale": is_stale,
            "freshness_unknown": False,
            "requires_review": is_stale,
        }

    @staticmethod
    def _provenance(
        source_type: str,
        label: str,
        confidence: str,
        claim_type: Optional[str] = None,
        **metadata: Any,
    ) -> Dict[str, Any]:
        is_placeholder = source_type in AssumptionAutofillEngine.PLACEHOLDER_SOURCE_TYPES
        if is_placeholder and not label.startswith("[PLACEHOLDER]"):
            label = f"[PLACEHOLDER] {label}"

        if claim_type is None:
            claim_type = {
                "company_actual": "Fact",
                "calculation": "Calculation",
                "formula": "Calculation",
                "industry_benchmark": "Estimate",
                "industry_benchmark_blend": "Estimate",
                "methodology_engine": "Estimate",
                "user_input": "User Assumption",
            }.get(source_type, "Estimate")

        return {
            "source_type": source_type,
            "label": label,
            "confidence": confidence,
            "claim_type": claim_type,
            "is_placeholder": is_placeholder,
            "requires_review": is_placeholder,
            **metadata,
        }

    @staticmethod
    def _source_metadata(provenance: Dict[str, Any]) -> Dict[str, Any]:
        placeholder_fields = [
            key for key, value in provenance.items()
            if isinstance(value, dict) and value.get("is_placeholder")
        ]
        review_fields = [
            key for key, value in provenance.items()
            if isinstance(value, dict) and value.get("requires_review")
        ]
        legacy_fallback_fields = [
            key for key, value in provenance.items()
            if isinstance(value, dict) and value.get("fallback_policy")
        ]
        stale_source_fields = [
            key for key, value in provenance.items()
            if isinstance(value, dict) and value.get("is_stale")
        ]
        freshness_unknown_fields = [
            key for key, value in provenance.items()
            if isinstance(value, dict) and value.get("freshness_unknown")
        ]
        source_dates = sorted(
            value["source_as_of"]
            for value in provenance.values()
            if isinstance(value, dict) and value.get("source_as_of")
        )
        source_counts_by_type: Dict[str, int] = {}
        for value in provenance.values():
            if not isinstance(value, dict):
                continue
            source_type = value.get("source_type", "unknown")
            source_counts_by_type[source_type] = source_counts_by_type.get(source_type, 0) + 1

        currency_entries = [
            value
            for value in provenance.values()
            if isinstance(value, dict) and value.get("reporting_currency")
        ]
        source_rank = {
            "reviewed_metric_unit": 5,
            "reviewed_candidate_unit": 4,
            "filing_metadata": 3,
            "manual_entry": 2,
            "company_fallback": 1,
            "system_default": 0,
            "legacy_unknown": 0,
        }
        preferred_currency_entry = max(
            currency_entries,
            key=lambda value: source_rank.get(value.get("reporting_currency_source"), 0),
            default=None,
        )
        reporting_currency = (
            preferred_currency_entry.get("reporting_currency") if preferred_currency_entry else None
        )
        reporting_currency_source = (
            preferred_currency_entry.get("reporting_currency_source")
            if preferred_currency_entry
            else None
        )
        reporting_currency_confidence = (
            preferred_currency_entry.get("reporting_currency_confidence")
            if preferred_currency_entry
            else None
        )

        return {
            "promotion_ready": len(review_fields) == 0,
            "requires_review": len(review_fields) > 0,
            "placeholder_fields": placeholder_fields,
            "review_fields": review_fields,
            "source_counts_by_type": source_counts_by_type,
            "legacy_fallback_fields": legacy_fallback_fields,
            "stale_source_fields": stale_source_fields,
            "freshness_unknown_fields": freshness_unknown_fields,
            "oldest_source_as_of": source_dates[0] if source_dates else None,
            "latest_source_as_of": source_dates[-1] if source_dates else None,
            "reporting_currency": reporting_currency,
            "reporting_currency_source": reporting_currency_source,
            "reporting_currency_confidence": reporting_currency_confidence,
        }

    @staticmethod
    def _input_readiness(
        assumptions: Dict[str, Any],
        provenance: Dict[str, Any],
    ) -> tuple[list[Dict[str, Any]], Dict[str, Any]]:
        rows: list[Dict[str, Any]] = []
        for field, (category, required, model_scope) in AssumptionAutofillEngine.INPUT_CONTRACT.items():
            value = assumptions.get(field)
            entry = provenance.get(field, {})
            if not isinstance(entry, dict):
                entry = {}
            present = value is not None and value != ""
            source_type = entry.get("source_type")
            if not present:
                status = "missing" if required else "optional_unavailable"
            elif entry.get("is_placeholder") or entry.get("requires_review"):
                status = "review_required"
            elif source_type == "user_input":
                status = "user_input"
            elif source_type in {"formula", "calculation"}:
                status = "calculated"
            else:
                status = "source_backed"
            rows.append({
                "field": field,
                "category": category,
                "required": required,
                "model_scope": model_scope,
                "status": status,
                "source_type": source_type,
                "source_file": entry.get("source_file"),
                "source_as_of": entry.get("source_as_of"),
                "claim_type": entry.get("claim_type"),
            })

        counts: Dict[str, int] = {}
        for row in rows:
            counts[row["status"]] = counts.get(row["status"], 0) + 1
        required_missing = [
            row["field"] for row in rows
            if row["required"] and row["status"] == "missing"
        ]
        required_review = [
            row["field"] for row in rows
            if row["required"] and row["status"] == "review_required"
        ]
        return rows, {
            "field_count": len(rows),
            "counts_by_status": counts,
            "required_missing_fields": required_missing,
            "required_review_fields": required_review,
            "ready_for_review": not required_missing,
            "ready_for_promotion": not required_missing and not required_review,
        }

    @staticmethod
    def draft_assumptions(db: Session, company_id: int, base_assumptions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Drafts a full set of DCF assumptions by combining:
        1. Base assumptions provided by the user (or existing ones)
        2. Extracted historicals/actuals (e.g. from SEC filings)
        3. Damodaran industry priors as fallbacks
        """
        company = db.get(Company, company_id)
        if not company:
            raise ValueError("Company not found")

        draft = base_assumptions.copy() if base_assumptions else {}
        provenance = draft.pop("provenance", {})
        warnings = []

        # Ensure provenance dicts exist
        for k, v in provenance.items():
            if isinstance(v, str):
                provenance[k] = AssumptionAutofillEngine._provenance("user_input", v, "high")

        # Default structural parameters
        if "scenario" not in draft:
            draft["scenario"] = "Base"
            provenance["scenario"] = AssumptionAutofillEngine._provenance("formula", "Structural Default", "high")
        if "projection_years_count" not in draft:
            draft["projection_years_count"] = 10
            provenance["projection_years_count"] = AssumptionAutofillEngine._provenance(
                "formula", "Ten-year explicit forecast structure", "high"
            )
        if "reinvestment_method" not in draft:
            draft["reinvestment_method"] = "sales_to_capital"
            provenance["reinvestment_method"] = AssumptionAutofillEngine._provenance(
                "formula", "Sales-to-capital reinvestment method", "high"
            )

        # 1. Fetch Damodaran Priors
        priors = {}
        country = company.country or "India"
        industry_mix = IndustryMappingService.industry_mix_context(db, company.id)
        if industry_mix:
            try:
                priors = IndustryAssumptionService.get_weighted_assumption_priors(
                    db,
                    country,
                    industry_mix["allocations"],
                )
                warnings.extend(priors.get("warnings", []))
            except Exception:
                warnings.append("The revenue-weighted industry mix could not be loaded. Industry priors are unavailable.")
        elif company.damodaran_industry:
            try:
                priors = IndustryAssumptionService.get_assumption_priors(db, country, company.damodaran_industry)
            except Exception:
                warnings.append("The confirmed Damodaran industry prior could not be loaded.")
        else:
            warnings.append("Company is not mapped to a Damodaran industry. Falling back to generic defaults.")

        margin_priors = priors.get("marginPriors", {})
        reinvestment_priors = priors.get("reinvestmentPriors", {})
        capital_structure_priors = priors.get("capitalStructurePriors", {})
        growth_priors = priors.get("revenueGrowthPriors", {})

        # 2. Extract latest reviewed/promoted actuals from the current canonical path
        actuals = AssumptionAutofillEngine._extract_latest_actuals(db, company)
        candidates = sec_draft_inputs(db, company)
        if candidates:
            reviewed_year = max((source.get("fiscal_year", 0) for _, source in actuals.values()), default=0)
            candidate_year = max(source.get("fiscal_year", 0) for _, source in candidates.values())
            # A newer draft basis does not modify reviewed financial records.
            # Never fill a new annual basis with old-year optional cash flows.
            actuals = candidates if candidate_year > reviewed_year else actuals
            warnings.append("SEC annual candidates populate draft suggestions only. Review their filing, units and scope; no financial facts have been approved.")
            if candidate_year > reviewed_year:
                warnings.append("SEC draft amounts are in full reporting-currency units and full shares, not millions. Keep manual edits on the same scale.")
            else:
                warnings.append("The reviewed annual basis is preserved. SEC candidates are not mixed into it because legacy financial scales may differ; review and normalize missing inputs first.")
        market_price = stored_market_price(db, company)
        if market_price is not None:
            actuals["current_market_price"] = market_price
        if not actuals:
            warnings.append("Company has no extracted actuals. Falling back to industry priors or defaults.")
        legacy_actuals = [
            key for key, (_, source) in actuals.items()
            if source.get("fallback_policy")
        ]
        if legacy_actuals:
            warnings.append(
                "Legacy financial metric fallback used for same-period fields: "
                + ", ".join(sorted(legacy_actuals))
            )
        actual_currency_sources = {
            source.get("reporting_currency_source")
            for _, source in actuals.values()
            if source.get("reporting_currency_source")
        }
        low_confidence_currency_sources = {
            "company_fallback",
            "system_default",
            "legacy_unknown",
        }
        if actual_currency_sources and actual_currency_sources.issubset(low_confidence_currency_sources):
            warnings.append(
                "Reporting currency has low-confidence provenance because reviewed source units and filing metadata did not identify it."
            )
        actual_reporting_currency = next(
            (
                source.get("reporting_currency")
                for _, source in actuals.values()
                if source.get("reporting_currency")
            ),
            None,
        )
        valuation_currency = (company.currency or actual_reporting_currency or "").upper() or None
        if valuation_currency is None:
            warnings.append(
                "The company cash-flow currency is not identified. Currency-specific discount-rate methods are unavailable until it is reviewed."
            )

        def industry_provenance(suffix: str = "", module: str | None = None) -> Dict[str, Any]:
            if industry_mix:
                return AssumptionAutofillEngine._provenance(
                    "industry_benchmark_blend",
                    f"Damodaran Revenue-Weighted Blend{suffix}",
                    "medium",
                    country=country,
                    industry_mix_id=industry_mix["mix_id"],
                    industry_mix_signature=industry_mix["signature"],
                    industry_mix_basis=industry_mix["basis"],
                    industry_mix_allocations=industry_mix["allocations"],
                    source_summary=priors.get("sourceSummary", []),
                    requires_review=True,
                )
            industry_name = company.damodaran_industry or "Unknown Industry"
            source = next(
                (
                    item for item in priors.get("sourceSummary", [])
                    if module is None or item.get("module") == module
                ),
                {},
            )
            freshness = AssumptionAutofillEngine._freshness_metadata(
                source.get("source_as_of"),
                550,
            )
            source_claim_type = source.get("claim_type")
            source_metadata = {
                **source,
                **freshness,
                "requires_review": True,
            }
            source_metadata.pop("claim_type", None)
            return AssumptionAutofillEngine._provenance(
                "industry_benchmark",
                f"Damodaran Prior: {industry_name}{suffix}",
                "medium",
                claim_type=source_claim_type,
                industry=industry_name,
                country=country,
                **source_metadata,
            )

        def set_val(
            key,
            actual_key=None,
            prior_val=None,
            default_val=None,
            fallback_type="missing_actual_default",
            fallback_label="Missing Actual Default",
            prior_module: str | None = None,
        ):
            if key in draft:
                if key not in provenance:
                    provenance[key] = AssumptionAutofillEngine._provenance(
                        "user_input",
                        "User Provided",
                        "high",
                    )
                return

            if actual_key and actual_key in actuals:
                draft[key] = actuals[actual_key][0]
                provenance[key] = actuals[actual_key][1]
            elif prior_val is not None:
                draft[key] = prior_val
                provenance[key] = industry_provenance(module=prior_module)
            else:
                draft[key] = default_val
                provenance[key] = AssumptionAutofillEngine._provenance(fallback_type, fallback_label, "low")

        def dependencies_require_review(*keys: str) -> bool:
            return any(
                isinstance(provenance.get(key), dict) and provenance[key].get("requires_review")
                for key in keys
            )

        # 3. Merge Strategy: Actuals > Priors > Defaults

        set_val("current_operating_margin", "operating_margin", prior_val=margin_priors.get("industryUnadjustedOperatingMargin"), default_val=0.10, fallback_type="generic_market_default", fallback_label="Generic Default Margin", prior_module="margin")
        set_val("target_operating_margin", prior_val=margin_priors.get("suggestedTargetMargin"), default_val=draft["current_operating_margin"], fallback_type="generic_market_default", fallback_label="Derived from current margin", prior_module="margin")

        set_val("sales_to_capital_ratio", "sales_to_capital", prior_val=reinvestment_priors.get("suggestedSalesToCapital"), default_val=1.5, fallback_type="generic_market_default", fallback_label="Generic Sales to Capital", prior_module="reinvestment")

        from app.services.assumption_methodology import AssumptionMethodologyService

        method_industry = None if industry_mix else company.damodaran_industry

        def apply_methodology_default(
            key: str,
            default_fallback: float | None,
            label_fallback: str,
            *,
            industry: str | None = method_industry,
            currency: str | None = valuation_currency,
        ) -> bool:
            if key not in draft:
                default_method = AssumptionMethodologyService.get_default_method(
                    db,
                    key,
                    country,
                    industry,
                    currency,
                )
                if default_method:
                    draft[key] = default_method["value"]
                    source = default_method["source"]
                    freshness = AssumptionAutofillEngine._freshness_metadata(
                        source.get("source_as_of") or source.get("dataset_date"),
                        550,
                    )
                    method_metadata = {
                        **source,
                        **freshness,
                        "requires_review": True,
                    }
                    provenance[key] = AssumptionAutofillEngine._provenance(
                        "methodology_engine",
                        f"{default_method['label']} ({source['source_name']})",
                        default_method["confidence"],
                        claim_type=default_method.get("claim_type"),
                        method_key=default_method["method_key"],
                        method_industry=default_method.get("industry"),
                        method_currency=default_method.get("currency"),
                        **method_metadata,
                    )
                    return True
                else:
                    set_val(key, None, None, default_val=default_fallback, fallback_type="country_default", fallback_label=label_fallback)
            return False

        fred_rate = stored_usd_risk_free_rate(db, valuation_currency)
        if "risk_free_rate" not in draft and fred_rate is not None:
            draft["risk_free_rate"], provenance["risk_free_rate"] = fred_rate
        apply_methodology_default("risk_free_rate", None, f"Not configured for {country}")
        apply_methodology_default(
            "equity_risk_premium",
            None,
            f"Not configured for {country}",
            industry=None,
            currency=None,
        )

        apply_methodology_default(
            "beta",
            1.0,
            "Generic Market Beta",
            currency=None,
        )

        if "cost_of_equity" not in draft:
            if draft.get("risk_free_rate") is not None and draft.get("beta") is not None and draft.get("equity_risk_premium") is not None:
                draft["cost_of_equity"] = draft["risk_free_rate"] + (draft["beta"] * draft["equity_risk_premium"])
                provenance["cost_of_equity"] = AssumptionAutofillEngine._provenance(
                    "formula",
                    "Calculated from CAPM",
                    "high",
                    requires_review=dependencies_require_review("risk_free_rate", "beta", "equity_risk_premium"),
                )
            else:
                draft["cost_of_equity"] = None
                provenance["cost_of_equity"] = AssumptionAutofillEngine._provenance(
                    "missing_dependency",
                    "Missing CAPM inputs",
                    "low",
                    requires_review=True,
                )

        if "pre_tax_cost_of_debt" not in draft and "cost_of_debt" in actuals:
            set_val("pre_tax_cost_of_debt", "cost_of_debt")
        if "pre_tax_cost_of_debt" not in draft:
            fallback_debt_cost = (
                draft["risk_free_rate"] + 0.02
                if draft.get("risk_free_rate") is not None
                else None
            )
            apply_methodology_default(
                "pre_tax_cost_of_debt",
                fallback_debt_cost,
                "Risk-free rate plus an unverified 2% spread" if fallback_debt_cost is not None else "Missing risk-free rate",
            )
        if "tax_rate" not in draft and "effective_tax_rate" in actuals:
            set_val("tax_rate", "effective_tax_rate")
        if "tax_rate" not in draft:
            apply_methodology_default(
                "tax_rate",
                0.25,
                "Generic Corporate Tax Rate",
                industry=None,
                currency=None,
            )
        apply_methodology_default(
            "debt_to_capital",
            0.20,
            "Generic Debt to Capital",
            currency=None,
        )

        if "equity_to_capital" not in draft:
            draft["equity_to_capital"] = 1.0 - draft["debt_to_capital"]
            provenance["equity_to_capital"] = AssumptionAutofillEngine._provenance(
                "formula",
                "Calculated (1 - debt_to_capital)",
                "high",
                requires_review=dependencies_require_review("debt_to_capital"),
            )

        # Use the currency-matched industry workbook WACC when available. The
        # component calculation remains visible in the component inputs above.
        if provenance.get("risk_free_rate", {}).get("source_type") != "market_reference":
            apply_methodology_default("wacc_start", None, "Missing WACC source")
        if "wacc_start" not in draft or draft.get("wacc_start") is None:
            if draft.get("cost_of_equity") is not None and draft.get("pre_tax_cost_of_debt") is not None and draft.get("equity_to_capital") is not None and draft.get("debt_to_capital") is not None and draft.get("tax_rate") is not None:
                draft["wacc_start"] = (draft["cost_of_equity"] * draft["equity_to_capital"]) + \
                                      (draft["pre_tax_cost_of_debt"] * (1 - draft["tax_rate"]) * draft["debt_to_capital"])
                provenance["wacc_start"] = AssumptionAutofillEngine._provenance(
                    "formula",
                    "Calculated from components",
                    "high",
                    requires_review=dependencies_require_review(
                        "cost_of_equity",
                        "equity_to_capital",
                        "pre_tax_cost_of_debt",
                        "tax_rate",
                        "debt_to_capital",
                    ),
                )
            else:
                draft["wacc_start"] = None
                provenance["wacc_start"] = AssumptionAutofillEngine._provenance(
                    "missing_dependency",
                    "Missing WACC components",
                    "low",
                    requires_review=True,
                )

        if "wacc_terminal" not in draft:
            draft["wacc_terminal"] = draft.get("wacc_start")
            if draft["wacc_terminal"] is not None:
                provenance["wacc_terminal"] = AssumptionAutofillEngine._provenance(
                    "formula",
                    "Derived from wacc_start",
                    "high",
                    requires_review=dependencies_require_review("wacc_start"),
                )
            else:
                provenance["wacc_terminal"] = AssumptionAutofillEngine._provenance(
                    "missing_dependency",
                    "Missing wacc_start",
                    "low",
                    requires_review=True,
                )

        # Terminal assumptions
        if "terminal_growth_rate" not in draft:
            if draft.get("risk_free_rate") is not None:
                raw_tgr = min(draft["risk_free_rate"], 0.03)
                draft["terminal_growth_rate"] = raw_tgr
                provenance["terminal_growth_rate"] = AssumptionAutofillEngine._provenance(
                    "formula",
                    "Capped at risk_free_rate",
                    "low",
                    requires_review=dependencies_require_review("risk_free_rate"),
                )
                if raw_tgr == draft["risk_free_rate"]:
                    warnings.append(f"Terminal growth rate is capped at the risk-free rate ({draft['risk_free_rate']*100:.2f}%).")
            else:
                draft["terminal_growth_rate"] = None
                provenance["terminal_growth_rate"] = AssumptionAutofillEngine._provenance(
                    "missing_dependency",
                    "Missing risk_free_rate",
                    "low",
                    requires_review=True,
                )

        if "terminal_roic" not in draft:
            draft["terminal_roic"] = draft.get("wacc_terminal")
            if draft["terminal_roic"] is not None:
                provenance["terminal_roic"] = AssumptionAutofillEngine._provenance(
                    "formula",
                    "Derived from wacc_terminal",
                    "high",
                    requires_review=dependencies_require_review("wacc_terminal"),
                )
            else:
                provenance["terminal_roic"] = AssumptionAutofillEngine._provenance(
                    "missing_dependency",
                    "Missing wacc_terminal",
                    "low",
                    requires_review=True,
                )

        # Base financial numbers
        set_val("starting_revenue", "revenue", None, default_val=0.0, fallback_type="missing_actual_default", fallback_label="Requires Manual Entry")

        if "starting_invested_capital" not in draft:
            if "invested_capital" in actuals and actuals["invested_capital"][0] > 0:
                draft["starting_invested_capital"] = actuals["invested_capital"][0]
                provenance["starting_invested_capital"] = actuals["invested_capital"][1]
            elif draft.get("sales_to_capital_ratio") and draft["sales_to_capital_ratio"] > 0:
                draft["starting_invested_capital"] = draft["starting_revenue"] / draft["sales_to_capital_ratio"]
                provenance["starting_invested_capital"] = AssumptionAutofillEngine._provenance(
                    "formula",
                    "Calculated (revenue / sales_to_capital)",
                    "high",
                    requires_review=dependencies_require_review("starting_revenue", "sales_to_capital_ratio"),
                )
            else:
                draft["starting_invested_capital"] = 0.0
                provenance["starting_invested_capital"] = AssumptionAutofillEngine._provenance(
                    "formula",
                    "Fallback (sales_to_capital is 0)",
                    "low",
                    requires_review=True,
                )

        if "revenue_growth_years_json" not in draft:
            historical_growth = actuals.get("historical_revenue_growth")
            initial_growth = historical_growth[0] if historical_growth else growth_priors.get("industryExpected2Y")
            medium_growth = growth_priors.get("industryExpected5Y")
            if initial_growth is None:
                initial_growth = medium_growth if medium_growth is not None else 0.10
            if medium_growth is None:
                medium_growth = initial_growth

            tgr = draft.get("terminal_growth_rate", 0.03)
            if tgr is None:
                tgr = 0.03

            growth_values = [initial_growth] * 2 + [medium_growth] * 3 + [
                medium_growth - ((medium_growth - tgr) / 5) * i for i in range(1, 6)
            ]
            draft["revenue_growth_years_json"] = {
                str(index): value for index, value in enumerate(growth_values, start=1)
            }

            if historical_growth:
                provenance["revenue_growth_years_json"] = historical_growth[1]
            elif growth_priors.get("industryExpected5Y") is not None:
                provenance["revenue_growth_years_json"] = industry_provenance(" (2Y/5Y path and decay)", "growth")
            else:
                provenance["revenue_growth_years_json"] = AssumptionAutofillEngine._provenance("generic_market_default", "10% decay to terminal", "low")

        # Equity Bridge
        set_val("cash", "cash", None, 0.0, fallback_type="missing_actual_default", fallback_label="Requires Manual Entry")
        set_val("cross_holdings", "cross_holdings", None, None, fallback_type="missing_actual_default", fallback_label="Optional comparison unavailable")
        if draft["cross_holdings"] is None:
            provenance["cross_holdings"]["requires_review"] = False
        set_val("debt", "debt", None, 0.0, fallback_type="missing_actual_default", fallback_label="Requires Manual Entry")
        set_val("operating_leases", "operating_leases", None, None, fallback_type="missing_actual_default", fallback_label="Optional comparison unavailable")
        if draft["operating_leases"] is None:
            provenance["operating_leases"]["requires_review"] = False
        set_val("minority_interests", "minority_interests", None, 0.0, fallback_type="missing_actual_default", fallback_label="Requires Manual Entry")
        set_val("preferred_stock", "preferred_stock", None, 0.0, fallback_type="missing_actual_default", fallback_label="Requires Manual Entry")
        set_val("employee_options_value", "employee_options_value", None, 0.0, fallback_type="missing_actual_default", fallback_label="Requires Manual Entry")
        set_val("diluted_shares", "diluted_shares", None, 0.0, fallback_type="missing_actual_default", fallback_label="Requires Manual Entry")
        set_val("basic_shares", "basic_shares", None, None, fallback_type="missing_actual_default", fallback_label="Optional comparison unavailable")
        if draft["basic_shares"] is None:
            provenance["basic_shares"]["requires_review"] = False
        set_val("current_market_price", "current_market_price", None, 0.0, fallback_type="missing_actual_default", fallback_label="Requires Manual Entry")

        for key in (
            "net_income",
            "capex",
            "depreciation",
            "change_in_nwc",
            "new_debt_issued",
            "debt_repaid",
            "dividends",
            "buybacks",
            "stock_issuances",
            "book_value_of_equity",
        ):
            if key not in draft and key in actuals:
                draft[key] = actuals[key][0]
                provenance[key] = actuals[key][1]

        for key in ("cash_flow_currency", "discount_rate_currency"):
            if key in draft:
                provenance.setdefault(
                    key,
                    AssumptionAutofillEngine._provenance("user_input", "User Provided", "high"),
                )
            elif valuation_currency is not None:
                draft[key] = valuation_currency
                provenance[key] = AssumptionAutofillEngine._provenance(
                    "company_actual",
                    "Company reporting currency",
                    "high" if actual_reporting_currency else "medium",
                    source_table="financial_statement_periods" if actual_reporting_currency else "companies",
                    reporting_currency=valuation_currency,
                    reporting_currency_source=(
                        "unreviewed_sec_unit" if candidates and candidate_year > reviewed_year
                        else "reviewed_financial_history" if actual_reporting_currency else "company_profile"
                    ),
                    reporting_currency_confidence="high" if actual_reporting_currency else "medium",
                )
            else:
                draft[key] = None
                provenance[key] = AssumptionAutofillEngine._provenance(
                    "missing_dependency",
                    "Reporting currency is required",
                    "low",
                    requires_review=True,
                )

        for key, (_, required, _) in AssumptionAutofillEngine.INPUT_CONTRACT.items():
            if key in draft:
                continue
            draft[key] = None
            provenance[key] = AssumptionAutofillEngine._provenance(
                "missing_dependency" if required else "optional_unavailable",
                "Required valuation input is unavailable" if required else "Optional input is not available from reviewed sources",
                "low",
                requires_review=required,
            )

        # Check for missing actual defaults
        missing_keys = [k for k, v in provenance.items() if isinstance(v, dict) and v.get("source_type") == "missing_actual_default"]
        if missing_keys:
            warnings.append(f"Missing actual financial data. Manual entry required for: {', '.join(missing_keys[:3])}" + ("..." if len(missing_keys) > 3 else ""))

        statement_identities = FinancialStatementIdentityService.evaluate_company(db, company_id)
        if statement_identities["status"] == "failed":
            for value in provenance.values():
                if isinstance(value, dict) and value.get("source_type") == "company_actual":
                    value["requires_review"] = True
                    value["financial_statement_identity_status"] = "failed"
            warnings.append(
                "Financial statement identity checks failed; source-derived valuation inputs require reconciliation before use."
            )
        elif statement_identities["status"] == "partial":
            warnings.append(
                "Financial statement identity coverage is partial because some annual source facts are unavailable."
            )
        elif statement_identities["status"] == "not_available":
            warnings.append(
                "Financial statement identity checks are unavailable because the required annual source facts are missing."
            )

        source_metadata = AssumptionAutofillEngine._source_metadata(provenance)
        readiness_rows, readiness_summary = AssumptionAutofillEngine._input_readiness(
            draft,
            provenance,
        )
        source_metadata["input_readiness"] = readiness_rows
        source_metadata["input_readiness_summary"] = readiness_summary
        source_metadata["source_input_signature"] = source_input_signature(db, company)
        source_metadata["financial_period_policy"] = "latest_completed_annual"
        source_metadata["financial_history_signature"] = AssumptionAutofillEngine.financial_history_signature(
            db,
            company_id,
        )
        source_metadata["financial_statement_identity"] = {
            "status": statement_identities["status"],
            "applicable_check_count": statement_identities["applicable_check_count"],
            "failed_check_count": statement_identities["failed_check_count"],
            "valuation_trust_status": (
                "blocked"
                if statement_identities["status"] == "failed"
                else "supported"
                if statement_identities["status"] == "passed"
                else "limited"
            ),
        }
        if industry_mix:
            source_metadata.update(
                {
                    "industry_mix_id": industry_mix["mix_id"],
                    "industry_mix_signature": industry_mix["signature"],
                    "industry_mix_basis": industry_mix["basis"],
                    "industry_mix_as_of_date": industry_mix["as_of_date"],
                    "industry_mix_allocations": industry_mix["allocations"],
                }
            )
        if source_metadata["stale_source_fields"]:
            warnings.append(
                "Stale source data requires explicit review for: "
                + ", ".join(source_metadata["stale_source_fields"])
            )
        if source_metadata["freshness_unknown_fields"]:
            warnings.append(
                "Source freshness could not be verified for: "
                + ", ".join(source_metadata["freshness_unknown_fields"])
            )

        return {
            "assumptions": draft,
            "provenance": provenance,
            "source_metadata": source_metadata,
            "warnings": warnings
        }

    @staticmethod
    def _extract_latest_actuals(db: Session, company: Company) -> Dict[str, tuple[float, Dict[str, Any]]]:
        """
        Extract the latest reviewed/promoted financial metrics for valuation autofill.
        """
        period = db.scalar(
            select(FinancialStatementPeriod)
            .where(FinancialStatementPeriod.company_id == company.id)
            .where(FinancialStatementPeriod.period_type == "annual")
            .order_by(FinancialStatementPeriod.year.desc(), FinancialStatementPeriod.report_date.desc())
        )
        if period is None:
            return {}

        period_str = f"FY{period.year}"
        financial_freshness = AssumptionAutofillEngine._freshness_metadata(
            period.report_date.isoformat(),
            550,
        )

        def currency_metadata(unit: str | None) -> Dict[str, Any]:
            unit_upper = (unit or "").upper()
            has_explicit_metric_currency = bool(period.currency and period.currency.upper() in unit_upper)
            source = "reviewed_metric_unit" if has_explicit_metric_currency else period.currency_source
            confidence = "high" if has_explicit_metric_currency else period.currency_confidence
            return {
                "reporting_currency": period.currency,
                "reporting_currency_source": source,
                "reporting_currency_confidence": confidence,
            }

        legacy_metrics = {}
        for metric in db.scalars(
            select(FinancialMetric).where(FinancialMetric.period_id == period.id)
        ):
            legacy_metrics[metric.metric_name] = (
                metric.value,
                AssumptionAutofillEngine._provenance(
                    "company_actual",
                    f"Legacy Metrics ({period_str})",
                    "medium",
                    source_table="financial_metrics",
                    source_record_id=metric.id,
                    period_id=period.id,
                    fiscal_year=period.year,
                    period_type=period.period_type,
                    report_date=period.report_date.isoformat(),
                    unit=metric.unit,
                    **financial_freshness,
                    **currency_metadata(metric.unit),
                ),
            )
        normalized_metrics = {}
        snapshot = db.scalar(
            select(NormalizedFinancialSnapshot)
            .where(NormalizedFinancialSnapshot.company_id == company.id)
            .where(NormalizedFinancialSnapshot.period_id == period.id)
            .order_by(NormalizedFinancialSnapshot.updated_at.desc(), NormalizedFinancialSnapshot.id.desc())
        )
        if snapshot is not None:
            for metric in db.scalars(
                select(NormalizedFinancialMetric).where(NormalizedFinancialMetric.snapshot_id == snapshot.id)
            ):
                is_derived = metric.metric_code in AssumptionAutofillEngine.DERIVED_NORMALIZED_METRICS or (metric.provenance_notes or "").startswith("Computed:")
                normalized_metrics[metric.metric_code] = (
                    metric.value,
                    AssumptionAutofillEngine._provenance(
                        "calculation" if is_derived else "company_actual",
                        f"Normalized Financials ({period_str})",
                        "medium" if metric.warnings else "high",
                        source_table="normalized_financial_metrics",
                        source_record_id=metric.id,
                        snapshot_id=snapshot.id,
                        period_id=period.id,
                        fiscal_year=period.year,
                        period_type=period.period_type,
                        report_date=period.report_date.isoformat(),
                        unit=metric.unit,
                        **{
                            **financial_freshness,
                            "requires_review": bool(metric.warnings) or financial_freshness["requires_review"],
                        },
                        **currency_metadata(metric.unit),
                        provenance_notes=metric.provenance_notes,
                        warnings=metric.warnings,
                    ),
                )

        if snapshot is None:
            metrics = legacy_metrics
        else:
            bridge_fallbacks = {}
            for metric_code in (
                "cash",
                "debt",
                "diluted_shares",
                "basic_shares",
                "lease_liabilities",
                "operating_leases",
                "cross_holdings",
                "minority_interests",
                "preferred_stock",
                "employee_options_value",
                "cost_of_debt",
                "new_debt_issued",
                "debt_repaid",
                "dividends",
                "buybacks",
                "stock_issuances",
                "book_equity",
            ):
                if metric_code not in legacy_metrics or metric_code in normalized_metrics:
                    continue
                value, source = legacy_metrics[metric_code]
                bridge_fallbacks[metric_code] = (
                    value,
                    {
                        **source,
                        "fallback_policy": "same_period_missing_normalized_bridge_metric",
                        "normalized_snapshot_id": snapshot.id,
                    },
                )
            metrics = {**bridge_fallbacks, **normalized_metrics}

        actuals: Dict[str, tuple[float, Dict[str, Any]]] = {}
        for source_key, target_key in (
            ("revenue", "revenue"),
            ("cash", "cash"),
            ("debt", "debt"),
            ("diluted_shares", "diluted_shares"),
            ("basic_shares", "basic_shares"),
            ("operating_leases", "operating_leases"),
            ("cross_holdings", "cross_holdings"),
            ("minority_interests", "minority_interests"),
            ("preferred_stock", "preferred_stock"),
            ("employee_options_value", "employee_options_value"),
            ("cost_of_debt", "cost_of_debt"),
            ("effective_tax_rate", "effective_tax_rate"),
            ("invested_capital", "invested_capital"),
            ("net_income", "net_income"),
            ("capex", "capex"),
            ("depreciation", "depreciation"),
            ("change_in_nwc", "change_in_nwc"),
            ("new_debt_issued", "new_debt_issued"),
            ("debt_repaid", "debt_repaid"),
            ("dividends", "dividends"),
            ("buybacks", "buybacks"),
            ("stock_issuances", "stock_issuances"),
            ("book_equity", "book_value_of_equity"),
        ):
            if source_key in metrics:
                actuals[target_key] = metrics[source_key]
        if "operating_leases" not in actuals and "lease_liabilities" in metrics:
            actuals["operating_leases"] = metrics["lease_liabilities"]

        revenue_tuple = metrics.get("revenue")
        ebit_tuple = metrics.get("ebit")
        if revenue_tuple and ebit_tuple is not None and revenue_tuple[0] != 0:
            is_normalized = "Normalized" in ebit_tuple[1]["label"]
            actuals["operating_margin"] = (
                ebit_tuple[0] / revenue_tuple[0],
                AssumptionAutofillEngine._provenance(
                    "calculation",
                    f"Calculated from Normalized Financials ({period_str})" if is_normalized else f"Calculated from Legacy Metrics ({period_str})",
                    "high" if is_normalized else "medium",
                    calculation_basis={
                        "revenue": revenue_tuple[1],
                        "ebit": ebit_tuple[1],
                    },
                    **financial_freshness,
                )
            )

        invested_capital_tuple = metrics.get("invested_capital")
        if revenue_tuple and invested_capital_tuple and invested_capital_tuple[0] > 0:
            actuals["sales_to_capital"] = (
                revenue_tuple[0] / invested_capital_tuple[0],
                AssumptionAutofillEngine._provenance(
                    "calculation",
                    f"Calculated from Normalized Financials ({period_str})",
                    "high",
                    calculation_basis={
                        "revenue": revenue_tuple[1],
                        "invested_capital": invested_capital_tuple[1],
                    },
                    **financial_freshness,
                ),
            )

        revenue_history = AssumptionAutofillEngine._extract_revenue_history(db, company.id)
        if revenue_history is not None:
            actuals["historical_revenue_growth"] = revenue_history

        return actuals

    @staticmethod
    def _extract_revenue_history(
        db: Session,
        company_id: int,
    ) -> Optional[tuple[float, Dict[str, Any]]]:
        periods = list(
            db.scalars(
                select(FinancialStatementPeriod)
                .where(FinancialStatementPeriod.company_id == company_id)
                .where(FinancialStatementPeriod.period_type == "annual")
                .order_by(FinancialStatementPeriod.year.asc(), FinancialStatementPeriod.report_date.asc())
            )
        )
        history: list[tuple[int, float, Dict[str, Any]]] = []
        for period in periods[-6:]:
            snapshot = db.scalar(
                select(NormalizedFinancialSnapshot)
                .where(NormalizedFinancialSnapshot.period_id == period.id)
                .order_by(NormalizedFinancialSnapshot.updated_at.desc(), NormalizedFinancialSnapshot.id.desc())
            )
            metric = None
            if snapshot is not None:
                metric = db.scalar(
                    select(NormalizedFinancialMetric)
                    .where(NormalizedFinancialMetric.snapshot_id == snapshot.id)
                    .where(NormalizedFinancialMetric.metric_code == "revenue")
                )
            if metric is not None and metric.value > 0:
                source = AssumptionAutofillEngine._provenance(
                    "company_actual",
                    f"Normalized Financials (FY{period.year})",
                    "high",
                    source_table="normalized_financial_metrics",
                    source_record_id=metric.id,
                    snapshot_id=snapshot.id,
                    period_id=period.id,
                    fiscal_year=period.year,
                )
                history.append((period.year, metric.value, source))
                continue

            if snapshot is not None:
                continue

            legacy_metric = db.scalar(
                select(FinancialMetric)
                .where(FinancialMetric.period_id == period.id)
                .where(FinancialMetric.metric_name == "revenue")
            )
            if legacy_metric is not None and legacy_metric.value > 0:
                source = AssumptionAutofillEngine._provenance(
                    "company_actual",
                    f"Legacy Metrics (FY{period.year})",
                    "medium",
                    source_table="financial_metrics",
                    source_record_id=legacy_metric.id,
                    period_id=period.id,
                    fiscal_year=period.year,
                )
                history.append((period.year, legacy_metric.value, source))

        if len(history) < 2:
            return None

        oldest_year, oldest_revenue, _ = history[0]
        latest_year, latest_revenue, _ = history[-1]
        year_span = latest_year - oldest_year
        if year_span <= 0:
            return None

        cagr = (latest_revenue / oldest_revenue) ** (1 / year_span) - 1
        requires_review = cagr > 0.50 or cagr < -0.20
        return (
            cagr,
            AssumptionAutofillEngine._provenance(
                "calculation",
                f"Historical Revenue CAGR (FY{oldest_year}-FY{latest_year})",
                "medium" if requires_review else "high",
                calculation_basis=[source for _, _, source in history],
                history_years=[year for year, _, _ in history],
                history_values=[value for _, value, _ in history],
                requires_review=requires_review,
                warnings="Historical revenue CAGR is outside the normal review range." if requires_review else None,
            ),
        )
