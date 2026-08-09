from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.portfolio_intelligence_engine import PortfolioIntelligenceEngine

router = APIRouter(prefix="/portfolios", tags=["portfolio-intelligence"])

@router.get("/{portfolio_id}/performance")
def get_performance(portfolio_id: int, db: Session = Depends(get_db)):
    """Returns Time-Weighted Return and XIRR for the portfolio."""
    engine = PortfolioIntelligenceEngine(db)
    twr = engine.calculate_twr(portfolio_id)
    xirr = engine.calculate_xirr(portfolio_id)
    return {
        "status": "success",
        "twr": twr,
        "xirr": xirr
    }

@router.get("/{portfolio_id}/attribution")
def get_attribution(portfolio_id: int, db: Session = Depends(get_db)):
    """Decomposes PnL into price movement, cash flow, FX impact, etc."""
    engine = PortfolioIntelligenceEngine(db)
    attribution = engine.calculate_attribution(portfolio_id)
    return {
        "status": "success",
        "data": attribution
    }

@router.get("/{portfolio_id}/opportunity-cost")
def get_opportunity_cost(portfolio_id: int, db: Session = Depends(get_db)):
    """Returns opportunity cost vs benchmarks or alternative holdings."""
    engine = PortfolioIntelligenceEngine(db)
    opportunity_cost = engine.calculate_opportunity_cost(portfolio_id)
    return {
        "status": "success",
        "data": opportunity_cost
    }
