from typing import Any, Dict, List, Optional
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from app.models.assumption_methodology import AssumptionMethodValue
from app.services.damodaran_dataset_versions import active_dataset_ids


def _country_aliases(country: str) -> tuple[str, ...]:
    normalized = country.strip().casefold()
    for aliases in (("united states", "united states of america", "us", "usa"), ("india", "in", "ind")):
        if normalized in aliases:
            return aliases
    return (normalized,)


class AssumptionMethodologyService:

    @staticmethod
    def _map_method_label(assumption_key: str, method_key: str) -> str:
        labels = {
            "damodaran_implied_erp": "Damodaran implied ERP",
            "mature_market_plus_crp": "Mature market ERP + CRP",
            "sovereign_spread": "Sovereign/default spread approach",
            "lambda_adjusted_crp": "Lambda-adjusted CRP",
            "user_custom": "Custom user input",
            "current_government_bond": "Current government bond yield",
            "normalized_risk_free_rate": "Normalized risk-free rate",
            "bottom_up_industry_beta": "Bottom-up industry beta",
            "regression_beta": "Regression beta",
            "industry_median": "Industry median",
            "historical_average": "Historical average",
            "damodaran_country_erp": "Damodaran country equity risk premium",
            "damodaran_us_workbook_erp": "US WACC workbook equity premium",
            "long_term_us_treasury": "Long-term US Treasury rate",
            "inflation_parity_from_us_treasury": "INR risk-free rate by inflation parity",
            "industry_regression_beta": "Industry regression beta",
            "bottom_up_unlevered_beta": "Industry unlevered beta",
            "cash_corrected_unlevered_beta": "Cash-corrected industry unlevered beta",
            "industry_effective_tax_rate": "Industry effective tax rate",
            "country_marginal_corporate_tax_rate": "Country marginal corporate tax rate",
            "industry_cost_of_debt_local": "Industry pre-tax cost of debt in local currency",
            "industry_cost_of_debt_usd": "Industry pre-tax cost of debt in USD",
            "industry_market_debt_ratio": "Industry market debt ratio",
            "industry_market_equity_ratio": "Industry market equity ratio",
            "industry_cost_of_capital_local": "Industry cost of capital in local currency",
            "industry_cost_of_capital_usd": "Industry cost of capital in USD",
        }
        return labels.get(method_key, method_key.replace("_", " ").capitalize())

    @staticmethod
    def get_available_methods(
        db: Session,
        assumption_key: str,
        country: str,
        industry: Optional[str] = None,
        currency: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = select(AssumptionMethodValue).where(
            AssumptionMethodValue.assumption_key == assumption_key,
            func.lower(func.trim(AssumptionMethodValue.country)).in_(_country_aliases(country)),
            or_(
                AssumptionMethodValue.dataset_file_id.in_(active_dataset_ids()),
                and_(
                    AssumptionMethodValue.dataset_file_id.is_(None),
                    AssumptionMethodValue.source_type.in_(("manual", "user", "reviewed")),
                ),
            ),
        )
        if industry:
            query = query.where((AssumptionMethodValue.industry == industry) | (AssumptionMethodValue.industry.is_(None)))
        else:
            query = query.where(AssumptionMethodValue.industry.is_(None))
        if currency:
            query = query.where(
                (AssumptionMethodValue.currency == currency.upper())
                | (AssumptionMethodValue.currency.is_(None))
            )

        ordering = []
        if industry:
            ordering.append(case((AssumptionMethodValue.industry == industry, 0), else_=1))
        if currency:
            ordering.append(case((AssumptionMethodValue.currency == currency.upper(), 0), else_=1))
        ordering.extend((
            AssumptionMethodValue.is_default_candidate.desc(),
            AssumptionMethodValue.imported_at.desc(),
            AssumptionMethodValue.id.desc(),
        ))
        query = query.order_by(*ordering)

        records = db.scalars(query).all()

        methods = []
        for rec in records:
            dataset = rec.dataset_file
            label = AssumptionMethodologyService._map_method_label(assumption_key, rec.method_key)
            notes = rec.notes
            # Preserve historical keys/values, but correct their source scope on reads.
            # The supplied workbook explicitly labels D10/D11 "Global weighted average".
            if rec.source_file == "waccIndia.xls" and assumption_key in {
                "equity_risk_premium", "country_default_spread"
            }:
                label = f"Damodaran WACC workbook {'equity premium' if assumption_key == 'equity_risk_premium' else 'default spread'} input"
                notes = (
                    "Source labels this input 'Global weighted average'. It is a dated WACC "
                    "workbook assumption, not independently verified country-specific risk. "
                    "Review geographic exposure and the discount-rate methodology before use."
                )
            methods.append({
                    "method_key": rec.method_key,
                    "label": label,
                    "value": rec.value,
                    "low_value": rec.low_value,
                    "base_value": rec.base_value,
                    "high_value": rec.high_value,
                    "unit": rec.unit,
                    "source": {
                        "source_name": rec.source_name,
                        "source_file": rec.source_file,
                        "source_sheet": rec.source_sheet,
                        "source_row": rec.source_row,
                        "source_column": rec.source_column,
                        "dataset_date": rec.dataset_date.isoformat() if rec.dataset_date else None,
                        "dataset_file_id": rec.dataset_file_id,
                        "source_sha256": dataset.source_sha256 if dataset else None,
                        "source_as_of": dataset.source_as_of if dataset else None,
                        "canonical_source_path": dataset.canonical_source_path if dataset else None,
                    },
                    "confidence": rec.confidence,
                    "available": True,
                    "is_default": rec.is_default_candidate,
                    "currency": rec.currency,
                    "industry": rec.industry,
                    "claim_type": "Calculation" if rec.source_type == "calculation" else "Estimate",
                    "requires_review": True,
                    "notes": notes
                })

        # Always add user custom as available fallback
        if not any(m.get("method_key") == "user_custom" for m in methods):
            methods.append({
                "method_key": "user_custom",
                "label": "Custom user input",
                "available": True,
                "is_default": False,
                "confidence": "high",
                "source": {
                    "source_name": "User override"
                }
            })

        return methods

    @staticmethod
    def get_default_method(
        db: Session,
        assumption_key: str,
        country: str,
        industry: Optional[str] = None,
        currency: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        methods = AssumptionMethodologyService.get_available_methods(
            db,
            assumption_key,
            country,
            industry,
            currency,
        )
        for m in methods:
            if m.get("available") and m.get("is_default"):
                return m

        # If no default designated, pick the first available non-custom one
        for m in methods:
            if m.get("available") and m.get("method_key") != "user_custom":
                return m

        return None

    @staticmethod
    def build_country_assumption_pack(
        db: Session,
        country: str,
        industry: Optional[str] = None,
        currency: Optional[str] = None,
    ) -> Dict[str, Any]:
        keys = [
            "equity_risk_premium",
            "risk_free_rate",
            "beta",
            "pre_tax_cost_of_debt",
            "debt_to_capital",
            "equity_to_capital",
            "wacc_start",
            "country_default_spread",
            "tax_rate",
            "target_operating_margin",
            "sales_to_capital_ratio",
            "terminal_growth",
            "terminal_roc"
        ]

        pack = {}
        for key in keys:
            methods = AssumptionMethodologyService.get_available_methods(
                db,
                key,
                country,
                industry,
                currency,
            )
            default = AssumptionMethodologyService.get_default_method(
                db,
                key,
                country,
                industry,
                currency,
            )

            if default:
                pack[key] = {
                    "assumption_key": key,
                    "country": country,
                    "industry": industry,
                    "default_method": default["method_key"],
                    "selected_method": default["method_key"],
                    "methods": methods,
                    "range": {
                        "low": default.get("low_value"),
                        "base": default.get("base_value", default.get("value")),
                        "high": default.get("high_value")
                    } if "low_value" in default else None,
                    "requires_review": True
                }
            else:
                pack[key] = {
                    "assumption_key": key,
                    "country": country,
                    "industry": industry,
                    "default_method": "user_custom",
                    "selected_method": "user_custom",
                    "methods": methods,
                    "range": None,
                    "requires_review": True
                }

        return pack
