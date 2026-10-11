from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.company import Company
from app.services.industry_assumption import IndustryAssumptionService
from app.services.industry_mapping import IndustryMappingService
from app.services.financial_statement_identity import FinancialStatementIdentityService
from app.services.valuation_source_inputs import sec_draft_inputs, source_input_signature, stored_market_price, stored_usd_risk_free_rate
from app.services.assumption_provenance import (INPUT_CONTRACT, PLACEHOLDER_SOURCE_TYPES, DERIVED_NORMALIZED_METRICS, _freshness_metadata, _provenance, _source_metadata, _input_readiness)
from app.services.assumption_financial_inputs import (financial_history_signature, _extract_latest_actuals, _extract_revenue_history)

class AssumptionAutofillEngine:
    INPUT_CONTRACT = INPUT_CONTRACT
    PLACEHOLDER_SOURCE_TYPES = PLACEHOLDER_SOURCE_TYPES
    DERIVED_NORMALIZED_METRICS = DERIVED_NORMALIZED_METRICS
    _freshness_metadata = staticmethod(_freshness_metadata)
    _provenance = staticmethod(_provenance)
    _source_metadata = staticmethod(_source_metadata)
    _input_readiness = staticmethod(_input_readiness)
    financial_history_signature = staticmethod(financial_history_signature)
    _extract_latest_actuals = staticmethod(_extract_latest_actuals)
    _extract_revenue_history = staticmethod(_extract_revenue_history)

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
