from sqlalchemy.orm import Session
from app.models.decision_journal import DecisionLog, OutcomeReview
from typing import Dict, Any


class ForecastLearningEngine:

    @staticmethod
    def log_decision(db: Session, user_id: str, company_id: int, decision_data: Dict[str, Any]) -> DecisionLog:
        """
        Creates a DecisionLog acting as a snapshot of research memory.
        """
        log = DecisionLog(
            user_id=user_id,
            company_id=company_id,
            decision_type=decision_data.get("decision_type", "Unknown"),
            rationale=decision_data.get("rationale", ""),
            price_at_time=decision_data.get("price_at_time"),
            emotional_state=decision_data.get("emotional_state"),
            alternatives_considered=decision_data.get("alternatives_considered"),

            # Stage 14 fields
            current_thesis=decision_data.get("current_thesis"),
            valuation=decision_data.get("valuation"),
            decision_readiness=decision_data.get("decision_readiness"),
            key_supporting_evidence=decision_data.get("key_supporting_evidence"),
            key_contradictory_evidence=decision_data.get("key_contradictory_evidence"),
            uncertainties=decision_data.get("uncertainties"),
            expected_catalysts=decision_data.get("expected_catalysts"),
            what_would_change_the_view=decision_data.get("what_would_change_the_view"),
            portfolio_context=decision_data.get("portfolio_context")
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def review_outcome(db: Session, decision_log_id: int, outcome_data: Dict[str, Any]) -> OutcomeReview:
        """
        Creates an OutcomeReview for a past decision to serve as a structured calibration dataset.
        """
        review = OutcomeReview(
            decision_log_id=decision_log_id,
            what_happened=outcome_data.get("what_happened", ""),
            wrong_assumption=outcome_data.get("wrong_assumption"),
            information_unavailable_or_misinterpreted=outcome_data.get("information_unavailable_or_misinterpreted", False),
            valuation_wrong=outcome_data.get("valuation_wrong", False),
            thesis_wrong=outcome_data.get("thesis_wrong", False),
            timing_wrong=outcome_data.get("timing_wrong", False),
            sizing_wrong=outcome_data.get("sizing_wrong", False),
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return review
