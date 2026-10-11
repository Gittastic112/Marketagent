"""Private research context must follow the persisted portfolio/model owner."""
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import select

from app.models import (
    Alert, Company, DcfAssumptionSet, DcfOutput, Event, MarketPrice, Portfolio,
    PortfolioHolding, ThesisNote, User, ValuationModel,
)
from app.models.dcf import ValuationAssumptionChangeLog
from app.services.portfolio_valuation import calculate_portfolio_valuation
from app.services.valuation_alert_service import generate_valuation_alert


@pytest.fixture
def private_context(db):
    company = Company(ticker="CTX", name="Mock Data", currency="USD")
    db.add_all([company, User(id="context-other", email="context@example.invalid")])
    db.flush()
    contexts = []
    for owner, value, status in [
        ("admin_user_id_fallback", 120, "active"),
        ("context-other", 999, "broken"),
    ]:
        portfolio = Portfolio(user_id=owner, name="Mock Data", base_currency="USD")
        model = ValuationModel(user_id=owner, company_id=company.id, name="Mock Data")
        db.add_all([portfolio, model])
        db.flush()
        assumption = DcfAssumptionSet(
            valuation_model_id=model.id, scenario="Base", cash_flow_currency="USD",
        )
        db.add(assumption)
        db.flush()
        db.add_all([
            PortfolioHolding(portfolio_id=portfolio.id, company_id=company.id,
                             ticker="CTX", quantity=1, average_cost=100,
                             currency="USD", as_of_date=date.today()),
            DcfOutput(assumption_set_id=assumption.id, intrinsic_value_per_share=value,
                      model_quality_score=90, warnings_json=[]),
            ThesisNote(user_id=owner, company_id=company.id, title="Mock Data",
                       thesis_text="Private context", status=status,
                       updated_at=datetime(2026, 1, len(contexts) + 1, tzinfo=timezone.utc)),
            Alert(user_id=owner, company_id=company.id, alert_type="filing",
                  severity="medium", title="Mock Data"),
        ])
        contexts.append((portfolio, model, assumption))
    event = Event(company_id=company.id, event_type="filing", information_speed="slow", title="Mock Data")
    db.add_all([event, MarketPrice(company_id=company.id, ticker="CTX", price=100,
                                  currency="USD", as_of_date=date.today())])
    db.commit()
    return company, event, contexts


def test_valuation_derives_private_context_from_portfolio_owner(db, private_context):
    _, _, contexts = private_context
    portfolio, _, _ = contexts[0]
    row = calculate_portfolio_valuation(db, portfolio.id)["holdings"][0]
    assert row["intrinsic_value"] == 120
    assert row["thesis_status"] == "active"
    assert row["active_alerts_count"] == 1


def test_valuation_rejects_mismatched_explicit_owner(db, private_context):
    _, _, contexts = private_context
    with pytest.raises(ValueError, match="not found"):
        calculate_portfolio_valuation(db, contexts[0][0].id, user_id="context-other")


@pytest.mark.parametrize("owner_index", [0, 1])
def test_event_valuation_alert_uses_model_owner_for_alert_and_impacts(db, private_context, owner_index):
    _, event, contexts = private_context
    portfolio, _, assumption = contexts[owner_index]
    alert = generate_valuation_alert(db, event.id, assumption.id)
    assert alert.user_id == portfolio.user_id
    assert [impact.portfolio_id for impact in alert.portfolio_impacts] == [portfolio.id]


def test_event_valuation_alert_rejects_unrelated_company(db, private_context):
    _, event, contexts = private_context
    other = Company(ticker="OTHERCTX", name="Mock Data")
    db.add(other)
    db.flush()
    event.company_id = other.id
    db.commit()
    before = list(db.scalars(select(Alert.id)))
    with pytest.raises(ValueError, match="company"):
        generate_valuation_alert(db, event.id, contexts[0][2].id)
    assert list(db.scalars(select(Alert.id))) == before


def test_event_valuation_alert_rejects_unrelated_change_log(db, private_context):
    _, event, contexts = private_context
    _, other_model, other_assumption = contexts[1]
    change = ValuationAssumptionChangeLog(
        valuation_model_id=other_model.id, assumption_set_id=other_assumption.id,
        event_id=event.id, parameter_name="revenue_growth", rationale="Private context",
    )
    db.add(change)
    db.commit()
    before = list(db.scalars(select(Alert.id)))
    with pytest.raises(ValueError, match="Change log"):
        generate_valuation_alert(db, event.id, contexts[0][2].id, change.id)
    assert list(db.scalars(select(Alert.id))) == before
