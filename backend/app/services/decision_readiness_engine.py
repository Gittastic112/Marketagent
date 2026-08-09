from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Company,
    DecisionReadiness,
    FinancialStatementPeriod,
    ValuationModel,
    ThesisNote,
    Event,
)


class DecisionReadinessEngine:
    @staticmethod
    def evaluate(db: Session, company_id: int) -> DecisionReadiness:
        # Check if record exists
        readiness = db.scalar(
            select(DecisionReadiness).where(DecisionReadiness.company_id == company_id)
        )
        if not readiness:
            readiness = DecisionReadiness(company_id=company_id)
            db.add(readiness)

        blocking_issues = []

        # 1. Financial Readiness
        # Require at least one annual financial statement period
        financial_count = db.scalar(
            select(FinancialStatementPeriod.id)
            .where(
                FinancialStatementPeriod.company_id == company_id,
                FinancialStatementPeriod.period_type == "annual"
            )
            .limit(1)
        )
        readiness.financial_ready = bool(financial_count)
        if not readiness.financial_ready:
            blocking_issues.append("Missing annual financial statements.")

        # 2. Valuation Readiness
        # Should we forcibly block Valuation if Financial is missing? The plan question asks this.
        # For now, we evaluate it independently. Require at least one ValuationModel.
        valuation_count = db.scalar(
            select(ValuationModel.id)
            .where(ValuationModel.company_id == company_id)
            .limit(1)
        )
        readiness.valuation_ready = bool(valuation_count)
        if not readiness.valuation_ready:
            blocking_issues.append("No valuation model found.")

        # 3. Thesis Readiness
        # Require at least one active thesis note.
        thesis_count = db.scalar(
            select(ThesisNote.id)
            .where(
                ThesisNote.company_id == company_id,
                ThesisNote.status == "active"
            )
            .limit(1)
        )
        readiness.thesis_ready = bool(thesis_count)
        if not readiness.thesis_ready:
            blocking_issues.append("No active thesis note.")

        # 4. Evidence Readiness
        # Require at least one event linked to the company
        event_count = db.scalar(
            select(Event.id)
            .where(Event.company_id == company_id)
            .limit(1)
        )
        readiness.evidence_ready = bool(event_count)
        if not readiness.evidence_ready:
            blocking_issues.append("No evidence/events linked to company.")

        # 5. Portfolio Readiness
        # Check if there are active holdings (simplification: assume True if not checked)
        # We can set this to false by default unless an integration exists.
        readiness.portfolio_ready = False
        blocking_issues.append("Portfolio position tracking not verified.")

        # 6. Catalyst Readiness
        # Could be based on upcoming events.
        readiness.catalyst_ready = False
        blocking_issues.append("No upcoming catalysts identified.")

        readiness.blocking_issues_json = blocking_issues

        # Overall Status Logic
        score = sum([
            readiness.financial_ready,
            readiness.valuation_ready,
            readiness.thesis_ready,
            readiness.evidence_ready
        ])

        if score == 4:
            readiness.overall_status = "Ready"
        elif score > 0:
            readiness.overall_status = "Partial"
        else:
            readiness.overall_status = "Blocked"

        return readiness
