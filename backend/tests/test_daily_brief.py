from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import (
    Alert,
    Company,
    DailyBrief,
    Event,
    MarketPrice,
    Portfolio,
    PortfolioHolding,
    RawDocument,
    Source,
    ThesisNote,
    User,
)
from app.services.morning_briefing_engine import MorningBriefingEngine


USER_ID = "brief-owner"


@pytest.mark.parametrize("name,description,is_mock", [
    ("Technology Portfolio | Sample", "Hypothetical activity", True),
    ("Technology Portfolio", "Mock Data: hypothetical allocation", True),
    ("Technology Portfolio", "An actual account", False),
])
def test_real_market_prices_do_not_hide_explicit_sample_holdings(name, description, is_mock):
    company = Company(ticker="AAPL", name="Apple")
    portfolio = Portfolio(id=1, name=name, description=description, base_currency="USD")
    holding = PortfolioHolding(portfolio=portfolio, portfolio_id=1, ticker="AAPL", quantity=1, currency="USD")
    event = Event(company=company, id=1, title="A sourced event")
    prices = [MarketPrice(id=2, ticker="AAPL", price=110, currency="USD", provider_name="official",
        price_type="end_of_day", as_of_date=date(2026, 1, 2)),
        MarketPrice(id=1, ticker="AAPL", price=100, currency="USD", provider_name="official",
        price_type="end_of_day", as_of_date=date(2026, 1, 1))]
    move = MorningBriefingEngine._portfolio_move(event, [holding], prices, date(2026, 1, 2))
    assert move["move_percent"] == pytest.approx(10)
    assert move["contains_mock_data"] is is_mock
    assert any("sample holdings" in note for note in move["provenance_notes"]) is is_mock
    assert move["warnings"] == []
    assert move["calculation_status"] == "complete"


def test_sample_provenance_does_not_mean_missing_brief_inputs(client, db_session):
    from helpers import response_data
    from app.services.brief_public_coverage import public_coverage_context
    company = response_data(client.post("/companies", json={"ticker": "SAMPLE", "name": "Sample company"}))
    portfolio = response_data(client.post("/portfolios", json={"name": "Technology | Sample"}))
    event = Event(company_id=company["id"], title="Stored sample event", event_type="manual", information_speed="slow", priority_score=0)
    db_session.add(event)
    db_session.add(PortfolioHolding(portfolio_id=portfolio["id"], company_id=company["id"], ticker="SAMPLE",
        quantity=1, average_cost=100, currency="USD", as_of_date=date(2026, 1, 1)))
    for day, price in [(1, 100), (2, 110)]:
        db_session.add(MarketPrice(company_id=company["id"], ticker="SAMPLE", price=price, currency="USD",
            provider_name="official", as_of_date=date(2026, 1, day)))
    db_session.commit()
    now = datetime.now(timezone.utc)
    coverage = public_coverage_context(captured_at=now, start=None, end=now, basis="since_last_review",
        event_total=1, event_included=1, event_cap=100, failed_run_total=0, failed_run_included=0, failed_run_cap=10)
    payload = MorningBriefingEngine.build_briefing_payload(db_session, "admin_user_id_fallback", [event], [],
        allow_generation=False, as_of_date=date(2026, 1, 2), public_coverage=coverage)
    assert payload["contains_mock_data"] is True
    assert payload["calculation_status"] == "complete"
    assert payload["warnings"] == []
    assert "sample holdings" in payload["provenance_notes"][0]


