from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertPortfolioImpact
from app.models.dcf import DcfAssumptionSet, ValuationAssumptionChangeLog
from app.models.event import Event
from app.models.portfolio import PortfolioHolding


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

    change_log = None
    if change_log_id:
        change_log = db.scalar(select(ValuationAssumptionChangeLog).where(ValuationAssumptionChangeLog.id == change_log_id))

    company_id = event.company_id

    # Create the base Alert
    title = f"Valuation Stale: {event.title}"
    summary = assumption_set.stale_reason or "An event has triggered a review of current valuation assumptions."

    if change_log:
        title = f"Assumption Broken: {change_log.parameter_name}"
        summary = change_log.rationale

    alert = Alert(
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

    # Link to Portfolio impacts if this company is held in any portfolios
    holdings = db.scalars(
        select(PortfolioHolding).where(PortfolioHolding.company_id == company_id)
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

def check_price_valuation_divergence(db: Session, company_id: int | None) -> list[Alert]:
    """
    Checks if there's a material divergence between the current market price and
    the intrinsic value, or if the market price has moved significantly but the
    intrinsic value has remained unchanged. Generates alerts accordingly.
    """
    if company_id is None:
        return []

    from app.models.market_price import MarketPrice
    from app.models.dcf import ValuationModel, DcfAssumptionSet, DcfOutput

    # Get the latest price
    latest_price_record = db.scalar(
        select(MarketPrice)
        .where(MarketPrice.company_id == company_id)
        .order_by(MarketPrice.as_of_date.desc(), MarketPrice.id.desc())
        .limit(1)
    )
    if not latest_price_record:
        return []

    # Get the active assumption set
    latest_assumption_set = db.scalar(
        select(DcfAssumptionSet)
        .join(ValuationModel, ValuationModel.id == DcfAssumptionSet.valuation_model_id)
        .where(ValuationModel.company_id == company_id)
        .where(DcfAssumptionSet.scenario == "Base")
        .order_by(DcfAssumptionSet.id.desc())
        .limit(1)
    )
    if not latest_assumption_set:
        return []

    # Get the corresponding output
    latest_output = db.scalar(
        select(DcfOutput)
        .where(DcfOutput.assumption_set_id == latest_assumption_set.id)
    )
    if not latest_output or not latest_output.intrinsic_value_per_share:
        return []

    alerts_created = []
    current_price = float(latest_price_record.price)
    intrinsic_value = latest_output.intrinsic_value_per_share

    # Check for major upside/downside divergence (e.g. > 30% difference)
    divergence_pct = (intrinsic_value - current_price) / current_price if current_price > 0 else 0

    if abs(divergence_pct) > 0.30:
        # Check if an alert already exists for this to avoid spamming
        existing_alert = db.scalar(
            select(Alert)
            .where(Alert.company_id == company_id)
            .where(Alert.alert_type == "valuation_divergence")
            .where(Alert.review_status != "resolved")
            .limit(1)
        )

        if not existing_alert:
            direction = "Upside" if divergence_pct > 0 else "Downside"
            alert = Alert(
                company_id=company_id,
                alert_type="valuation_divergence",
                severity="medium",
                title=f"Material Valuation {direction}: {abs(divergence_pct)*100:.1f}%",
                summary=f"Market price is ${current_price:.2f} but intrinsic value is ${intrinsic_value:.2f}.",
                why_it_matters="Significant gap between price and value implies either a market opportunity or broken assumptions.",
                what_changed="Price moved or assumptions changed significantly.",
                confidence_bucket="medium",
                review_status="unreviewed"
            )
            db.add(alert)
            db.flush()

            # Associate with portfolios
            holdings = db.scalars(
                select(PortfolioHolding).where(PortfolioHolding.company_id == company_id)
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

    db.commit()
    return alerts_created
