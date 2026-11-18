"""FinanceDatabase reference snapshot adapter, never a reviewed peer-set writer."""

import csv
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path

from app.schemas.research_lab import PeerDiscoveryRequest
from app.services.research_lab.errors import ResearchAdapterError


MAX_SNAPSHOT_BYTES = 48 * 1024 * 1024
MAX_ROWS = 300_000
FIELDS = (
    "symbol",
    "name",
    "currency",
    "sector",
    "industry",
    "exchange",
    "mic",
    "country",
    "isin",
    "figi",
    "delisted",
)


def load_snapshot(path: str | None) -> tuple[list[dict], dict]:
    if not path:
        raise ResearchAdapterError(
            "PEER_SNAPSHOT_NOT_CONFIGURED",
            "Configure a pinned FinanceDatabase snapshot using the documented CLI.",
            503,
        )
    snapshot = Path(path)
    manifest_path = Path(str(snapshot) + ".manifest.json")
    try:
        if (
            snapshot.stat().st_size > MAX_SNAPSHOT_BYTES
            or manifest_path.stat().st_size > 64_000
        ):
            raise ResearchAdapterError(
                "PEER_SNAPSHOT_TOO_LARGE",
                "The configured peer snapshot exceeds its size limit.",
                503,
            )
        with snapshot.open("rb") as stream:
            raw = stream.read(MAX_SNAPSHOT_BYTES + 1)
        if len(raw) > MAX_SNAPSHOT_BYTES:
            raise ResearchAdapterError(
                "PEER_SNAPSHOT_TOO_LARGE",
                "The configured peer snapshot exceeds its size limit.",
                503,
            )
        manifest = json.loads(manifest_path.read_text())
        if manifest.get("sha256") != hashlib.sha256(raw).hexdigest():
            raise ResearchAdapterError(
                "PEER_SNAPSHOT_HASH_MISMATCH",
                "The peer snapshot does not match its manifest.",
                409,
            )
        if manifest.get("source") != "JerBouma/FinanceDatabase" or not isinstance(
            manifest.get("revision"), str
        ):
            raise ValueError("invalid source")
        observed = datetime.fromisoformat(manifest["observed_at"])
        if observed.tzinfo is None:
            raise ValueError("unqualified timestamp")
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        if not {
            "symbol",
            "name",
            "currency",
            "exchange",
            "country",
            "sector",
            "industry",
        } <= set(reader.fieldnames or ()):
            raise ValueError("missing columns")
        records = []
        for index, row in enumerate(reader):
            if index >= MAX_ROWS:
                raise ResearchAdapterError(
                    "PEER_SNAPSHOT_TOO_LARGE",
                    "The peer snapshot has too many records.",
                    503,
                )
            records.append({key: (row.get(key) or "").strip()[:500] for key in FIELDS})
        return records, manifest
    except ResearchAdapterError:
        raise
    except (OSError, ValueError, TypeError, KeyError, csv.Error) as exc:
        raise ResearchAdapterError(
            "PEER_SNAPSHOT_INVALID",
            "The configured peer snapshot or its manifest is unavailable or invalid.",
            503,
        ) from exc


def discover(request: PeerDiscoveryRequest, path: str | None) -> dict:
    records, manifest = load_snapshot(path)
    matches, seen = [], set()
    for row in records:
        if row["delisted"].casefold() in {"true", "yes", "1"}:
            continue
        if any(
            value and row[key].casefold() != value.casefold()
            for key, value in (
                ("country", request.country),
                ("sector", request.sector),
                ("industry", request.industry),
            )
        ):
            continue
        if (
            request.query
            and request.query.casefold()
            not in (row["symbol"] + " " + row["name"]).casefold()
        ):
            continue
        identity = (row["symbol"], row["exchange"], row["currency"])
        if not row["symbol"] or identity in seen:
            continue
        seen.add(identity)
        matches.append(row)
    matches.sort(key=lambda row: (row["symbol"], row["exchange"], row["currency"]))
    return {
        "adapter": "FinanceDatabase_snapshot",
        "adapter_version": "1",
        "candidates": matches[: request.limit],
        "total_matches": len(matches),
        "truncated": len(matches) > request.limit,
        "snapshot": manifest,
        "warnings": [
            "Candidates are reference metadata, not a verified or economically comparable peer set.",
            "Listing identity, business similarity, and financial comparability require review before use.",
            "This present-day snapshot does not establish historical universe membership or publication dates.",
        ],
    }
