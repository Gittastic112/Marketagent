"""Backup metadata validation must fail before any database replacement."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import recovery_metadata as recovery


def inventory(content="original"):
    return [
        {"kind": "database", "postgres_major": 16, "revisions": ["test_revision"]},
        {"kind": "table", "name": "alembic_version", "rows": 1, "sha256": sha256(b"revision").hexdigest()},
        {"kind": "table", "name": "document_assets", "rows": 1, "sha256": sha256(content.encode()).hexdigest()},
        {"kind": "table", "name": "brief_sources", "rows": 1, "sha256": sha256(b"private").hexdigest()},
        {"kind": "asset_store", "name": "document_assets", "present": True, "count": 1, "content_bytes": 4},
        {"kind": "asset_store", "name": "brief_sources", "present": True, "count": 1, "content_bytes": 7},
        {"kind": "asset", "store": "document_assets", "id": "1", "size_bytes": 4, "sha256": sha256(b"%PDF").hexdigest()},
        {"kind": "asset", "store": "brief_sources", "id": "2", "size_bytes": 7, "sha256": sha256(b"private").hexdigest()},
    ]


class RecoveryMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def backup(self):
        (self.root / "database.dump").write_bytes(b"Mock Data custom dump")
        (self.root / "inventory.raw.jsonl").write_text("\n".join(json.dumps(row) for row in inventory()))
        recovery.create(self.root, "20261011T000000Z")
        recovery.finalize(self.root)
        return self.root

    def test_v3_binds_dump_all_tables_and_both_asset_stores(self):
        root = self.backup()
        result = recovery.validate(root)
        self.assertEqual(result["format_version"], 3)
        self.assertEqual(result["verification_basis"], "restored_dump")
        self.assertEqual(result["asset_stores"]["brief_sources"]["content_bytes"], 7)
        self.assertEqual(result["table_count"], 3)

    def test_missing_or_interrupted_completion_is_not_a_backup(self):
        root = self.backup()
        (root / "COMPLETE").unlink()
        with self.assertRaisesRegex(ValueError, "completion"):
            recovery.validate(root)
        with patch.object(recovery.os, "replace", side_effect=PermissionError("Mock denial")):
            with self.assertRaises(PermissionError):
                recovery.finalize(root)
        self.assertFalse((root / "COMPLETE").exists())
        with self.assertRaisesRegex(ValueError, "completion"):
            recovery.validate(root)
        recovery.finalize(root)
        self.assertEqual(recovery.validate(root)["format_version"], 3)

    def test_completion_is_bound_to_exact_manifest_and_cannot_be_linked(self):
        root = self.backup()
        marker = root / "COMPLETE"
        marker.write_text(json.dumps({"format_version": 3, "manifest_sha256": "0" * 64}))
        with self.assertRaisesRegex(ValueError, "completion"):
            recovery.validate(root)
        marker.unlink()
        marker.symlink_to(root / "unread-target")
        with self.assertRaisesRegex(ValueError, "completion"):
            recovery.validate(root)

    def test_completed_format_two_remains_readable_without_a_marker(self):
        root = self.backup()
        manifest = json.loads((root / "manifest.json").read_text())
        manifest["format_version"] = 2
        (root / "manifest.json").write_text(json.dumps(manifest))
        (root / "COMPLETE").unlink()
        recovery.write_checksums(root, recovery.V2_FILES)
        self.assertEqual(recovery.validate(root)["format_version"], 2)

    def test_equal_counts_different_content_fails(self):
        root = self.backup()
        with self.assertRaisesRegex(ValueError, "content inventory"):
            recovery.compare(inventory("corrupted"), json.loads((root / "content_inventory.json").read_text()))

    def test_rejects_missing_private_asset_with_equal_table_count(self):
        rows = [row for row in inventory() if not (row["kind"] == "asset" and row["store"] == "brief_sources")]
        with self.assertRaisesRegex(ValueError, "asset inventory"):
            recovery.normalize(rows)

    def test_rejects_duplicate_tables_and_assets(self):
        for row in (inventory()[1], inventory()[-1]):
            with self.subTest(kind=row["kind"]), self.assertRaises(ValueError):
                recovery.normalize([*inventory(), row])

    def test_rejects_corruption_and_missing_checksum_coverage(self):
        root = self.backup()
        checksums = root / "checksums.sha256"
        checksums.write_text("\n".join(checksums.read_text().splitlines()[:-1]) + "\n")
        with self.assertRaisesRegex(ValueError, "checksum"):
            recovery.validate(root)
        self.backup()
        (root / "database.dump").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "checksum"):
            recovery.validate(root)

    def test_rejects_symlinks_and_path_traversal_before_opening_target(self):
        root = self.backup()
        dump = root / "database.dump"
        dump.unlink()
        dump.symlink_to(root / "outside-unread")
        with self.assertRaisesRegex(ValueError, "regular file"):
            recovery.validate(root)
        dump.unlink()
        self.backup()
        (root / "checksums.sha256").write_text(f'{"0" * 64}  ../outside-unread\n')
        with self.assertRaisesRegex(ValueError, "checksum"):
            recovery.validate(root)

    def test_manifest_unknown_version_and_changed_bounding_fields_fail(self):
        root = self.backup()
        for changes in ({"format_version": 99}, {"database_dump": {"path": "../outside"}}, {"table_count": 2}):
            manifest = json.loads((root / "manifest.json").read_text())
            manifest.update(changes)
            (root / "manifest.json").write_text(json.dumps(manifest))
            recovery.write_checksums(root, recovery.V2_FILES)
            with self.assertRaises(ValueError):
                recovery.validate(root)
            self.backup()

    def test_legacy_requires_explicit_count_only_opt_in(self):
        root = self.root
        (root / "database.dump").write_bytes(b"Mock Data legacy dump")
        (root / "record_counts.tsv").write_text("alpha\t1\n")
        (root / "manifest.json").write_text(json.dumps({"format_version": 1}))
        recovery.write_checksums(root, recovery.V1_FILES)
        with self.assertRaisesRegex(ValueError, "legacy"):
            recovery.validate(root)
        self.assertEqual(recovery.validate(root, allow_legacy=True)["format_version"], 1)

    def test_pruning_preserves_partial_unowned_and_invalid_backups(self):
        for name in ("20261001T000000Z-1-market-intelligence", "20261002T000000Z-2-market-intelligence"):
            folder = self.root / name
            folder.mkdir()
            (folder / "database.dump").write_bytes(b"Mock Data")
            (folder / "inventory.raw.jsonl").write_text("\n".join(json.dumps(row) for row in inventory()))
            recovery.create(folder, "20261011T000000Z")
            recovery.finalize(folder)
        incomplete = self.root / "20261003T000000Z-3-market-intelligence"
        incomplete.mkdir()
        (incomplete / "database.dump").write_bytes(b"Mock Data")
        (incomplete / "inventory.raw.jsonl").write_text("\n".join(json.dumps(row) for row in inventory()))
        recovery.create(incomplete, "20261011T000000Z")
        for name in ("personal-market-intelligence", "20260901T000000Z-1-market-intelligence.partial", "20260902T000000Z-1-market-intelligence"):
            (self.root / name).mkdir()
        self.assertEqual(recovery.prune(self.root, 1), 1)
        self.assertEqual(len(list(self.root.iterdir())), 5)
        self.assertTrue(incomplete.exists())
        with self.assertRaises(ValueError):
            recovery.prune(self.root, 0)


if __name__ == "__main__":
    unittest.main()
