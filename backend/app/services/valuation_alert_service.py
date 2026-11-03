from sqlalchemy import select
from datetime import date, timedelta
from math import isfinite
from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertPortfolioImpact
from app.models.dcf import DcfAssumptionSet, ValuationAssumptionChangeLog, ValuationModel
from app.models.event import Event
from app.models.portfolio import Portfolio, PortfolioHolding


def generate_valuation_alert(
    db: Session,
    event_id: int,
    assumption_set_id: int,
    change_log_id: int | None = None
) -> Alert:
    """
    Generates an Alert when a valuation assumption is broken or becomes stale due to an event.
    """
    event = db.scalar(select(Event).where(Event.id == event_id))
    if not event:
        raise ValueError(f"Event {event_id} not found")

    assumption_set = db.scalar(select(DcfAssumptionSet).where(DcfAssumptionSet.id == assumption_set_id))
    if not assumption_set:
        raise ValueError(f"Assumption Set {assumption_set_id} not found")
    model = db.get(ValuationModel, assumption_set.valuation_model_id)
    if model is None or not model.user_id:
        raise ValueError("Owned valuation model not found")
    if event.company_id != model.company_id:
        raise ValueError("Event and valuation must refer to the same company")

    change_log = None
    if change_log_id is not None:
        change_log = db.scalar(select(ValuationAssumptionChangeLog).where(
            ValuationAssumptionChangeLog.id == change_log_id,
            ValuationAssumptionChangeLog.valuation_model_id == model.id,
            ValuationAssumptionChangeLog.assumption_set_id == assumption_set.id,
            ValuationAssumptionChangeLog.event_id == event.id,
        ))
        if change_log is None:
            raise ValueError("Change log does not match the valuation and event")

    company_id = event.company_id

    # Create the base Alert
    title = f"Valuation Stale: {event.title}"
    summary = assumption_set.stale_reason or "An event has triggered a review of current valuation assumptions."

    if change_log:
        title = f"Assumption Broken: {change_log.parameter_name}"
        summary = change_log.rationale

    alert = Alert(
        user_id=model.user_id,
        event_id=event.id,
        company_id=company_id,
        alert_type="valuation_stale" if not change_log else "assumption_broken",
        severity="high",
        title=title,
        summary=summary,
        why_it_matters="If your valuation assumption is wrong, your intrinsic value is wrong.",
        what_changed=f"Event '{event.title}' directly challenges existing assumptions.",
        confidence_bucket="medium",
        review_status="unreviewed"
    )
    db.add(alert)
    db.flush()

    # Private model context can only affect portfolios belonging to its owner.
    holdings = db.scalars(
        select(PortfolioHolding)
        .join(Portfolio, Portfolio.id == PortfolioHolding.portfolio_id)
        .where(PortfolioHolding.company_id == company_id, Portfolio.user_id == model.user_id)
    ).all()

    for holding in holdings:
        impact = AlertPortfolioImpact(
            alert_id=alert.id,
            portfolio_id=holding.portfolio_id,
            exposure_amount=float(holding.quantity * holding.average_cost), # simple cost exposure
            impact_score=8.0 # High impact since valuation is broken
        )
        db.add(impact)

    db.commit()
    return alert

