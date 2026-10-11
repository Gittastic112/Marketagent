from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.dcf import DcfAssumptionSet, ValuationAssumptionChangeLog

class AssumptionDiffService:
    DIFF_FIELDS = [
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
        "cross_holdings",
        "minority_interests",
        "preferred_stock",
        "debt",
        "operating_leases",
        "employee_options_value",
        "diluted_shares",
        "basic_shares",
        "current_market_price",
        "cash_flow_currency",
        "discount_rate_currency",
        "currency_override_note",
        "probability_of_failure",
        "distress_sale_proceeds",
        "book_value_of_equity",
        "target_roe",
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
    ]

    @classmethod
    def generate_change_logs(cls, db: Session, new_aset: DcfAssumptionSet) -> list[ValuationAssumptionChangeLog]:
        """
        Finds the most recent assumption set prior to new_aset for the same model,
        computes the difference, and creates ValuationAssumptionChangeLog records
        attached to new_aset.
        """
        # Find the most recent assumption set for this model that is NOT the new one
        # Assuming new_aset is already flushed to DB so it has an ID and created_at
        prev_aset = db.scalars(
            select(DcfAssumptionSet)
            .where(DcfAssumptionSet.valuation_model_id == new_aset.valuation_model_id)
            .where(DcfAssumptionSet.id != new_aset.id)
            .order_by(DcfAssumptionSet.created_at.desc(), DcfAssumptionSet.id.desc())
            .limit(1)
        ).first()

        if not prev_aset:
            return []

        logs = []
        for field in cls.DIFF_FIELDS:
            old_val = getattr(prev_aset, field, None)
            new_val = getattr(new_aset, field, None)

            # Simple equality check. Since these are floats, we could use math.isclose,
            # but exact equality is often enough if they haven't been touched.
            if old_val != new_val:
                log = ValuationAssumptionChangeLog(
                    valuation_model_id=new_aset.valuation_model_id,
                    assumption_set_id=new_aset.id,
                    parameter_name=field,
                    old_value=str(old_val) if old_val is not None else None,
                    new_value=str(new_val) if new_val is not None else None,
                    is_applied=True
                )
                logs.append(log)

        if logs:
            db.add_all(logs)
            db.flush()

        return logs
