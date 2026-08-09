#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.yml}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-}"
POSTGRES_SERVICE="${POSTGRES_SERVICE:-postgres}"
BACKEND_SERVICE="${BACKEND_SERVICE:-backend}"
FRONTEND_SERVICE="${FRONTEND_SERVICE-frontend}"
POSTGRES_USER="${POSTGRES_USER:-marketintel}"
POSTGRES_DB="${POSTGRES_DB:-marketintel}"

if [[ $# -ne 2 || "$2" != "--yes-replace-database" ]]; then
  printf 'Usage: %s BACKUP_DIR --yes-replace-database\n' "$0" >&2
  printf 'This command destroys and replaces the target PostgreSQL database.\n' >&2
  exit 2
fi

backup_dir="$(cd "$1" && pwd)"
for required in database.dump record_counts.tsv manifest.json checksums.sha256; do
  if [[ ! -f "$backup_dir/$required" ]]; then
    printf 'Backup is incomplete: missing %s\n' "$required" >&2
    exit 2
  fi
done

(
  cd "$backup_dir"
  shasum -a 256 -c checksums.sha256
)

compose=(docker compose)
if [[ -n "$COMPOSE_PROJECT_NAME" ]]; then
  compose+=( -p "$COMPOSE_PROJECT_NAME" )
fi
compose+=( -f "$COMPOSE_FILE" )

"${compose[@]}" exec -T "$POSTGRES_SERVICE" pg_restore --list < "$backup_dir/database.dump" >/dev/null

services_to_stop=("$BACKEND_SERVICE")
if [[ -n "$FRONTEND_SERVICE" ]]; then
  services_to_stop+=("$FRONTEND_SERVICE")
fi
"${compose[@]}" stop "${services_to_stop[@]}"

"${compose[@]}" exec -T "$POSTGRES_SERVICE" dropdb \
  -U "$POSTGRES_USER" \
  --if-exists \
  --force \
  "$POSTGRES_DB"
"${compose[@]}" exec -T "$POSTGRES_SERVICE" createdb \
  -U "$POSTGRES_USER" \
  "$POSTGRES_DB"
"${compose[@]}" exec -T "$POSTGRES_SERVICE" pg_restore \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --no-owner \
  --no-privileges \
  --exit-on-error < "$backup_dir/database.dump"

actual_counts="$(mktemp)"
trap 'rm -f "$actual_counts"' EXIT
while IFS=$'\t' read -r table_name _expected_count; do
  [[ -z "$table_name" ]] && continue
  actual_count="$("${compose[@]}" exec -T "$POSTGRES_SERVICE" psql \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -At \
    -c "SELECT count(*) FROM \"$table_name\";")"
  printf '%s\t%s\n' "$table_name" "$actual_count" >> "$actual_counts"
done < "$backup_dir/record_counts.tsv"

if ! cmp -s "$backup_dir/record_counts.tsv" "$actual_counts"; then
  printf 'Restored record counts do not match the backup manifest.\n' >&2
  diff -u "$backup_dir/record_counts.tsv" "$actual_counts" >&2 || true
  exit 1
fi

"${compose[@]}" run --rm --no-deps "$BACKEND_SERVICE" alembic upgrade head

services_to_start=("$BACKEND_SERVICE")
if [[ -n "$FRONTEND_SERVICE" ]]; then
  services_to_start+=("$FRONTEND_SERVICE")
fi
"${compose[@]}" up -d "${services_to_start[@]}"

printf 'Restore verified against checksums and table counts.\n'
