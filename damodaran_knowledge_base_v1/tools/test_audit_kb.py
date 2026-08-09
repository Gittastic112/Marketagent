from __future__ import annotations

import csv
import hashlib
import tempfile
import unittest
from pathlib import Path

from audit_kb import audit, write_hash_ledger


class AuditKnowledgeBaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "raw" / "datasets").mkdir(parents=True)
        (self.root / "raw" / "inbox").mkdir(parents=True)
        (self.root / "data").mkdir()
        (self.root / "knowledge").mkdir()
        (self.root / "raw" / "datasets" / "sample.xls").write_bytes(b"source")
        (self.root / "raw" / "inbox" / "README.md").write_text("# Inbox\n", encoding="utf-8")
        (self.root / "knowledge" / "rules.jsonl").write_text('{"id":"RULE-1"}\n', encoding="utf-8")
        write_hash_ledger(self.root)
        self._write_csv(
            "source_catalog.csv",
            [
                "filename",
                "canonical_path",
                "source_type",
                "purpose",
                "as_of",
                "date_confidence",
                "usage",
                "status",
                "notes",
            ],
            [["sample.xls", "raw/datasets/sample.xls", "dataset", "Fixture", "2026-01-01", "high", "Test", "active", ""]],
        )
        digest = hashlib.sha256(b"source").hexdigest()
        self._write_csv(
            "processing_ledger.csv",
            [
                "ingested_at",
                "source_path",
                "sha256",
                "size_bytes",
                "canonical_path",
                "processing_status",
                "duplicate_of",
                "review_item",
            ],
            [["2026-01-02", "fixture/sample.xls", digest, "6", "raw/datasets/sample.xls", "processed", "", ""]],
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_csv(self, name: str, headers: list[str], rows: list[list[str]]) -> None:
        with (self.root / "data" / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            writer.writerows(rows)

    def test_clean_knowledge_base_passes(self) -> None:
        report = audit(self.root)
        self.assertEqual(report.exit_code, 0)
        self.assertEqual(report.errors, [])

    def test_hash_mismatch_fails(self) -> None:
        (self.root / "raw" / "datasets" / "sample.xls").write_bytes(b"changed")
        report = audit(self.root)
        self.assertEqual(report.exit_code, 1)
        self.assertTrue(any("SHA-256 mismatch" in error for error in report.errors))

    def test_pending_inbox_has_distinct_exit_code(self) -> None:
        (self.root / "raw" / "inbox" / "new.xls").write_bytes(b"pending")
        report = audit(self.root)
        self.assertEqual(report.exit_code, 2)
        self.assertEqual(report.inbox_pending, ["raw/inbox/new.xls"])

    def test_invalid_catalog_status_fails(self) -> None:
        catalog = self.root / "data" / "source_catalog.csv"
        catalog.write_text(catalog.read_text(encoding="utf-8").replace("active", "invented", 1), encoding="utf-8")
        report = audit(self.root)
        self.assertEqual(report.exit_code, 1)
        self.assertTrue(any("invalid status" in error for error in report.errors))


if __name__ == "__main__":
    unittest.main()
