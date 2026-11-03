import os
import sys

__test__ = False

# Ensure backend/app is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Company, DcfAssumptionSet, User, ValuationModel
from app.services.assumption_diff_service import AssumptionDiffService


def run_ledger_smoke() -> None:
    """Run the assumption-ledger smoke check against an isolated database."""
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        user = User(id="ledger-smoke", email="ledger-smoke@example.test", name="Ledger Smoke")
        db.add(user)

        # Create a dummy company
        company = Company(name="Test Corp", ticker="TST", market="US")
        db.add(company)
        db.commit()
        db.refresh(company)

        # Create a valuation model
        model = ValuationModel(
            user_id=user.id,
            company_id=company.id,
            name="Base Model",
            model_type="FCFF DCF",
        )
        db.add(model)
        db.commit()
        db.refresh(model)

        print(f"Created model {model.id} for company {company.id}")

        # Add first assumption set
        as1 = DcfAssumptionSet(
            valuation_model_id=model.id,
            scenario="Base",
            starting_revenue=100.0,
            current_operating_margin=0.1,
            wacc_start=0.1,
        )
        db.add(as1)
        db.commit()
        db.refresh(as1)

        print(f"Added AssumptionSet 1 (id={as1.id}): Rev=100, Margin=0.1")

        # Now simulate a second assumption set coming in
        as2 = DcfAssumptionSet(
            valuation_model_id=model.id,
            scenario="Base",
            starting_revenue=120.0,
            current_operating_margin=0.15,
            wacc_start=0.1,
        )
        db.add(as2)
        db.commit()
        db.refresh(as2)
        print(f"Added AssumptionSet 2 (id={as2.id}): Rev=120, Margin=0.15")

        # Run diff service
        logs = AssumptionDiffService.generate_change_logs(db, as2)

        print(f"Found {len(logs)} change logs.")
        for log in logs:
            print(f"- {log.parameter_name}: {log.old_value} -> {log.new_value}")

        if len(logs) != 2:
            raise RuntimeError(f"Expected 2 assumption changes, found {len(logs)}")

        print("SUCCESS! Assumption History Ledger works correctly.")


if __name__ == "__main__":
    run_ledger_smoke()
