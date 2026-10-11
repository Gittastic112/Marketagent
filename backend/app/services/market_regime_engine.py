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
    FRESHNESS_DAYS = {
        "options": 2,
        "liquidity": 2,
        "volume": 2,
        "breadth": 2,
        "macro": 31,
    }
    FORMULA = "overall = options×0.30 + liquidity×0.25 + volume×0.15 + breadth×0.15 + macro×0.15"

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
        manual_modules = []
        stale_modules = []
        input_sources = []

        for metric in metrics:
            latest = self._get_latest_input(metric, target_date)
            if latest:
                scores[metric] = latest.value
                module_name = metric.capitalize()
                if latest.input_type == "provider":
                    live_modules.append(module_name)
                else:
                    manual_modules.append(module_name)
                age_days = (target_date - latest.as_of_date).days
                if age_days > self.FRESHNESS_DAYS[metric]:
                    stale_modules.append(module_name)
                input_sources.append(
                    {
                        "input_id": latest.id,
                        "metric_name": metric,
                        "value": latest.value,
                        "as_of_date": latest.as_of_date.isoformat(),
                        "age_days": age_days,
                        "freshness_threshold_days": self.FRESHNESS_DAYS[metric],
                        "input_type": latest.input_type,
                        "source_name": latest.source_name,
                        "source_url": latest.source_url,
                        "methodology": latest.methodology,
                        "claim_type": (
                            "Calculation"
                            if latest.source_record_id is not None
                            else "Source Summary"
                            if latest.input_type == "provider"
                            else "User Assumption"
                        ),
                        "evidence_state": (
                            "linked_record"
                            if latest.source_record_id is not None
                            else "declared_source"
                            if latest.input_type == "provider"
                            else "manual_assumption"
                        ),
                        "source_record_type": latest.source_record_type,
                        "source_record_id": latest.source_record_id,
                    }
                )
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
        blockers = []
        calculation_status = "complete"

        if len(missing_modules) > 0:
            confidence = "invalid"
            mode = "Incomplete"
            calculation_status = "blocked"
            blockers.append(f"Missing inputs for: {', '.join(missing_modules)}.")
            warnings.append("Overall score is unavailable until every weighted module has an input.")
            overall = 0.0
        else:
            overall = (
                options * self.WEIGHTS["options"] +
                liquidity * self.WEIGHTS["liquidity"] +
                volume * self.WEIGHTS["volume"] +
                breadth * self.WEIGHTS["breadth"] +
                macro * self.WEIGHTS["macro"]
            )
            if stale_modules:
                calculation_status = "stale"
                confidence = "low"
                mode = "Stale"
                warnings.append(f"Stale inputs: {', '.join(stale_modules)}. Refresh before using the score for timing decisions.")
            elif manual_modules and live_modules:
                confidence = "medium"
                mode = "Mixed"
            elif manual_modules:
                confidence = "medium"
                mode = "Manual"
            else:
                confidence = "high"
                mode = "Live"

        score = MarketRegimeScore(
            score_date=target_date,
            options_score=options,
            liquidity_score=liquidity,
            volume_score=volume,
            breadth_score=breadth,
            macro_score=macro,
            overall_score=overall,
            confidence=confidence,
            calculation_status=calculation_status,
            formula=self.FORMULA,
            blockers=blockers,
            input_sources=input_sources,
            warnings=warnings,
            mode=mode,
            live_modules=live_modules,
            manual_modules=manual_modules,
            simulated_modules=[]
        )

        self.db.add(score)
        self.db.commit()
        self.db.refresh(score)
        return score
