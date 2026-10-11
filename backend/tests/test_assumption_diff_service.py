from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.dcf import DcfAssumptionSet, ValuationModel
from app.services.assumption_diff_service import AssumptionDiffService


def test_generate_change_logs_records_only_changed_assumptions(db_session: Session) -> None:
    company = Company(name="Ledger Test Corp", ticker="LEDGER", market="US")
    db_session.add(company)
    db_session.flush()

    model = ValuationModel(
        user_id="admin_user_id_fallback",
        company_id=company.id,
        name="Ledger test model",
        model_type="fcff_dcf",
    )
    db_session.add(model)
    db_session.flush()

    previous = DcfAssumptionSet(
        valuation_model_id=model.id,
        scenario="Base",
        starting_revenue=100.0,
        current_operating_margin=0.10,
        wacc_start=0.10,
        capex=20.0,
        cash_flow_currency="USD",
    )
    db_session.add(previous)
    db_session.commit()

    current = DcfAssumptionSet(
        valuation_model_id=model.id,
        scenario="Base",
        starting_revenue=120.0,
        current_operating_margin=0.15,
        wacc_start=0.10,
        capex=25.0,
        cash_flow_currency="INR",
    )
    db_session.add(current)
    db_session.commit()
    db_session.refresh(current)

    logs = AssumptionDiffService.generate_change_logs(db_session, current)

    changes = {log.parameter_name: (log.old_value, log.new_value) for log in logs}
    assert changes == {
        "starting_revenue": ("100.0", "120.0"),
        "current_operating_margin": ("0.1", "0.15"),
        "cash_flow_currency": ("USD", "INR"),
        "capex": ("20.0", "25.0"),
    }
    assert all(log.assumption_set_id == current.id for log in logs)
    assert all(log.valuation_model_id == model.id for log in logs)
