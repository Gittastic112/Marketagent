from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assumption_methodology import AssumptionMethodValue

class AssumptionMethodologyService:

    # Optional explicitly hardcoded fallback methods if seed data isn't provided
    FALLBACK_METHODS = {
        "equity_risk_premium": {
            "India": [
                {
                    "method_key": "damodaran_implied_erp",
                    "label": "Damodaran implied ERP",
                    "value": 0.069,
                    "unit": "percent",
                    "source": {
                        "source_name": "Damodaran dataset fallback",
                        "source_file": "macro.xlsx (fallback)"
                    },
                    "confidence": "medium",
                    "available": True,
                    "is_default": True
                },
                {
                    "method_key": "mature_market_plus_crp",
                    "label": "Mature market ERP + country risk premium",
                    "value": 0.072,
                    "unit": "percent",
                    "source": {
                        "source_name": "Damodaran dataset fallback",
                        "source_file": "macro.xlsx (fallback)"
                    },
                    "confidence": "medium",
                    "available": True,
                    "is_default": False
                },
                {
                    "method_key": "sovereign_spread",
                    "label": "Sovereign spread / default spread approach",
                    "value": 0.075,
                    "unit": "percent",
                    "source": {
                        "source_name": "Sovereign Default Spread fallback",
                    },
                    "confidence": "low",
                    "available": True,
                    "is_default": False
                },
                {
                    "method_key": "lambda_adjusted_crp",
                    "label": "Lambda-adjusted country risk premium",
                    "available": False,
                    "reason": "No lambda-adjusted India CRP value found in imported datasets."
                }
            ],
            "United States": [
                {
                    "method_key": "mature_market_erp_baseline",
                    "label": "Mature market ERP baseline",
                    "value": 0.05,
                    "unit": "percent",
                    "source": {
                        "source_name": "Valuation model fallback",
                    },
                    "confidence": "low",
                    "available": True,
                    "is_default": True,
                }
            ],
        },
        "risk_free_rate": {
            "India": [
                {
                    "method_key": "current_government_bond",
                    "label": "Current 10-Year Government Bond",
                    "value": 0.071,
                    "unit": "percent",
                    "source": {
                        "source_name": "Macro fallback",
                    },
                    "confidence": "high",
                    "available": True,
                    "is_default": True
                }
            ],
            "United States": [
                {
                    "method_key": "normalized_risk_free_rate",
                    "label": "Normalized risk-free rate",
                    "value": 0.04,
                    "unit": "percent",
                    "source": {
                        "source_name": "Valuation model fallback",
                    },
                    "confidence": "low",
                    "available": True,
                    "is_default": True,
                }
            ],
        }
    }

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
            "historical_average": "Historical average"
        }
        return labels.get(method_key, method_key.replace("_", " ").capitalize())

    @staticmethod
    def get_available_methods(db: Session, assumption_key: str, country: str, industry: Optional[str] = None) -> List[Dict[str, Any]]:
        # Check DB first
        query = select(AssumptionMethodValue).where(
            AssumptionMethodValue.assumption_key == assumption_key,
            AssumptionMethodValue.country == country
        )
        if industry:
            query = query.where((AssumptionMethodValue.industry == industry) | (AssumptionMethodValue.industry.is_(None)))

        records = db.scalars(query).all()

        methods = []
        if records:
            for rec in records:
                methods.append({
                    "method_key": rec.method_key,
                    "label": AssumptionMethodologyService._map_method_label(assumption_key, rec.method_key),
                    "value": rec.value,
                    "low_value": rec.low_value,
                    "base_value": rec.base_value,
                    "high_value": rec.high_value,
                    "unit": rec.unit,
                    "source": {
                        "source_name": rec.source_name,
                        "source_file": rec.source_file,
                        "source_sheet": rec.source_sheet,
                        "dataset_date": rec.dataset_date.isoformat() if rec.dataset_date else None,
                    },
                    "confidence": rec.confidence,
                    "available": True,
                    "is_default": rec.is_default_candidate,
                    "notes": rec.notes
                })
        else:
            # Fallback to hardcoded structure if no DB records found
            if assumption_key in AssumptionMethodologyService.FALLBACK_METHODS and country in AssumptionMethodologyService.FALLBACK_METHODS[assumption_key]:
                methods = AssumptionMethodologyService.FALLBACK_METHODS[assumption_key][country]

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
    def get_default_method(db: Session, assumption_key: str, country: str, industry: Optional[str] = None) -> Optional[Dict[str, Any]]:
        methods = AssumptionMethodologyService.get_available_methods(db, assumption_key, country, industry)
        for m in methods:
            if m.get("available") and m.get("is_default"):
                return m

        # If no default designated, pick the first available non-custom one
        for m in methods:
            if m.get("available") and m.get("method_key") != "user_custom":
                return m

        return None

    @staticmethod
    def build_country_assumption_pack(db: Session, country: str, industry: Optional[str] = None) -> Dict[str, Any]:
        keys = [
            "equity_risk_premium",
            "risk_free_rate",
            "beta",
            "cost_of_debt",
            "tax_rate",
            "target_operating_margin",
            "sales_to_capital_ratio",
            "terminal_growth",
            "terminal_roc"
        ]

        pack = {}
        for key in keys:
            methods = AssumptionMethodologyService.get_available_methods(db, key, country, industry)
            default = AssumptionMethodologyService.get_default_method(db, key, country, industry)

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
