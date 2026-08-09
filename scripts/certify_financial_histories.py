#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.services.financial_history_certification import (
    build_certification_report,
    resolve_certification_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Assess real-source US and India financial histories without persisting a certification badge."
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    with SessionLocal() as db:
        report = build_certification_report(db, resolve_certification_manifest(db, manifest))
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
