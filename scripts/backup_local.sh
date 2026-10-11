#!/usr/bin/env bash
set -euo pipefail
umask 077

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_ROOT="${BACKUP_ROOT:-$ROOT_DIR/backups}"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.yml}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-}"
POSTGRES_SERVICE="${POSTGRES_SERVICE:-postgres}"
BACKEND_SERVICE="${BACKEND_SERVICE:-backend}"
POSTGRES_USER="${POSTGRES_USER:-marketintel}"
POSTGRES_DB="${POSTGRES_DB:-marketintel}"
BACKUP_RETENTION_COUNT="${BACKUP_RETENTION_COUNT:-7}"
BACKUP_PRUNE="${BACKUP_PRUNE:-false}"

if [[ ! "$BACKUP_RETENTION_COUNT" =~ ^[0-9]+$ ]]; then
  printf 'BACKUP_RETENTION_COUNT must be a non-negative integer.\n' >&2
  exit 2
fi

compose=(docker compose)
if [[ -n "$COMPOSE_PROJECT_NAME" ]]; then
  compose+=( -p "$COMPOSE_PROJECT_NAME" )
fi
compose+=( -f "$COMPOSE_FILE" )

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_dir="$BACKUP_ROOT/${timestamp}-market-intelligence"
mkdir -p "$backup_dir"
chmod 700 "$backup_dir"

dump_path="$backup_dir/database.dump"
counts_path="$backup_dir/record_counts.tsv"
manifest_path="$backup_dir/manifest.json"

"${compose[@]}" exec -T "$POSTGRES_SERVICE" pg_dump \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --format=custom \
  --compress=6 \
  --no-owner \
  --no-privileges > "$dump_path"

"${compose[@]}" exec -T "$POSTGRES_SERVICE" pg_restore --list < "$dump_path" >/dev/null

table_names="$("${compose[@]}" exec -T "$POSTGRES_SERVICE" psql \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  -At \
  -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;")"

: > "$counts_path"
while IFS= read -r table_name; do
  [[ -z "$table_name" ]] && continue
  # Keep Docker from consuming the remaining table names from this loop's stdin.
  count="$("${compose[@]}" exec -T "$POSTGRES_SERVICE" psql \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -At \
    -c "SELECT count(*) FROM \"$table_name\";" </dev/null)"
  printf '%s\t%s\n' "$table_name" "$count" >> "$counts_path"
done <<< "$table_names"

alembic_revision="$("${compose[@]}" exec -T "$BACKEND_SERVICE" alembic current 2>/dev/null | awk '/\(head\)/ {print $1; exit}')"
asset_summary="$("${compose[@]}" exec -T "$POSTGRES_SERVICE" psql \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  -At \
  -F $'\t' \
  -c "SELECT count(*), COALESCE(sum(octet_length(content)), 0) FROM document_assets;")"
asset_count="${asset_summary%%$'\t'*}"
asset_bytes="${asset_summary##*$'\t'}"

dump_sha="$(shasum -a 256 "$dump_path" | awk '{print $1}')"
counts_sha="$(shasum -a 256 "$counts_path" | awk '{print $1}')"
dump_bytes="$(wc -c < "$dump_path" | tr -d ' ')"

python3 - "$manifest_path" "$timestamp" "$alembic_revision" "$dump_sha" "$dump_bytes" "$counts_sha" "$asset_count" "$asset_bytes" <<'PY'
import json
import sys

(
    manifest_path,
    created_at,
    revision,
    dump_sha,
    dump_bytes,
    counts_sha,
    asset_count,
    asset_bytes,
) = sys.argv[1:]

manifest = {
    "format_version": 1,
    "created_at_utc": created_at,
    "database_format": "postgresql_custom",
    "alembic_revision": revision or None,
    "database_dump": {
        "path": "database.dump",
        "sha256": dump_sha,
        "size_bytes": int(dump_bytes),
    },
    "record_counts": {
        "path": "record_counts.tsv",
        "sha256": counts_sha,
    },
    "document_assets": {
        "storage": "postgresql_bytea",
        "count": int(asset_count),
        "content_bytes": int(asset_bytes),
        "included_in_database_dump": True,
    },
    "limitations": [
        "Secrets and local environment files are intentionally excluded.",
        "Provider data that was never persisted cannot be reconstructed from this archive.",
    ],
}
with open(manifest_path, "w", encoding="utf-8") as handle:
    json.dump(manifest, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY

(
  cd "$backup_dir"
  shasum -a 256 database.dump record_counts.tsv manifest.json > checksums.sha256
  shasum -a 256 -c checksums.sha256 >/dev/null
)

if [[ "$BACKUP_PRUNE" == "true" ]]; then
  python3 - "$BACKUP_ROOT" "$BACKUP_RETENTION_COUNT" <<'PY'
from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1]).resolve()
retain = int(sys.argv[2])
candidates = sorted(
    (
        item
        for item in root.glob("*-market-intelligence")
        if item.is_dir() and (item / "manifest.json").is_file()
    ),
    reverse=True,
)
for stale in candidates[retain:]:
    if stale.parent != root:
        raise RuntimeError(f"Refusing to prune outside backup root: {stale}")
    shutil.rmtree(stale)
PY
fi

printf 'Backup verified.\nBACKUP_DIR=%s\n' "$backup_dir"
