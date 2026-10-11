"""Print the non-mutating real-input readiness audit for one owned portfolio."""

from __future__ import annotations

import argparse
import json

from app.db.session import SessionLocal
from app.services.portfolio_real_input_readiness import audit_portfolio_real_input_readiness


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect persisted portfolio inputs without seeding, capturing, refreshing, "
            "or changing any application record."
        )
    )
    parser.add_argument("--portfolio-id", type=int, required=True)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--min-observations", type=int, default=20)
    parser.add_argument("--lookback-days", type=int, default=365)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    with SessionLocal() as db:
        try:
            report = audit_portfolio_real_input_readiness(
                db,
                args.portfolio_id,
                user_id=args.user_id,
                min_observations=args.min_observations,
                lookback_days=args.lookback_days,
            )
        except ValueError as exc:
            print(json.dumps({"status": "error", "message": str(exc)}, indent=2))
            return 2
    print(json.dumps(report, default=str, indent=2, sort_keys=True))
    return 0 if report["certification_status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
