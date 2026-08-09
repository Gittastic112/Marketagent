import asyncio
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.assumption_methodology import AssumptionMethodValue

# Hardcoded seed data for India ERP as a pilot
# When actual macro.xlsx or ctryprem.xlsx files are imported, they will populate this dynamically.
SEED_DATA = [
    {
        "assumption_key": "equity_risk_premium",
        "method_key": "damodaran_implied_erp",
        "country": "India",
        "value": 0.069,
        "low_value": 0.065,
        "base_value": 0.069,
        "high_value": 0.075,
        "unit": "percent",
        "source_type": "benchmark",
        "source_name": "Damodaran Dataset (Seed)",
        "confidence": "high",
        "is_default_candidate": True,
        "notes": "Implied ERP from Damodaran for India",
    },
    {
        "assumption_key": "equity_risk_premium",
        "method_key": "mature_market_plus_crp",
        "country": "India",
        "value": 0.072,
        "low_value": 0.070,
        "base_value": 0.072,
        "high_value": 0.078,
        "unit": "percent",
        "source_type": "benchmark",
        "source_name": "Damodaran Dataset (Seed)",
        "confidence": "high",
        "is_default_candidate": False,
        "notes": "Mature Market Premium + Country Risk Premium for India",
    },
    {
        "assumption_key": "equity_risk_premium",
        "method_key": "sovereign_spread",
        "country": "India",
        "value": 0.075,
        "low_value": 0.072,
        "base_value": 0.075,
        "high_value": 0.080,
        "unit": "percent",
        "source_type": "benchmark",
        "source_name": "Sovereign Default Spread (Seed)",
        "confidence": "medium",
        "is_default_candidate": False,
        "notes": "Sovereign Default Spread method",
    },
    {
        "assumption_key": "risk_free_rate",
        "method_key": "current_government_bond",
        "country": "India",
        "value": 0.071,
        "unit": "percent",
        "source_type": "benchmark",
        "source_name": "Macro Dataset (Seed)",
        "confidence": "high",
        "is_default_candidate": True,
        "notes": "India 10Y Government Bond Yield",
    }
]

def seed_assumptions(db: Session):
    for item in SEED_DATA:
        existing = db.query(AssumptionMethodValue).filter_by(
            assumption_key=item["assumption_key"],
            method_key=item["method_key"],
            country=item["country"]
        ).first()

        if not existing:
            print(f"Seeding {item['assumption_key']} for {item['country']} via {item['method_key']}")
            val = AssumptionMethodValue(**item)
            db.add(val)
        else:
            print(f"Already seeded: {item['assumption_key']} via {item['method_key']} for {item['country']}")

    db.commit()

def main():
    db = SessionLocal()
    try:
        seed_assumptions(db)
        print("Seed completed successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