def test_generate_daily_brief_ranks_events_and_preserves_evidence() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        company = Company(ticker="AAPL", name="Apple Inc.")
        source = Source(name="SEC EDGAR", source_type="filing", reliability_score=95)
        raw_document = RawDocument(
            company=company,
            source=source,
            document_type="filing",
            title="Apple 10-Q",
            url="https://www.sec.gov/example",
            published_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
            raw_text="Risk factor language changed.",
            content_hash="brief-hash-1",
        )
        high_priority_event = Event(
            company=company,
            raw_document=raw_document,
            event_type="filing_change",
            information_speed="slow",
            title="Risk factor language changed",
            description="Supply chain risk language changed.",
            credibility_score=95,
            novelty_score=80,
            impact_score=75,
            priority_score=84,
        )
        lower_priority_event = Event(
            company=company,
            event_type="manual_event",
            information_speed="medium",
            title="Lower priority manual event",
            priority_score=20,
        )
        alert = Alert(
            user_id=USER_ID,
            company=company,
            event=high_priority_event,
            alert_type="source_backed_change",
            severity="medium",
            title="Review Apple filing change",
            confidence_bucket="high",
        )
        thesis_note = ThesisNote(
            user_id=USER_ID,
            company=company,
            title="Apple base thesis",
            thesis_text="Services growth remains important.",
        )

        session.add_all([company, source, raw_document, high_priority_event, lower_priority_event, alert, thesis_note])
        session.commit()
        raw_document_id = raw_document.id
        high_priority_event_id = high_priority_event.id
        lower_priority_event_id = lower_priority_event.id

        session.add_all(
            [
                Alert(
                    user_id="another-user",
                    company=company,
                    alert_type="private_alert",
                    severity="high",
                    title="Another user's alert",
                ),
                ThesisNote(
                    user_id="another-user",
                    company=company,
                    title="Another user's thesis",
                    thesis_text="Private thesis content.",
                ),
            ]
        )
        session.commit()

        brief_orm = MorningBriefingEngine.generate_briefing(session, user_id=USER_ID)
        brief = brief_orm.payload_json

    assert brief_orm.title == "Daily Intelligence Brief"
    assert brief_orm.review_status == "new"

    # We should have high_materiality_events
    high_mat = brief["high_materiality_events"]
    assert len(high_mat) > 0
    assert high_mat[0]["headline"] == "Risk factor language changed"
    assert high_mat[0]["priority"] == "high"
    assert high_mat[0]["raw_document_id"] == raw_document_id
    assert high_mat[0]["source_name"] == "SEC EDGAR"
    assert high_mat[0]["claim_type"] == "Source Summary"
    assert high_mat[0]["evidence_status"] == "source_linked"
    assert brief["source_event_ids"] == [high_priority_event_id, lower_priority_event_id]
    assert brief["source_raw_document_ids"] == [raw_document_id]


