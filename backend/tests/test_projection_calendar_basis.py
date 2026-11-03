"""Relative projection periods must not acquire fabricated calendar dates."""
import pytest
from sqlalchemy import select

from app.models.dcf import DcfAssumptionSet, DcfProjectionYear
from app.schemas.valuation_outputs import DcfProjectionYearRead
from app.services.dcf import calculate_dcf
from test_saved_relative_inputs import seed


@pytest.mark.parametrize("model_type", ["fcff_dcf", "financial_services", "distressed"])
def test_new_forecasts_have_relative_periods_without_calendar_anchor(model_type):
    row = DcfAssumptionSet(id=1, valuation_model_id=1,
        starting_revenue=100, current_operating_margin=.1,
        target_operating_margin=.1, tax_rate=0, sales_to_capital_ratio=2,
        starting_invested_capital=50, revenue_growth_years_json={"1": 0, "2": 0},
        projection_years_count=2, wacc_start=.1, wacc_terminal=.1,
        terminal_growth_rate=0, terminal_roic=.1, cost_of_equity=.1,
        cash=0, debt=0, operating_leases=0, cross_holdings=0,
        minority_interests=0, preferred_stock=0,
        employee_options_value=0, diluted_shares=10,
        book_value_of_equity=100, net_income=10, target_roe=.1,
        probability_of_failure=0, distress_sale_proceeds=0,
        cash_flow_currency="USD", discount_rate_currency="USD")
    output, projections, _ = calculate_dcf(row, model_type)
    assert [p.year_index for p in projections] == [1, 2]
    assert all(p.calendar_year is None for p in projections)
    assert output.equity_value == pytest.approx(100)
    assert output.intrinsic_value_per_share == pytest.approx(10)


def test_unknown_year_persists_and_legacy_year_is_withheld_without_rewrite(client, db_session):
    _, model, assumption = seed(db_session)
    legacy = DcfProjectionYear(assumption_set_id=assumption.id,
        year_index=1, calendar_year=2025, revenue=100)
    unknown = DcfProjectionYear(assumption_set_id=assumption.id,
        year_index=2, calendar_year=None, revenue=110)
    db_session.add_all([legacy, unknown])
    db_session.commit()
    identities = (legacy.id, unknown.id)
    body = client.get(f"/valuation-models/{model.id}/assumptions/{assumption.id}/forecast")
    assert body.status_code == 200
    rows = {row["year_index"]: row for row in body.json()["data"]}
    assert rows[1]["calendar_year"] is None and rows[2]["calendar_year"] is None
    assert rows[1]["revenue"] == 100 and rows[2]["revenue"] == 110
    db_session.expire_all()
    stored = db_session.scalars(select(DcfProjectionYear).where(
        DcfProjectionYear.id.in_(identities)).order_by(DcfProjectionYear.id)).all()
    assert [row.calendar_year for row in stored] == [2025, None]
    assert DcfProjectionYearRead.model_validate(stored[0]).model_dump()["calendar_year"] is None
    assert stored[0].calendar_year == 2025
