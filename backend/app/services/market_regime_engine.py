from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market_regime import MarketRegimeScore
from app.models.market_regime_input import MarketRegimeInput

class MarketRegimeEngine:

    # Configurable weights (must sum to 1.0)
    WEIGHTS = {
        "options": 0.30,
        "liquidity": 0.25,
        "volume": 0.15,
        "breadth": 0.15,
        "macro": 0.15
    }

    def __init__(self, db: Session):
        self.db = db

    def get_current_regime(self, target_date: date | None = None) -> MarketRegimeScore:
        score_date = target_date or date.today()
        existing = self.db.scalar(
            select(MarketRegimeScore)
            .where(MarketRegimeScore.score_date == score_date)
            .order_by(MarketRegimeScore.created_at.desc(), MarketRegimeScore.id.desc())
            .limit(1)
        )
        if existing is not None:
            return existing
        return self.calculate_regime_score(score_date)

    def _get_latest_input(self, metric_name: str, target_date: date) -> MarketRegimeInput | None:
        """Fetch the latest input for a given metric up to target_date."""
        stmt = (
            select(MarketRegimeInput)
            .where(MarketRegimeInput.metric_name == metric_name)
            .where(MarketRegimeInput.as_of_date <= target_date)
            .order_by(MarketRegimeInput.as_of_date.desc(), MarketRegimeInput.id.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def calculate_regime_score(self, target_date: date | None = None) -> MarketRegimeScore:
        """
        Calculates the Market Regime Score based on the latest available inputs.
        Gracefully handles missing data by not calculating an overall score if any component is missing.
        """
        if target_date is None:
            target_date = date.today()

        metrics = ["options", "liquidity", "volume", "breadth", "macro"]
        scores = {}
        missing_modules = []
        live_modules = []

        for metric in metrics:
            latest = self._get_latest_input(metric, target_date)
            if latest:
                scores[metric] = latest.value
                live_modules.append(metric.capitalize())
            else:
                scores[metric] = None
                missing_modules.append(metric.capitalize())

        options = scores["options"]
        liquidity = scores["liquidity"]
        volume = scores["volume"]
        breadth = scores["breadth"]
        macro = scores["macro"]

        overall = 0.0
        confidence = "high"
        mode = "Live"
        warnings = []

        if len(missing_modules) > 0:
            confidence = "invalid"
            mode = "Incomplete"
            warnings.append(f"Missing data for modules: {', '.join(missing_modules)}. Cannot calculate overall score.")
            overall = 0.0
        else:
            overall = (
                options * self.WEIGHTS["options"] +
                liquidity * self.WEIGHTS["liquidity"] +
                volume * self.WEIGHTS["volume"] +
                breadth * self.WEIGHTS["breadth"] +
                macro * self.WEIGHTS["macro"]
            )
            warnings.append(f"Formula: Sum of (Module Score × Weight). Weights: {self.WEIGHTS}")

        score = MarketRegimeScore(
            score_date=target_date,
            options_score=options,
            liquidity_score=liquidity,
            volume_score=volume,
            breadth_score=breadth,
            macro_score=macro,
            overall_score=overall,
            confidence=confidence,
            warnings=warnings,
            mode=mode,
            live_modules=live_modules,
            manual_modules=[],
            simulated_modules=[]
        )

        self.db.add(score)
        self.db.commit()
        self.db.refresh(score)
        return score