def test_generate_daily_brief_respects_last_review_date() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Create an old reviewed brief
        old_brief = DailyBrief(
            user_id=USER_ID,
            brief_date=date(2026, 1, 1),
            title="Old Brief",
            summary="Old",
            payload_json={},
            review_status="reviewed",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            reviewed_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        session.add(old_brief)
        session.commit()

        # Event created after brief creation but before the actual review should be ignored.
        company = Company(ticker="AAPL", name="Apple Inc.")
        event_old = Event(
            company=company,
            event_type="manual",
            information_speed="medium",
            title="Old Event",
            priority_score=90,
            created_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )
        # Event created after review should be included
        event_new = Event(
            company=company,
            event_type="manual",
            information_speed="medium",
            title="New Event",
            priority_score=90,
            created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        )
        session.add_all([company, event_old, event_new])
        session.commit()

        # Generate brief
        new_brief_orm = MorningBriefingEngine.generate_briefing(session, user_id=USER_ID)
        new_brief = new_brief_orm.payload_json

    # Should only contain 'New Event'
    high_mat = new_brief["high_materiality_events"]
    assert len(high_mat) == 1
    assert high_mat[0]["headline"] == "New Event"
    assert new_brief["last_reviewed_at"].startswith("2026-03-01")


def test_briefing_never_invents_zero_portfolio_move_and_keeps_source_context() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(id=USER_ID, email="brief-owner@example.invalid", name="Brief Owner")
        company = Company(ticker="MOVE", name="Move Company")
        source = Source(name="Official Filing Source", source_type="filing", reliability_score=95)
        document = RawDocument(
            company=company,
            source=source,
            document_type="filing",
            title="MOVE annual filing",
            url="https://example.invalid/move-filing",
            published_at=datetime(2026, 8, 22, tzinfo=timezone.utc),
            raw_text="Revenue growth slowed.",
            content_hash="brief-move-source",
        )
        event = Event(
            company=company,
            raw_document=document,
            event_type="SEC Filing",
            information_speed="slow",
            title="MOVE filing update",
            description="Revenue growth slowed.",
            priority_score=90,
            created_at=datetime(2026, 8, 22, tzinfo=timezone.utc),
        )
        portfolio = Portfolio(user_id=USER_ID, name="Core", base_currency="USD")
        session.add_all([user, company, source, document, event, portfolio])
        session.flush()
        session.add(PortfolioHolding(
            portfolio_id=portfolio.id,
            company_id=company.id,
            ticker="MOVE",
            quantity=4,
            average_cost=95,
            currency="USD",
            as_of_date=date(2026, 8, 23),
        ))
        only_price = MarketPrice(
            company_id=company.id,
            ticker="MOVE",
            price=100,
            currency="USD",
            as_of_date=date(2026, 8, 23),
            provider_name="manual",
        )
        session.add(only_price)
        session.commit()

        unavailable = MorningBriefingEngine.build_briefing_payload(
            session,
            USER_ID,
            [event],
            [],
            allow_generation=False,
            as_of_date=date(2026, 8, 23),
        )

        move = unavailable["new_since_last_review"]["portfolio_moves"][0]
        assert move["move_percent"] is None
        assert move["calculation_status"] == "not_available"
        assert move["source_market_price_ids"] == [only_price.id]
        assert move["affected_portfolios"] == [
            {"portfolio_id": portfolio.id, "portfolio_name": "Core"}
        ]
        assert unavailable["calculation_status"] == "partial"
        assert unavailable["high_materiality_events"][0]["raw_document_id"] == document.id
        assert unavailable["new_since_last_review"]["filings"][0]["event_id"] == event.id

        previous_price = MarketPrice(
            company_id=company.id,
            ticker="MOVE",
            price=95,
            currency="USD",
            as_of_date=date(2026, 8, 22),
            provider_name="manual",
        )
        session.add(previous_price)
        session.commit()

        complete = MorningBriefingEngine.build_briefing_payload(
            session,
            USER_ID,
            [event],
            [],
            allow_generation=False,
            as_of_date=date(2026, 8, 23),
        )
        move = complete["new_since_last_review"]["portfolio_moves"][0]
        assert move["move_percent"] == pytest.approx((100 / 95 - 1) * 100)
        assert move["calculation_status"] == "complete"
        assert move["source_market_price_ids"] == [previous_price.id, only_price.id]


def test_briefing_exposes_valuation_generation_failure(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        company = Company(ticker="FAIL", name="Failure Company")
        event = Event(
            company=company,
            event_type="manual_event",
            information_speed="fast",
            title="Material event",
            description="Material evidence",
            priority_score=90,
        )
        session.add_all([company, event])
        session.commit()

        def fail_mapping(**_kwargs):
            raise RuntimeError("provider unavailable")

        monkeypatch.setattr(
            "app.services.morning_briefing_engine.map_event_to_dcf_variables",
            fail_mapping,
        )
        payload = MorningBriefingEngine.build_briefing_payload(
            session,
            USER_ID,
            [event],
            [],
            allow_generation=True,
            include_portfolio_moves=False,
            as_of_date=date(2026, 8, 23),
        )

    assert payload["valuation_analysis_status"] == "failed"
    assert payload["valuation_relevance"] == []
    assert any("Valuation mapping failed" in warning for warning in payload["warnings"])
