#!/usr/bin/env python3
"""Audit the integrity and processing state of the Damodaran knowledge base."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


CANONICAL_RAW_DIRS = ("articles", "cases", "datasets", "models")
REQUIRED_CATALOG_COLUMNS = {
    "filename",
    "canonical_path",
    "source_type",
    "purpose",
    "as_of",
    "date_confidence",
    "usage",
    "status",
    "notes",
}
REQUIRED_PROCESSING_COLUMNS = {
    "ingested_at",
    "source_path",
    "sha256",
    "size_bytes",
    "canonical_path",
    "processing_status",
    "duplicate_of",
    "review_item",
}
ALLOWED_SOURCE_STATUSES = {"active", "case_only", "historical_only", "review_required", "superseded"}
ALLOWED_DATE_CONFIDENCE = {"high", "medium", "low"}


@dataclass
class AuditReport:
    canonical_files: int = 0
    catalog_rows: int = 0
    processing_rows: int = 0
    inbox_pending: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        if self.errors:
            return 1
        if self.inbox_pending:
            return 2
        return 0

    def as_dict(self) -> dict[str, object]:
        return {
            "status": "error" if self.errors else "pending" if self.inbox_pending else "ok",
            "canonical_files": self.canonical_files,
            "catalog_rows": self.catalog_rows,
            "processing_rows": self.processing_rows,
            "inbox_pending": self.inbox_pending,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_files(kb_root: Path) -> list[Path]:
    files: list[Path] = []
    raw_root = kb_root / "raw"
    for directory in CANONICAL_RAW_DIRS:
        target = raw_root / directory
        if target.exists():
            files.extend(path for path in target.rglob("*") if path.is_file() and path.name != "README.md")
    return sorted(files)


def read_csv(path: Path, report: AuditReport) -> tuple[list[dict[str, str]], set[str]]:
    if not path.exists():
        report.errors.append(f"Missing required CSV: {path.relative_to(path.parents[1])}")
        return [], set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader), set(reader.fieldnames or [])


def write_hash_ledger(kb_root: Path) -> None:
    output = kb_root / "data" / "raw_file_hashes.csv"
    rows = []
    for path in canonical_files(kb_root):
        rows.append(
            {
                "path": path.relative_to(kb_root).as_posix(),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("path", "sha256", "size_bytes"))
        writer.writeheader()
        writer.writerows(rows)


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def audit(kb_root: Path) -> AuditReport:
    kb_root = kb_root.resolve()
    report = AuditReport()

    files = canonical_files(kb_root)
    report.canonical_files = len(files)
    actual = {
        path.relative_to(kb_root).as_posix(): (sha256_file(path), path.stat().st_size)
        for path in files
    }

    hash_rows, hash_columns = read_csv(kb_root / "data" / "raw_file_hashes.csv", report)
    if hash_columns and hash_columns != {"path", "sha256", "size_bytes"}:
        report.errors.append("raw_file_hashes.csv must contain exactly path, sha256, size_bytes")
    ledger_paths = [row.get("path", "") for row in hash_rows]
    for duplicate in sorted(_duplicates(ledger_paths)):
        report.errors.append(f"Duplicate hash-ledger path: {duplicate}")
    ledger = {row.get("path", ""): row for row in hash_rows}

    for path, (actual_hash, actual_size) in actual.items():
        row = ledger.get(path)
        if row is None:
            report.errors.append(f"Canonical raw file missing from hash ledger: {path}")
            continue
        if row.get("sha256") != actual_hash:
            report.errors.append(f"SHA-256 mismatch: {path}")
        try:
            expected_size = int(row.get("size_bytes", ""))
        except ValueError:
            expected_size = -1
        if expected_size != actual_size:
            report.errors.append(f"Size mismatch: {path}")
    for path in sorted(set(ledger) - set(actual)):
        report.errors.append(f"Hash ledger references a missing canonical file: {path}")

    hashes: dict[str, list[str]] = {}
    for path, (digest, _) in actual.items():
        hashes.setdefault(digest, []).append(path)
    for paths in hashes.values():
        if len(paths) > 1:
            report.warnings.append(f"Canonical raw files share identical bytes: {', '.join(sorted(paths))}")

    catalog_rows, catalog_columns = read_csv(kb_root / "data" / "source_catalog.csv", report)
    report.catalog_rows = len(catalog_rows)
    missing_catalog_columns = REQUIRED_CATALOG_COLUMNS - catalog_columns
    if missing_catalog_columns:
        report.errors.append(
            "source_catalog.csv missing columns: " + ", ".join(sorted(missing_catalog_columns))
        )
    catalog_paths = [row.get("canonical_path", "") for row in catalog_rows]
    for duplicate in sorted(_duplicates(catalog_paths)):
        report.errors.append(f"Duplicate source-catalog canonical_path: {duplicate}")
    for path in sorted(set(actual) - set(catalog_paths)):
        report.errors.append(f"Canonical raw file missing from source catalog: {path}")
    for path in sorted(set(catalog_paths) - set(actual)):
        report.errors.append(f"Source catalog references a missing canonical file: {path}")
    for number, row in enumerate(catalog_rows, 2):
        for column in REQUIRED_CATALOG_COLUMNS - {"notes"}:
            if not row.get(column, "").strip():
                report.errors.append(f"Source catalog row {number} has empty {column}")
        canonical_path = row.get("canonical_path", "")
        if canonical_path and row.get("filename") != Path(canonical_path).name:
            report.errors.append(f"Source catalog row {number} filename does not match canonical_path")
        if row.get("date_confidence") not in ALLOWED_DATE_CONFIDENCE:
            report.errors.append(f"Source catalog row {number} has invalid date_confidence")
        if row.get("status") not in ALLOWED_SOURCE_STATUSES:
            report.errors.append(f"Source catalog row {number} has invalid status")

    processing_rows, processing_columns = read_csv(kb_root / "data" / "processing_ledger.csv", report)
    report.processing_rows = len(processing_rows)
    missing_processing_columns = REQUIRED_PROCESSING_COLUMNS - processing_columns
    if missing_processing_columns:
        report.errors.append(
            "processing_ledger.csv missing columns: " + ", ".join(sorted(missing_processing_columns))
        )
    for number, row in enumerate(processing_rows, 2):
        canonical_path = row.get("canonical_path", "") or row.get("duplicate_of", "")
        if canonical_path and canonical_path not in actual:
            report.errors.append(f"Processing ledger row {number} references missing raw file: {canonical_path}")
            continue
        if canonical_path:
            expected_hash = row.get("sha256", "")
            expected_size = row.get("size_bytes", "")
            actual_hash, actual_size = actual[canonical_path]
            if expected_hash != actual_hash:
                report.errors.append(f"Processing ledger row {number} hash does not match {canonical_path}")
            if expected_size != str(actual_size):
                report.errors.append(f"Processing ledger row {number} size does not match {canonical_path}")
        source_path = kb_root.parent / row.get("source_path", "")
        if source_path.is_file():
            if sha256_file(source_path) != row.get("sha256", ""):
                report.errors.append(f"Processing ledger row {number} intake hash changed: {row.get('source_path')}")
            if str(source_path.stat().st_size) != row.get("size_bytes", ""):
                report.errors.append(f"Processing ledger row {number} intake size changed: {row.get('source_path')}")
        if row.get("processing_status") == "duplicate_verified" and not row.get("duplicate_of"):
            report.errors.append(f"Processing ledger row {number} duplicate lacks duplicate_of")

    inbox = kb_root / "raw" / "inbox"
    if not inbox.exists():
        report.errors.append("Missing raw/inbox directory")
    else:
        report.inbox_pending = sorted(
            path.relative_to(kb_root).as_posix()
            for path in inbox.rglob("*")
            if path.is_file() and path.name != "README.md" and not path.name.startswith(".")
        )

    for jsonl_path in sorted((kb_root / "knowledge").glob("*.jsonl")):
        with jsonl_path.open(encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    json.loads(line)
                except json.JSONDecodeError as exc:
                    report.errors.append(
                        f"Invalid JSONL at {jsonl_path.relative_to(kb_root)}:{number}: {exc.msg}"
                    )

    return report


def print_report(report: AuditReport) -> None:
    print(f"status: {'error' if report.errors else 'pending' if report.inbox_pending else 'ok'}")
    print(f"canonical raw files: {report.canonical_files}")
    print(f"source catalog rows: {report.catalog_rows}")
    print(f"processing ledger rows: {report.processing_rows}")
    print(f"pending inbox files: {len(report.inbox_pending)}")
    for path in report.inbox_pending:
        print(f"  PENDING {path}")
    for warning in report.warnings:
        print(f"  WARNING {warning}")
    for error in report.errors:
        print(f"  ERROR {error}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kb-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Knowledge-base root (defaults to the parent of tools/).",
    )
    parser.add_argument("--json", action="store_true", help="Print a JSON report.")
    parser.add_argument(
        "--refresh-hashes",
        action="store_true",
        help="Rewrite data/raw_file_hashes.csv from immutable canonical raw files before auditing.",
    )
    args = parser.parse_args()
    if args.refresh_hashes:
        write_hash_ledger(args.kb_root.resolve())
    report = audit(args.kb_root)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print_report(report)
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
