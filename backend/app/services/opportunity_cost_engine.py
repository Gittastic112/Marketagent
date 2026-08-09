from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PortfolioHolding, EntityScore, DecisionReadiness, ValuationModel, DcfAssumptionSet
from app.services.portfolio_valuation import calculate_portfolio_valuation


class OpportunityCostEngine:

    @staticmethod
    def compare_holdings(db: Session, portfolio_id: int) -> List[Dict[str, Any]]:
        """
        Compares holdings in a portfolio using DCF gap, EntityScore confidence, and DecisionReadiness.
        Returns a list of structured trade-offs.
        """
        holdings = db.scalars(
            select(PortfolioHolding)
            .where(PortfolioHolding.portfolio_id == portfolio_id)
            .where(PortfolioHolding.quantity > 0)
        ).all()

        results = []
        for holding in holdings:
            if not holding.company_id:
                continue

            # Fetch DecisionReadiness
            readiness = db.scalar(
                select(DecisionReadiness)
                .where(DecisionReadiness.company_id == holding.company_id)
            )
            readiness_status = readiness.overall_status if readiness else "Unknown"

            # Fetch EntityScore
            score = db.scalar(
                select(EntityScore)
                .where(EntityScore.company_id == holding.company_id)
            )
            confidence = score.overall_confidence_score if score else None

            # Fetch Valuation / DCF Gap (implied upside)
            base_valuation = db.scalar(
                select(DcfAssumptionSet)
                .join(ValuationModel, ValuationModel.id == DcfAssumptionSet.valuation_model_id)
                .where(ValuationModel.company_id == holding.company_id)
                .where(DcfAssumptionSet.scenario == "Base")
                .order_by(DcfAssumptionSet.id.desc())
                .limit(1)
            )

            dcf_upside = None
            if base_valuation and base_valuation.implied_share_price:
                # We need the current market price to calculate the gap
                from app.services.portfolio_valuation import get_latest_price
                price = get_latest_price(db, holding.ticker)
                if price and float(price.price) > 0:
                    dcf_upside = (float(base_valuation.implied_share_price) / float(price.price)) - 1.0

            results.append({
                "ticker": holding.ticker,
                "readiness_status": readiness_status,
                "confidence_score": confidence,
                "dcf_upside": dcf_upside,
            })

        # Example of creating trade-offs:
        # Sort by dcf_upside descending
        results.sort(key=lambda x: x.get("dcf_upside") or -999, reverse=True)

        trade_offs = []
        if len(results) >= 2:
            top_upside = results[0]
            second_upside = results[1]

            trade_offs.append({
                "comparison": f"{top_upside['ticker']} vs {second_upside['ticker']}",
                "narrative": f"{top_upside['ticker']} offers larger modeled upside ({(top_upside['dcf_upside'] or 0)*100:.1f}%) "
                             f"but has a confidence score of {top_upside['confidence_score']} and readiness '{top_upside['readiness_status']}'. "
                             f"{second_upside['ticker']} offers {(second_upside['dcf_upside'] or 0)*100:.1f}% upside "
                             f"with confidence {second_upside['confidence_score']} and readiness '{second_upside['readiness_status']}'."
            })

        return trade_offs