def check_price_valuation_divergence(
    db: Session, company_id: int | None, *, user_id: str | None = None, commit: bool = True,
) -> list[Alert]:
    """
    Checks if there's a material divergence between the current market price and
    the intrinsic value, or if the market price has moved significantly but the
    intrinsic value has remained unchanged. Generates alerts accordingly.
    """
    if company_id is None or user_id is None:
        return []

    from app.models.market_price import MarketPrice
    from app.models.dcf import ValuationModel, DcfAssumptionSet, DcfOutput

    # Get the latest price
    latest_price_record = db.scalar(
        select(MarketPrice)
        .where(MarketPrice.company_id == company_id)
        .where(MarketPrice.as_of_date <= date.today())
        .order_by(MarketPrice.as_of_date.desc(), MarketPrice.id.desc())
        .limit(1)
    )
    if not latest_price_record or date.today() - latest_price_record.as_of_date > timedelta(days=5):
        return []

    # Get the active assumption set
    latest_assumption_set = db.scalar(
        select(DcfAssumptionSet)
        .join(ValuationModel, ValuationModel.id == DcfAssumptionSet.valuation_model_id)
        .where(ValuationModel.company_id == company_id)
        .where(ValuationModel.user_id == user_id)
        .where(DcfAssumptionSet.scenario == "Base")
        .order_by(DcfAssumptionSet.id.desc())
        .limit(1)
    )
    if not latest_assumption_set or latest_assumption_set.is_stale:
        return []

    # Get the corresponding output
    latest_output = db.scalar(
        select(DcfOutput)
        .where(DcfOutput.assumption_set_id == latest_assumption_set.id)
    )
    if (not latest_output or latest_output.intrinsic_value_per_share is None
        or latest_output.model_quality_score is None or latest_output.model_quality_score < 60
        or latest_output.warnings_json):
        return []

    alerts_created = []
    current_price = float(latest_price_record.price)
    intrinsic_value = latest_output.intrinsic_value_per_share
    currency = (latest_assumption_set.cash_flow_currency or "").upper()
    if (not currency or currency != latest_price_record.currency.upper()
        or not isfinite(current_price) or current_price <= 0
        or not isfinite(intrinsic_value) or intrinsic_value < 0):
        return []

    # Check for major upside/downside divergence (e.g. > 30% difference)
    divergence_pct = (intrinsic_value - current_price) / current_price if current_price > 0 else 0

    if abs(divergence_pct) > 0.30:
        # Check if an alert already exists for this to avoid spamming
        existing_alert = db.scalar(
            select(Alert)
            .where(Alert.company_id == company_id)
            .where(Alert.user_id == user_id)
            .where(Alert.alert_type == "valuation_divergence")
            .where(Alert.review_status != "resolved")
            .limit(1)
        )

        if not existing_alert:
            direction = "above" if divergence_pct > 0 else "below"
            alert = Alert(
                user_id=user_id,
                company_id=company_id,
                alert_type="valuation_divergence",
                severity="medium",
                title=f"Saved estimate {abs(divergence_pct)*100:.1f}% {direction} observed price",
                summary=f"Observed price: {currency} {current_price:.2f}; saved valuation estimate: {currency} {intrinsic_value:.2f}.",
                why_it_matters="Calculation from saved User Assumptions. Review the inputs and source age; this is not a forecast or recommendation.",
                what_changed="The current price-to-saved-estimate gap exceeds the 30% review threshold.",
                score_explanation_json={"claim_type":"Calculation", "basis":"User Assumption",
                    "market_price_id":latest_price_record.id, "dcf_output_id":latest_output.id,
                    "assumption_set_id":latest_assumption_set.id, "price_as_of":latest_price_record.as_of_date.isoformat(),
                    "formula":"(saved intrinsic value per share - market price) / market price"},
                confidence_bucket="medium",
                review_status="unreviewed"
            )
            db.add(alert)
            db.flush()

            # Associate with portfolios
            holdings = db.scalars(
                select(PortfolioHolding).join(Portfolio, Portfolio.id == PortfolioHolding.portfolio_id)
                .where(PortfolioHolding.company_id == company_id, Portfolio.user_id == user_id)
            ).all()

            for holding in holdings:
                impact = AlertPortfolioImpact(
                    alert_id=alert.id,
                    portfolio_id=holding.portfolio_id,
                    exposure_amount=float(holding.quantity * holding.average_cost),
                    impact_score=5.0
                )
                db.add(impact)

            alerts_created.append(alert)

    if commit:
        db.commit()
    return alerts_created
