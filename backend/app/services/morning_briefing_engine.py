from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Alert,
    DailyBrief,
    Event,
    MarketPrice,
    Portfolio,
    PortfolioHolding,
    ProcessingRun,
    ThesisNote,
)
from app.services.contradiction_detector import detect_thesis_contradiction
from app.services.dcf_variable_mapper import map_event_to_dcf_variables
from app.services.brief_private_context import snapshot_private_research


PRICE_LOOKBACK_DAYS = 14
STALE_PRICE_DAYS = 3
STALE_EVENT_DAYS = 7


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _event_evidence(event: Event) -> dict[str, Any]:
    document = event.raw_document
    source = document.source if document is not None else None
    return {
        "raw_document_id": document.id if document is not None else None,
        "source_name": source.name if source is not None else None,
        "source_url": document.url if document is not None else None,
        "source_published_at": _iso(document.published_at) if document is not None else None,
        "event_created_at": _iso(event.created_at),
        "claim_type": "Source Summary" if document is not None else "User Assumption",
        "evidence_status": "source_linked" if document is not None else "manual",
    }


def _event_status(event: Event, target_date: date, unresolved_event_ids: set[int]) -> str:
    if event.id in unresolved_event_ids:
        return "Unresolved"
    timestamp = (
        event.raw_document.published_at
        if event.raw_document is not None and event.raw_document.published_at is not None
        else event.event_time or event.created_at
    )
    if timestamp is not None and (target_date - timestamp.date()).days > STALE_EVENT_DAYS:
        return "Stale"
    return "New"


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
        # GET remains deterministic. External AI runs only after the explicit POST action.
        return MorningBriefingEngine.generate_briefing(
            db,
            user_id,
            brief_date,
            allow_generation=False,
        )

    @staticmethod
    def _owned_holding_contexts(
        db: Session,
        user_id: str,
    ) -> tuple[dict[int, list[PortfolioHolding]], dict[str, list[PortfolioHolding]]]:
        holdings = list(
            db.scalars(
                select(PortfolioHolding)
                .options(selectinload(PortfolioHolding.portfolio))
                .join(Portfolio)
                .where(Portfolio.user_id == user_id, PortfolioHolding.quantity > 0)
                .order_by(PortfolioHolding.id)
            )
        )
        by_company: dict[int, list[PortfolioHolding]] = {}
        by_ticker: dict[str, list[PortfolioHolding]] = {}
        for holding in holdings:
            if holding.company_id is not None:
                by_company.setdefault(holding.company_id, []).append(holding)
            by_ticker.setdefault(holding.ticker.upper(), []).append(holding)
        return by_company, by_ticker

    @staticmethod
    def _price_histories(
        db: Session,
        events: list[Event],
        held_by_company: dict[int, list[PortfolioHolding]],
        held_by_ticker: dict[str, list[PortfolioHolding]],
        target_date: date,
    ) -> tuple[dict[int, list[MarketPrice]], dict[str, list[MarketPrice]]]:
        company_ids = {
            event.company_id
            for event in events
            if event.company_id is not None and event.company_id in held_by_company
        }
        tickers = {
            event.company.ticker.upper()
            for event in events
            if event.company is not None
            and event.company.ticker
            and event.company.ticker.upper() in held_by_ticker
        }
        if not company_ids and not tickers:
            return {}, {}
        conditions = []
        if company_ids:
            conditions.append(MarketPrice.company_id.in_(company_ids))
        if tickers:
            conditions.append(MarketPrice.ticker.in_(tickers))
        prices = list(
            db.scalars(
                select(MarketPrice)
                .where(
                    or_(*conditions),
                    MarketPrice.as_of_date <= target_date,
                    MarketPrice.as_of_date >= target_date - timedelta(days=PRICE_LOOKBACK_DAYS),
                )
                .order_by(MarketPrice.as_of_date.desc(), MarketPrice.id.desc())
            )
        )
        by_company: dict[int, list[MarketPrice]] = {}
        by_ticker: dict[str, list[MarketPrice]] = {}
        for price in prices:
            if price.company_id is not None:
                by_company.setdefault(price.company_id, []).append(price)
            by_ticker.setdefault(price.ticker.upper(), []).append(price)
        return by_company, by_ticker

    @staticmethod
    def _portfolio_move(
        event: Event,
        holdings: list[PortfolioHolding],
        prices: list[MarketPrice],
        target_date: date,
    ) -> dict[str, Any]:
        unique_dates: list[MarketPrice] = []
        seen_dates: set[date] = set()
        for price in prices:
            if price.as_of_date in seen_dates:
                continue
            unique_dates.append(price)
            seen_dates.add(price.as_of_date)
            if len(unique_dates) == 2:
                break
        latest = unique_dates[0] if unique_dates else None
        previous = unique_dates[1] if len(unique_dates) > 1 else None
        warnings: list[str] = []
        move_percent = None
        status = "not_available"
        if latest is None or previous is None:
            warnings.append("Two distinct dated market prices are required; no zero move was inferred.")
        elif latest.currency.upper() != previous.currency.upper():
            warnings.append("The two market prices use different currencies, so the move is unavailable.")
        elif float(previous.price) <= 0:
            warnings.append("The earlier market price is not positive, so the move is unavailable.")
        else:
            move_percent = ((float(latest.price) / float(previous.price)) - 1.0) * 100.0
            age_days = (target_date - latest.as_of_date).days
            if age_days > STALE_PRICE_DAYS:
                status = "stale"
                warnings.append(f"The latest market price is {age_days} days old.")
            else:
                status = "complete"
        affected_portfolios = sorted(
            {(holding.portfolio_id, holding.portfolio.name) for holding in holdings}
        )
        source_prices = list(reversed(unique_dates))
        contains_mock_data = any(
            (price.price_type or "").strip().lower() == "mock data"
            or "mock" in (price.provider_name or "").lower()
            for price in source_prices
        )
        return {
            "ticker": event.company.ticker.upper() if event.company else holdings[0].ticker.upper(),
            "event_headline": event.title,
            "event_id": event.id,
            "move_percent": move_percent,
            "calculation_status": status,
            "claim_type": "Calculation" if move_percent is not None else "Unavailable",
            "price_start_date": previous.as_of_date.isoformat() if previous is not None else None,
            "price_end_date": latest.as_of_date.isoformat() if latest is not None else None,
            "price_currency": latest.currency if latest is not None else None,
            "price_provider": latest.provider_name if latest is not None else None,
            "source_market_price_ids": [price.id for price in source_prices],
            "affected_portfolios": [
                {"portfolio_id": portfolio_id, "portfolio_name": portfolio_name}
                for portfolio_id, portfolio_name in affected_portfolios
            ],
            "warnings": warnings,
            "contains_mock_data": contains_mock_data,
        }

    @staticmethod
    def build_briefing_payload(
        db: Session,
        user_id: str,
        events: list[Event],
        thesis_notes: list[ThesisNote],
        *,
        allow_generation: bool = True,
        include_portfolio_moves: bool = True,
        persisted_alerts: list[Alert] | None = None,
        as_of_date: date | None = None,
        last_reviewed_at: datetime | None = None,
        processing_failures: list[ProcessingRun] | None = None,
    ) -> dict[str, Any]:
        target_date = as_of_date or date.today()
        existing_contradictions = [
            alert
            for alert in (persisted_alerts or [])
            if alert.alert_type == "contradiction" and alert.review_status != "reviewed"
        ]
        contradiction_warnings: list[str] = []
        contradiction_mock = False
        if allow_generation:
            generated, contradiction_warnings, contradiction_mock = MorningBriefingEngine._detect_contradictions(
                db,
                events,
                thesis_notes,
                user_id,
                excluded_event_ids={
                    alert.event_id
                    for alert in existing_contradictions
                    if alert.event_id is not None
                },
            )
            contradiction_alerts = [*existing_contradictions, *generated]
            if contradiction_warnings and generated:
                contradiction_status = "partial"
            elif contradiction_warnings:
                contradiction_status = "failed"
            else:
                contradiction_status = "complete"
        else:
            contradiction_alerts = existing_contradictions
            contradiction_status = "not_run" if events and thesis_notes else "not_required"

        unresolved_event_ids = {
            alert.event_id
            for alert in contradiction_alerts
            if alert.event_id is not None and alert.review_status != "reviewed"
        }
        held_by_company: dict[int, list[PortfolioHolding]] = {}
        held_by_ticker: dict[str, list[PortfolioHolding]] = {}
        prices_by_company: dict[int, list[MarketPrice]] = {}
        prices_by_ticker: dict[str, list[MarketPrice]] = {}
        if include_portfolio_moves:
            held_by_company, held_by_ticker = MorningBriefingEngine._owned_holding_contexts(db, user_id)
            prices_by_company, prices_by_ticker = MorningBriefingEngine._price_histories(
                db,
                events,
                held_by_company,
                held_by_ticker,
                target_date,
            )

        filings: list[dict[str, Any]] = []
        high_materiality_events: list[dict[str, Any]] = []
        valuation_relevance: list[dict[str, Any]] = []
        portfolio_moves: list[dict[str, Any]] = []
        warnings = list(contradiction_warnings)
        seen_moves: set[str] = set()
        valuation_attempts = 0
        valuation_successes = 0
        contains_mock_data = contradiction_mock

        for event in events:
            ticker = event.company.ticker.upper() if event.company and event.company.ticker else None
            evidence = _event_evidence(event)
            status = _event_status(event, target_date, unresolved_event_ids)
            event_holdings = held_by_company.get(event.company_id, []) if event.company_id is not None else []
            if not event_holdings and ticker:
                event_holdings = held_by_ticker.get(ticker, [])
            if include_portfolio_moves and ticker and event_holdings and ticker not in seen_moves:
                event_prices = prices_by_company.get(event.company_id, []) if event.company_id is not None else []
                if len({price.as_of_date for price in event_prices}) < 2:
                    event_prices = prices_by_ticker.get(ticker, [])
                move = MorningBriefingEngine._portfolio_move(
                    event,
                    event_holdings,
                    event_prices,
                    target_date,
                )
                portfolio_moves.append(move)
                warnings.extend(f"{ticker}: {warning}" for warning in move["warnings"])
                contains_mock_data = contains_mock_data or move["contains_mock_data"]
                seen_moves.add(ticker)

            if "filing" in (event.event_type or "").lower():
                filings.append(
                    {
                        "ticker": ticker or "Unknown",
                        "form_type": event.event_type,
                        "headline": event.title,
                        "event_id": event.id,
                        "status": status,
                        **evidence,
                    }
                )

            if event.priority_score is not None and event.priority_score >= 80:
                high_materiality_events.append(
                    {
                        "headline": event.title,
                        "priority": "high",
                        "priority_score": event.priority_score,
                        "event_id": event.id,
                        "ticker": ticker,
                        "event_type": event.event_type,
                        "status": status,
                        **evidence,
                    }
                )
                if allow_generation:
                    valuation_attempts += 1
                    try:
                        dcf_result = map_event_to_dcf_variables(
                            db=db,
                            event_text=event.description or event.title,
                            event_id=event.id,
                            user_id=user_id,
                        )
                        if dcf_result.execution_status != "success" or dcf_result.is_blocked:
                            raise ValueError("generated output did not pass execution gates")
                        dcf_data = json.loads(dcf_result.output_text)
                        valuation_successes += 1
                        contains_mock_data = contains_mock_data or dcf_result.is_mock
                        for impact in dcf_data.get("impacted_variables", []):
                            valuation_relevance.append(
                                {
                                    "event_id": event.id,
                                    "headline": event.title,
                                    "variable": impact.get("variable_name"),
                                    "direction": impact.get("impact_direction"),
                                    "reasoning": impact.get("reasoning"),
                                    "confidence": impact.get("confidence") or dcf_result.confidence_label,
                                    "claim_type": "AI Interpretation",
                                    "ai_output_id": dcf_result.id,
                                    "model_name": dcf_result.model_name,
                                    "prompt_version": dcf_result.prompt_version,
                                    "review_status": dcf_result.human_review_status,
                                    "raw_document_id": evidence["raw_document_id"],
                                }
                            )
                    except Exception:
                        warnings.append(
                            f"Valuation mapping failed for event {event.id}; no DCF impact was inferred."
                        )

        if not high_materiality_events:
            valuation_status = "not_required"
        elif not allow_generation:
            valuation_status = "not_run"
        elif valuation_successes == valuation_attempts:
            valuation_status = "complete"
        elif valuation_successes:
            valuation_status = "partial"
        else:
            valuation_status = "failed"

        thesis_contradictions_payload = []
        for alert in contradiction_alerts:
            event = alert.event
            thesis_contradictions_payload.append(
                {
                    "assumption": (
                        alert.summary.split("assumption: ")[-1]
                        if alert.summary and "assumption: " in alert.summary
                        else "Assumption text unavailable"
                    ),
                    "evidence": alert.evidence,
                    "alert_id": alert.id,
                    "event_id": alert.event_id,
                    "raw_document_id": event.raw_document_id if event is not None else None,
                    "review_status": alert.review_status,
                    "claim_type": "AI Interpretation",
                }
            )

        inspection_queue: list[dict[str, Any]] = []
        for alert in thesis_contradictions_payload:
            inspection_queue.append(
                {
                    "action_id": f'contradiction-{alert["alert_id"]}',
                    "action_type": "review_contradiction",
                    "priority": "high",
                    "title": "Review unresolved thesis contradiction",
                    "reason": "An unresolved contradiction can change thesis confidence and requires human review.",
                    "href": f'/alerts/{alert["alert_id"]}',
                    "claim_type": "Calculation",
                    "source_event_ids": [alert["event_id"]] if alert["event_id"] is not None else [],
                    "source_raw_document_ids": [alert["raw_document_id"]] if alert["raw_document_id"] is not None else [],
                    "source_market_price_ids": [],
                    "source_alert_ids": [alert["alert_id"]],
                    "processing_run_id": None,
                }
            )
        for run in (processing_failures or []):
            inspection_queue.append(
                {
                    "action_id": f"processing-run-{run.id}",
                    "action_type": "inspect_processing_failure",
                    "priority": "high" if run.status in {"failed", "error"} else "medium",
                    "title": f"Inspect {run.run_type.replace('_', ' ')} processing run",
                    "reason": f"Run {run.id} recorded status {run.status} with {run.error_count} errors.",
                    "href": "/data-health",
                    "claim_type": "Calculation",
                    "source_event_ids": [],
                    "source_raw_document_ids": [],
                    "source_market_price_ids": [],
                    "source_alert_ids": [],
                    "processing_run_id": run.id,
                }
            )
        for move in portfolio_moves:
            if move["calculation_status"] == "complete":
                continue
            inspection_queue.append(
                {
                    "action_id": f'market-prices-{move["event_id"]}',
                    "action_type": "add_market_prices",
                    "priority": "medium",
                    "title": f'Complete price evidence for {move["ticker"]}',
                    "reason": "The held-company move could not be calculated from two distinct, current market-price records.",
                    "href": "/market-prices",
                    "claim_type": "Calculation",
                    "source_event_ids": [move["event_id"]],
                    "source_raw_document_ids": [],
                    "source_market_price_ids": move["source_market_price_ids"],
                    "source_alert_ids": [],
                    "processing_run_id": None,
                }
            )
        for event in high_materiality_events:
            if event["evidence_status"] == "source_linked":
                continue
            inspection_queue.append(
                {
                    "action_id": f'event-evidence-{event["event_id"]}',
                    "action_type": "resolve_event_evidence",
                    "priority": "medium",
                    "title": f'Resolve evidence for {event["ticker"] or "event"}',
                    "reason": "This material event has no linked source document and remains a user assumption.",
                    "href": f'/events/{event["event_id"]}/evidence-resolution',
                    "claim_type": "Calculation",
                    "source_event_ids": [event["event_id"]],
                    "source_raw_document_ids": [event["raw_document_id"]] if event["raw_document_id"] is not None else [],
                    "source_market_price_ids": [],
                    "source_alert_ids": [],
                    "processing_run_id": None,
                }
            )

        summary = (
            f"{len(events)} {'event' if len(events) == 1 else 'events'} since the last reviewed brief; "
            f"{len(thesis_contradictions_payload)} unresolved contradiction alerts; "
            f"{len(portfolio_moves)} affected held companies."
        )
        return {
            "summary": summary,
            "private_research": snapshot_private_research(db, user_id, target_date),
            "calculation_status": "partial" if warnings else "complete",
            "valuation_analysis_status": valuation_status,
            "contradiction_analysis_status": contradiction_status,
            "last_reviewed_at": _iso(last_reviewed_at),
            "new_since_last_review": {
                "filings": filings,
                "portfolio_moves": portfolio_moves,
            },
            "high_materiality_events": high_materiality_events,
            "thesis_contradictions": thesis_contradictions_payload,
            "thesis_confirmations": [],
            "valuation_relevance": valuation_relevance,
            "processing_failures": [
                {
                    "processing_run_id": run.id,
                    "run_type": run.run_type,
                    "source_type": run.source_type,
                    "status": run.status,
                    "error_count": run.error_count,
                    "started_at": _iso(run.started_at),
                    "finished_at": _iso(run.finished_at),
                    "claim_type": "Fact",
                }
                for run in (processing_failures or [])
            ],
            "inspection_queue": inspection_queue[:20],
            "warnings": sorted(set(warnings)),
            "contains_mock_data": contains_mock_data,
            "contains_stale_data": (
                any(move["calculation_status"] == "stale" for move in portfolio_moves)
                or any(event["status"] == "Stale" for event in high_materiality_events)
                or any(filing["status"] == "Stale" for filing in filings)
            ),
            "source_event_ids": [event.id for event in events],
            "source_raw_document_ids": sorted(
                {event.raw_document_id for event in events if event.raw_document_id is not None}
            ),
            "source_market_price_ids": sorted(
                {
                    price_id
                    for move in portfolio_moves
                    for price_id in move["source_market_price_ids"]
                }
            ),
            "source_alert_ids": sorted(alert.id for alert in contradiction_alerts),
        }

    @staticmethod
    def generate_briefing(
        db: Session,
        user_id: str,
        target_date: date | None = None,
        *,
        allow_generation: bool = True,
    ) -> DailyBrief:
        brief_date = target_date or date.today()
        last_reviewed_brief = db.scalar(
            select(DailyBrief)
            .where(
                DailyBrief.user_id == user_id,
                DailyBrief.review_status == "reviewed",
            )
            .order_by(
                func.coalesce(DailyBrief.reviewed_at, DailyBrief.created_at).desc(),
                DailyBrief.id.desc(),
            )
            .limit(1)
        )
        last_review_date = (
            last_reviewed_brief.reviewed_at or last_reviewed_brief.created_at
            if last_reviewed_brief
            else None
        )
        event_query = (
            select(Event)
            .options(selectinload(Event.company), selectinload(Event.raw_document))
            .order_by(Event.priority_score.desc().nullslast(), Event.created_at.desc())
        )
        if last_review_date:
            event_query = event_query.where(Event.created_at > last_review_date)
        events = list(db.scalars(event_query.limit(50)))
        thesis_notes = list(
            db.scalars(
                select(ThesisNote)
                .options(selectinload(ThesisNote.assumptions))
                .where(
                    ThesisNote.user_id == user_id,
                    ThesisNote.status == "active",
                )
            )
        )
        persisted_alerts = list(
            db.scalars(
                select(Alert)
                .options(selectinload(Alert.event))
                .where(
                    Alert.user_id == user_id,
                    Alert.alert_type == "contradiction",
                    Alert.review_status != "reviewed",
                )
            )
        )
        processing_failure_query = (
            select(ProcessingRun)
            .where(
                or_(
                    ProcessingRun.status.in_(("failed", "error", "partial", "completed_with_errors")),
                    ProcessingRun.error_count > 0,
                )
            )
            .order_by(ProcessingRun.started_at.desc(), ProcessingRun.id.desc())
            .limit(10)
        )
        if last_review_date:
            processing_failure_query = processing_failure_query.where(
                ProcessingRun.started_at > last_review_date
            )
        processing_failures = list(db.scalars(processing_failure_query))
        payload = MorningBriefingEngine.build_briefing_payload(
            db,
            user_id,
            events,
            thesis_notes,
            allow_generation=allow_generation,
            persisted_alerts=persisted_alerts,
            as_of_date=brief_date,
            last_reviewed_at=last_review_date,
            processing_failures=processing_failures,
        )
        brief = DailyBrief(
            user_id=user_id,
            brief_date=brief_date,
            title="Daily Intelligence Brief",
            summary=payload["summary"],
            payload_json=payload,
        )
        db.add(brief)
        db.commit()
        db.refresh(brief)
        return brief

    @staticmethod
    def _detect_contradictions(
        db: Session,
        events: list[Event],
        thesis_notes: list[ThesisNote],
        user_id: str,
        *,
        excluded_event_ids: set[int] | None = None,
    ) -> tuple[list[Alert], list[str], bool]:
        excluded = set(excluded_event_ids or set())
        excluded.update(
            event_id
            for event_id in db.scalars(
                select(Alert.event_id).where(
                    Alert.user_id == user_id,
                    Alert.alert_type == "contradiction",
                    Alert.event_id.is_not(None),
                    Alert.review_status != "reviewed",
                )
            )
            if event_id is not None
        )
        contradiction_alerts: list[Alert] = []
        warnings: list[str] = []
        contains_mock_data = False
        for event in events:
            if event.id in excluded:
                continue
            if not (
                (event.priority_score is not None and event.priority_score >= 50)
                or "filing" in (event.event_type or "").lower()
            ):
                continue
            matching_notes = [note for note in thesis_notes if note.company_id == event.company_id]
            event_alerted = False
            for note in matching_notes:
                for assumption in note.assumptions:
                    try:
                        ai_result = detect_thesis_contradiction(
                            db=db,
                            evidence_text=event.description or event.title,
                            assumption_text=assumption.description,
                            event_id=event.id,
                            user_id=user_id,
                        )
                        if ai_result.execution_status != "success" or ai_result.is_blocked:
                            raise ValueError("generated output did not pass execution gates")
                        contains_mock_data = contains_mock_data or ai_result.is_mock
                        result_data = json.loads(ai_result.output_text)
                        if not result_data.get("is_contradiction"):
                            continue
                        alert = Alert(
                            user_id=user_id,
                            event=event,
                            company=event.company,
                            event_id=event.id,
                            company_id=event.company_id,
                            alert_type="contradiction",
                            severity="high",
                            title=f"Contradiction Alert: {event.company.ticker if event.company else 'Unknown'}",
                            summary=(
                                f"Event '{event.title}' may contradict your thesis assumption: "
                                f"{assumption.description}"
                            ),
                            why_it_matters=result_data.get(
                                "reasoning", "This may invalidate a recorded assumption."
                            ),
                            what_changed=event.title,
                            evidence=event.description,
                            confidence_bucket=result_data.get("confidence", "medium"),
                            review_status="unreviewed",
                        )
                        contradiction_alerts.append(alert)
                        db.add(alert)
                        excluded.add(event.id)
                        event_alerted = True
                        break
                    except Exception:
                        warnings.append(
                            f"Contradiction analysis failed for event {event.id}; no alert was inferred."
                        )
                if event_alerted:
                    break
        if contradiction_alerts:
            db.commit()
            for alert in contradiction_alerts:
                db.refresh(alert)
        return contradiction_alerts, sorted(set(warnings)), contains_mock_data
