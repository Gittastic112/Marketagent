"""Read-only, explicit scoped evidence report. Never fetches or approves inputs."""
import argparse
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.services.financial_coverage_inventory import build_financial_coverage_inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", type=Path, required=True)
    parser.add_argument("--checklist", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with SessionLocal() as db:
        report = build_financial_coverage_inventory(db, json.loads(args.scope.read_text()), json.loads(args.checklist.read_text()))
        db.rollback()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(f"Recorded {len(report['companies'])} security inventories; no financial review state changed.")


if __name__ == "__main__":
    main()
