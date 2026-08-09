from datetime import date
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.models import Alert, DailyBrief, Event, ThesisNote, Portfolio, PortfolioHolding
from app.services.contradiction_detector import detect_thesis_contradiction
from app.services.dcf_variable_mapper import map_event_to_dcf_variables
from app.services.portfolio_valuation import get_latest_price
from datetime import date, timedelta
import json

class MorningBriefingEngine:
    @staticmethod
    def get_or_generate_briefing(
        db: Session,
        user_id: str,
        target_date: date | None = None,
    ) -> DailyBrief:
        brief_date = target_date or date.today()
        existing = db.scalar(
            select(DailyBrief)
            .where(
                DailyBrief.user_id == user_id,
                DailyBrief.brief_date == brief_date,
            )
            .order_by(DailyBrief.created_at.desc(), DailyBrief.id.desc())
            .limit(1)
        )
        if existing is not None:
            return existing
        return MorningBriefingEngine.generate_briefing(db, user_id, brief_date)

    @staticmethod
    def build_briefing_payload(db: Session, user_id: str, events: list[Event], thesis_notes: list[ThesisNote]) -> dict[str, Any]:
        contradiction_alerts = MorningBriefingEngine._detect_contradictions(db, events, thesis_notes, user_id)

        # 3. Query user's portfolio holdings
        user_holdings = db.scalars(
            select(PortfolioHolding)
            .join(Portfolio)
            .where(Portfolio.user_id == user_id, PortfolioHolding.quantity > 0)
        ).all()
        held_tickers = {h.ticker.upper() for h in user_holdings}

        filings = []
        high_materiality_events = []
        valuation_relevance = []
        portfolio_moves = []
        seen_moves = set()

        for event in events:
            ticker = event.company.ticker.upper() if event.company and event.company.ticker else None
            if ticker and ticker in held_tickers and ticker not in seen_moves:
                today = date.today()
                yesterday = today - timedelta(days=1)
                latest = get_latest_price(db, ticker, today)
                prev = get_latest_price(db, ticker, yesterday)
                move_pct = 0.0
                if latest and prev and prev.price > 0:
                    move_pct = ((float(latest.price) - float(prev.price)) / float(prev.price)) * 100.0

                portfolio_moves.append({
                    "ticker": ticker,
                    "event_headline": event.title,
                    "event_id": event.id,
                    "move_percent": move_pct,
                })
                seen_moves.add(ticker)

            if event.priority_score and event.priority_score >= 80:
                high_materiality_events.append({
                    "headline": event.title,
                    "priority": "high",
                    "event_id": event.id,
                })
                # Check for valuation impact
                try:
                    dcf_result = map_event_to_dcf_variables(
                        db=db,
                        event_text=event.description or event.title,
                        event_id=event.id,
                        user_id=user_id,
                    )
                    dcf_data = json.loads(dcf_result.output_text)
                    if dcf_data.get("impacted_variables"):
                        for impact in dcf_data["impacted_variables"]:
                            valuation_relevance.append({
                                "event_id": event.id,
                                "headline": event.title,
                                "variable": impact.get("variable_name"),
                                "direction": impact.get("impact_direction"),
                                "reasoning": impact.get("reasoning")
                            })
                except Exception:
                    pass
            elif event.event_type == "filing" or event.event_type == "SEC Filing":
                filings.append({
                    "ticker": event.company.ticker if event.company else "Unknown",
                    "form_type": event.event_type,
                    "headline": event.title,
                    "event_id": event.id,
                })

        thesis_contradictions_payload = []
        for alert in contradiction_alerts:
            thesis_contradictions_payload.append({
                "assumption": alert.summary.split("assumption: ")[-1] if "assumption: " in alert.summary else "Unknown assumption",
                "evidence": alert.evidence,
                "alert_id": alert.id,
            })

        return {
            "new_since_last_review": {
                "filings": filings,
                "portfolio_moves": portfolio_moves
            },
            "high_materiality_events": high_materiality_events,
            "thesis_contradictions": thesis_contradictions_payload,
            "thesis_confirmations": [],
            "valuation_relevance": valuation_relevance
        }

    @staticmethod
    def generate_briefing(db: Session, user_id: str, target_date: date | None = None) -> DailyBrief:
        if target_date is None:
            target_date = date.today()
        # Find the last reviewed brief for the user
        last_reviewed_brief = db.scalar(
            select(DailyBrief)
            .where(DailyBrief.user_id == user_id, DailyBrief.review_status == 'reviewed')
            .order_by(DailyBrief.created_at.desc())
            .limit(1)
        )
        last_review_date = last_reviewed_brief.created_at if last_reviewed_brief else None

        # 1. Query new events
        event_query = (
            select(Event)
            .options(selectinload(Event.company), selectinload(Event.raw_document))
            .order_by(Event.priority_score.desc().nullslast(), Event.created_at.desc())
        )
        if last_review_date:
            event_query = event_query.where(Event.created_at > last_review_date)

        events = list(db.scalars(event_query.limit(50)))

        # 2. Query active thesis notes
        thesis_notes = list(
            db.scalars(
                select(ThesisNote).where(
                    ThesisNote.user_id == user_id,
                    ThesisNote.status == "active",
                )
            )
        )

        payload = MorningBriefingEngine.build_briefing_payload(db, user_id, events, thesis_notes)

        brief = DailyBrief(
            user_id=user_id,
            brief_date=target_date,
            title="Daily Intelligence Brief",
            summary=f"Market is active. {len(events)} new events processed. {len(payload['thesis_contradictions'])} thesis contradictions found.",
            payload_json=payload
        )

        db.add(brief)
        db.commit()
        db.refresh(brief)
        return brief

    @staticmethod
    def _detect_contradictions(db: Session, events: list[Event], thesis_notes: list[ThesisNote], user_id: str) -> list[Alert]:
        contradiction_alerts = []
        for event in events:
            # We want to check events that are high priority or filings
            if (event.priority_score and event.priority_score >= 50) or event.event_type in ["filing", "SEC Filing"]:
                for note in thesis_notes:
                    if note.company_id == event.company_id:
                        for assumption in note.assumptions:
                            try:
                                ai_result = detect_thesis_contradiction(
                                    db=db,
                                    evidence_text=event.description or event.title,
                                    assumption_text=assumption.description,
                                    event_id=event.id,
                                    user_id=user_id,
                                )
                                result_data = json.loads(ai_result.output_text)
                                if result_data.get("is_contradiction"):
                                    alert = Alert(
                                        user_id=user_id,
                                        event=event,
                                        company=event.company,
                                        event_id=event.id,
                                        company_id=event.company_id,
                                        alert_type="contradiction",
                                        severity="high",
                                        title=f"Contradiction Alert: {event.company.ticker if event.company else 'Unknown'}",
                                        summary=f"Event '{event.title}' may contradict your thesis assumption: {assumption.description}",
                                        why_it_matters=result_data.get("reasoning", "This could invalidate your base valuation."),
                                        what_changed=event.title,
                                        evidence=event.description,
                                        confidence_bucket=result_data.get("confidence", "medium"),
                                        review_status="unreviewed",
                                    )
                                    contradiction_alerts.append(alert)
                                    db.add(alert)
                                    break # Only one alert per event/note is enough for the brief
                            except Exception:
                                pass

                        if any(a.event_id == event.id for a in contradiction_alerts):
                            break

        if contradiction_alerts:
            db.commit()
            for alert in contradiction_alerts:
                db.refresh(alert)
        return contradiction_alerts
