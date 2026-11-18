import io
import json
from pathlib import Path
import stat
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app.services.research_lab import snapshot_cli


class SnapshotInstallTests(unittest.TestCase):
    def test_public_snapshot_and_manifest_are_readable_by_the_backend_uid(self):
        # Mock Data. Containers read this host-owned public reference through a read-only mount.
        raw = b"symbol,name,currency,exchange,country,sector,industry\nA,Example,USD,NMS,US,IT,Software\n"
        with TemporaryDirectory() as tmp, patch.object(snapshot_cli, "build_opener") as opener:
            opener.return_value.open.return_value = io.BytesIO(raw)
            path = Path(tmp) / "reference.csv"
            result = snapshot_cli.refresh(path, "1" * 40, ["NMS"])
            manifest = path.with_suffix(".csv.manifest.json")
            self.assertEqual(result["row_count"], 1)
            self.assertEqual(json.loads(manifest.read_bytes()), result)
            for asset in (path, manifest):
                with self.subTest(asset=asset.name):
                    self.assertEqual(stat.S_IMODE(asset.stat().st_mode), 0o644)
