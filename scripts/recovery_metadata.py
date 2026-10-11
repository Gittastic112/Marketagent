"""Versioned recovery evidence. Only reads the explicitly supplied backup folder."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import sys

ALGORITHM = "postgres16-jsonb-sorted-row-sha256-v1"
V1_FILES = ("database.dump", "record_counts.tsv", "manifest.json")
V2_FILES = (*V1_FILES, "content_inventory.json")
STORES = {"document_assets", "brief_sources"}
HEX = re.compile(r"[0-9a-f]{64}\Z")
TABLE = re.compile(r"[a-z_][a-z0-9_]*\Z")
OWNED_FOLDER = re.compile(r"\d{8}T\d{6}Z-\d+-market-intelligence\Z")


def regular(path: Path) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Backup requires a regular file: {path.name}")
    return path


def digest(path: Path) -> str:
    result = sha256()
    with regular(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def read_text(path: Path, limit: int = 4 * 1024 * 1024) -> str:
    regular(path)
    if path.stat().st_size > limit:
        raise ValueError(f"Backup metadata exceeds its size limit: {path.name}")
    return path.read_text(encoding="utf-8")


def integer(value: object) -> bool:
    return type(value) is int and value >= 0


def normalize(rows: list[dict]) -> list[dict]:
    if not isinstance(rows, list) or not rows or any(not isinstance(row, dict) for row in rows):
        raise ValueError("Invalid content inventory")
    tables, stores, assets, databases = {}, {}, {}, []
    for row in rows:
        kind = row.get("kind")
        if kind == "database":
            if (set(row) != {"kind", "postgres_major", "revisions"}
                or row["postgres_major"] != 16 or not isinstance(row["revisions"], list)
                or not row["revisions"] or any(not isinstance(v, str) or not re.fullmatch(r"[a-zA-Z0-9_]+", v) for v in row["revisions"])
                or len(set(row["revisions"])) != len(row["revisions"])):
                raise ValueError("Unsupported database version or missing migration revision")
            databases.append(row)
        elif kind == "table":
            name = row.get("name", "")
            if (set(row) != {"kind", "name", "rows", "sha256"} or not isinstance(name, str)
                or not TABLE.fullmatch(name) or name in tables or not integer(row["rows"])
                or not isinstance(row["sha256"], str) or not HEX.fullmatch(row["sha256"])):
                raise ValueError("Invalid or duplicate table inventory")
            tables[name] = row
        elif kind == "asset_store":
            name = row.get("name")
            if (set(row) != {"kind", "name", "present", "count", "content_bytes"}
                or name not in STORES or name in stores or type(row["present"]) is not bool
                or not integer(row["count"]) or not integer(row["content_bytes"])):
                raise ValueError("Invalid or duplicate asset inventory")
            stores[name] = row
        elif kind == "asset":
            key = (row.get("store"), row.get("id"))
            if (set(row) != {"kind", "store", "id", "size_bytes", "sha256"}
                or key[0] not in STORES or not isinstance(key[1], str) or not re.fullmatch(r"[0-9]+", key[1])
                or key in assets or not integer(row["size_bytes"])
                or not isinstance(row["sha256"], str) or not HEX.fullmatch(row["sha256"])):
                raise ValueError("Invalid or duplicate asset inventory")
            assets[key] = row
        else:
            raise ValueError("Unknown content inventory record")
    if len(databases) != 1 or not tables or "alembic_version" not in tables:
        raise ValueError("Incomplete database/table inventory")
    if set(stores) != STORES:
        raise ValueError("Incomplete asset inventory")
    for name, store in stores.items():
        items = [v for (source, _), v in assets.items() if source == name]
        if (store["count"] != len(items) or store["content_bytes"] != sum(v["size_bytes"] for v in items)
            or store["present"] != (name in tables)
            or (not store["present"] and (store["count"] or store["content_bytes"]))
            or (store["present"] and store["count"] > tables[name]["rows"])):
            raise ValueError("Incomplete or inconsistent asset inventory")
    return sorted(rows, key=lambda row: (row["kind"], row.get("name", row.get("store", "")), row.get("id", "")))


def raw_inventory(root: Path) -> list[dict]:
    return normalize([json.loads(line) for line in read_text(root / "inventory.raw.jsonl", 64 * 1024 * 1024).splitlines() if line])


def counts(rows: list[dict]) -> str:
    return "".join(f'{row["name"]}\t{row["rows"]}\n' for row in rows if row["kind"] == "table")


def write_checksums(root: Path, names: tuple[str, ...]) -> None:
    (root / "checksums.sha256").write_text("".join(f"{digest(root / name)}  {name}\n" for name in names))


def create(root: Path, timestamp: str) -> dict:
    if not re.fullmatch(r"\d{8}T\d{6}Z", timestamp):
        raise ValueError("Invalid backup timestamp")
    rows = raw_inventory(root)
    (root / "content_inventory.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
    (root / "record_counts.tsv").write_text(counts(rows))
    database = next(row for row in rows if row["kind"] == "database")
    manifest = {
        "application": "market-intelligence", "format_version": 2,
        "created_at_utc": timestamp, "database_format": "postgresql_custom",
        "verification_basis": "restored_dump", "fingerprint_algorithm": ALGORITHM,
        "postgres_major": database["postgres_major"], "alembic_revisions": database["revisions"],
        "table_count": sum(row["kind"] == "table" for row in rows),
        "database_dump": {"path": "database.dump", "sha256": digest(root / "database.dump"), "size_bytes": (root / "database.dump").stat().st_size},
        "record_counts": {"path": "record_counts.tsv", "sha256": digest(root / "record_counts.tsv")},
        "content_inventory": {"path": "content_inventory.json", "sha256": digest(root / "content_inventory.json")},
        "asset_stores": {row["name"]: {key: row[key] for key in ("present", "count", "content_bytes")} for row in rows if row["kind"] == "asset_store"},
        "limitations": ["Environment files and encryption keys are excluded.", "This local backup is not an encrypted off-device recovery proof.", "Checksums detect accidental corruption; they do not authenticate an untrusted backup."],
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    write_checksums(root, V2_FILES)
    validate(root)
    return manifest


def validate(root: Path, allow_legacy: bool = False) -> dict:
    if root.is_symlink():
        raise ValueError("Backup must be a regular directory")
    manifest = json.loads(read_text(root / "manifest.json"))
    version = manifest.get("format_version") if isinstance(manifest, dict) else None
    if type(version) is not int or version not in (1, 2):
        raise ValueError("Unsupported backup format version")
    if version == 1 and not allow_legacy:
        raise ValueError("A legacy backup requires RESTORE_ALLOW_LEGACY=true; only row counts can be verified")
    names = V2_FILES if version == 2 else V1_FILES
    supplied = {}
    for line in read_text(root / "checksums.sha256").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([a-z_.]+)", line)
        if not match or match[2] not in names or match[2] in supplied:
            raise ValueError("Invalid checksum path or duplicate checksum entry")
        supplied[match[2]] = match[1]
    if set(supplied) != set(names):
        raise ValueError("Incomplete checksum coverage")
    for name in names:
        if digest(root / name) != supplied[name]:
            raise ValueError(f"Backup checksum mismatch: {name}")
    count_text = read_text(root / "record_counts.tsv")
    count_names = []
    for line in count_text.splitlines():
        match = re.fullmatch(r"([a-z_][a-z0-9_]*)\t([0-9]+)", line)
        if not match:
            raise ValueError("Invalid record count inventory")
        count_names.append(match[1])
    if not count_names or count_names != sorted(set(count_names)):
        raise ValueError("Invalid or duplicate record count inventory")
    if version == 1:
        for field, name in (("database_dump", "database.dump"), ("record_counts", "record_counts.tsv")):
            if field in manifest and (manifest[field].get("path") != name or manifest[field].get("sha256") != supplied[name]):
                raise ValueError("Invalid legacy manifest file binding")
        return manifest
    rows = normalize(json.loads(read_text(root / "content_inventory.json", 64 * 1024 * 1024)))
    database = next(row for row in rows if row["kind"] == "database")
    asset_stores = {row["name"]: {key: row[key] for key in ("present", "count", "content_bytes")} for row in rows if row["kind"] == "asset_store"}
    if (manifest.get("application") != "market-intelligence" or manifest.get("verification_basis") != "restored_dump"
        or manifest.get("fingerprint_algorithm") != ALGORITHM or manifest.get("database_format") != "postgresql_custom"
        or manifest.get("table_count") != len(count_names) or manifest.get("postgres_major") != database["postgres_major"]
        or manifest.get("alembic_revisions") != database["revisions"] or manifest.get("asset_stores") != asset_stores
        or counts(rows) != count_text):
        raise ValueError("Manifest and content inventory disagree")
    for field, name in (("database_dump", "database.dump"), ("record_counts", "record_counts.tsv"), ("content_inventory", "content_inventory.json")):
        binding = manifest.get(field)
        if not isinstance(binding, dict) or binding.get("path") != name or binding.get("sha256") != supplied[name]:
            raise ValueError("Invalid manifest file binding")
    if manifest["database_dump"].get("size_bytes") != (root / "database.dump").stat().st_size:
        raise ValueError("Invalid database dump size")
    return manifest


def compare(actual: list[dict], expected: list[dict]) -> None:
    if normalize(actual) != normalize(expected):
        raise ValueError("Restored content inventory does not match the backup (tables, bytes, or migration basis)")


def prune(root: Path, retain: int) -> int:
    if retain < 1:
        raise ValueError("Retention must preserve at least one verified backup")
    candidates = []
    for path in sorted(root.iterdir(), reverse=True):
        if path.is_symlink() or not path.is_dir() or not OWNED_FOLDER.fullmatch(path.name):
            continue
        try:
            validate(path)
        except (ValueError, OSError):
            continue
        candidates.append(path)
    for path in candidates[retain:]:
        shutil.rmtree(path)
    return max(0, len(candidates) - retain)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("create", "validate", "compare", "prune"))
    parser.add_argument("value", nargs="?")
    parser.add_argument("--allow-legacy", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    if args.command == "create":
        manifest = create(root, args.value or "")
        print(f'Manifest verifies {manifest["table_count"]} tables and both PDF-store inventories.')
    elif args.command == "validate":
        print(validate(root, args.allow_legacy)["format_version"])
    elif args.command == "compare":
        rows = raw_inventory(root)
        if args.value == "2":
            compare(rows, json.loads(read_text(root / "expected_content_inventory.json", 64 * 1024 * 1024)))
        elif counts(rows) != read_text(root / "expected_counts.tsv"):
            raise ValueError("Restored record counts do not match the legacy backup")
    else:
        print(f"Pruned {prune(root, int(args.value or '0'))} verified local backups")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError):
        # Detailed validation reasons are exercised by tests; operator errors must
        # never echo parsed archive content or private data.
        print("Recovery metadata validation failed. Check format, file integrity and inventory completeness.", file=sys.stderr)
        sys.exit(2)
