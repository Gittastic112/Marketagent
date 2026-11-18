"""Explicit bounded FinanceDatabase download. Run outside the HTTP request path."""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile
import time
from urllib.request import HTTPRedirectHandler, Request, build_opener

from app.services.research_lab.peers import MAX_SNAPSHOT_BYTES


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def refresh(destination: Path, revision: str, exchanges: list[str]) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("revision must be the exact upstream commit SHA")
    if not 1 <= len(exchanges) <= 12 or any(
        not re.fullmatch(r"[A-Z]{2,5}", exchange) for exchange in exchanges
    ):
        raise ValueError("Choose 1 to 12 exact upstream exchange file codes.")
    buffer = io.StringIO(newline="")
    writer, columns, total, rows = None, None, 0, 0
    sources = []
    deadline = time.monotonic() + 90
    opener = build_opener(_NoRedirect())
    for exchange in sorted(set(exchanges)):
        url = f"https://raw.githubusercontent.com/JerBouma/FinanceDatabase/{revision}/database/equities/{exchange}.csv"
        raw = bytearray()
        request = Request(
            url,
            headers={
                "Accept": "text/csv",
                "User-Agent": "Marketagent reference snapshot/1",
            },
        )
        with opener.open(request, timeout=15) as response:
            while chunk := response.read(64 * 1024):
                total += len(chunk)
                if total > MAX_SNAPSHOT_BYTES or time.monotonic() > deadline:
                    raise ValueError("Snapshot download exceeded its byte/time budget.")
                raw.extend(chunk)
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        if writer is None:
            columns = reader.fieldnames
            if not columns or "symbol" not in columns:
                raise ValueError("Missing upstream symbol column.")
            writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
        if reader.fieldnames != columns:
            raise ValueError("Upstream schemas differ; refusing to combine snapshots.")
        for row in reader:
            writer.writerow(row)
            rows += 1
            if rows > 300_000:
                raise ValueError("Too many reference rows.")
        sources.append(
            {
                "exchange": exchange,
                "url": url,
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    payload = buffer.getvalue().encode()
    if len(payload) > MAX_SNAPSHOT_BYTES:
        raise ValueError("Combined snapshot is too large.")
    manifest = {
        "schema_version": "financedatabase-snapshot/v1",
        "source": "JerBouma/FinanceDatabase",
        "revision": revision,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "row_count": rows,
        "sources": sources,
        "license": "MIT",
        "license_url": f"https://github.com/JerBouma/FinanceDatabase/blob/{revision}/LICENSE",
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Publish manifest last. Readers fail closed during an interrupted refresh.
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
        stream.write(payload)
        temp_csv = Path(stream.name)
    temp_csv.replace(destination)
    target_manifest = Path(str(destination) + ".manifest.json")
    with tempfile.NamedTemporaryFile(
        mode="w", dir=destination.parent, delete=False
    ) as stream:
        json.dump(manifest, stream, sort_keys=True, indent=2)
        temp_manifest = Path(stream.name)
    temp_manifest.replace(target_manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--exchange", action="append", required=True)
    arguments = parser.parse_args()
    print(
        json.dumps(
            refresh(arguments.output, arguments.revision, arguments.exchange), indent=2
        )
    )
