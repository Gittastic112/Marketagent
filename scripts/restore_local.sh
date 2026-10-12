#!/usr/bin/env bash
set -euo pipefail
umask 077

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POSTGRES_SERVICE="${POSTGRES_SERVICE:-postgres}"
BACKEND_SERVICE="${BACKEND_SERVICE:-backend}"
FRONTEND_SERVICE="${FRONTEND_SERVICE-frontend}"
DAILY_BRIEF_SERVICE="${DAILY_BRIEF_SERVICE-scheduler}"
SOURCE_REFRESH_SERVICE="${SOURCE_REFRESH_SERVICE-source_scheduler}"
POSTGRES_USER="${POSTGRES_USER:-marketintel}"
POSTGRES_DB="${POSTGRES_DB:-marketintel}"
source "$ROOT_DIR/scripts/recovery_common.sh"

if [[ $# -ne 2 || "$2" != "--yes-replace-database" ]]; then
  printf 'Usage: %s BACKUP_DIR --yes-replace-database\n' "$0" >&2
  printf 'This command destroys and replaces the explicitly configured target database.\n' >&2
  exit 2
fi
if [[ -L "$1" || "$1" == *.partial || "$1" == *.partial/ ]]; then
  printf 'Refusing a linked or incomplete backup directory.\n' >&2
  exit 2
fi
backup_dir="$(cd "$1" && pwd)"
validation_args=(validate)
if [[ "${RESTORE_ALLOW_LEGACY:-false}" == true ]]; then
  validation_args+=(--allow-legacy)
fi
# Validate paths, complete checksum coverage, format and content inventory before
# stopping any service or replacing any data. Only operator-trusted dumps belong here.
format_version="$(recovery_python "$backup_dir" "${validation_args[@]}")"
if [[ "$format_version" != 1 && "$format_version" != 2 && "$format_version" != 3 ]]; then
  printf 'Unknown recovery format.\n' >&2
  exit 2
fi
if [[ "$format_version" == 1 ]]; then
  printf 'Legacy restore: only table counts can be verified, not content or both PDF stores.\n' >&2
fi
"${compose[@]}" exec -T "$POSTGRES_SERVICE" pg_restore --list < "$backup_dir/database.dump" >/dev/null

verification_dir="$(mktemp -d)"
cleanup() { rm -rf "$verification_dir"; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
cp "$backup_dir/record_counts.tsv" "$verification_dir/expected_counts.tsv"
if [[ "$format_version" == 2 || "$format_version" == 3 ]]; then
  cp "$backup_dir/content_inventory.json" "$verification_dir/expected_content_inventory.json"
fi

services_to_stop=("$BACKEND_SERVICE")
if [[ -n "$FRONTEND_SERVICE" ]]; then
  services_to_stop+=("$FRONTEND_SERVICE")
fi
running_services="$("${compose[@]}" ps --services --status running --status restarting)"
workers_to_resume=()
while IFS= read -r service; do
  [[ -z "$service" ]] && continue
  if [[ "$service" == "$DAILY_BRIEF_SERVICE" || "$service" == "$SOURCE_REFRESH_SERVICE" ]]; then
    services_to_stop+=("$service")
    workers_to_resume+=("$service")
  fi
done <<< "$running_services"
"${compose[@]}" stop "${services_to_stop[@]}"
# On any failure or interruption from here onward, writers remain stopped.
"${compose[@]}" exec -T "$POSTGRES_SERVICE" dropdb -U "$POSTGRES_USER" --if-exists --force "$POSTGRES_DB"
"${compose[@]}" exec -T "$POSTGRES_SERVICE" createdb -U "$POSTGRES_USER" "$POSTGRES_DB"
"${compose[@]}" exec -T "$POSTGRES_SERVICE" pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  --no-owner --no-privileges --exit-on-error < "$backup_dir/database.dump"

collect_recovery_inventory > "$verification_dir/inventory.raw.jsonl"
if ! recovery_python "$verification_dir" compare "$format_version"; then
  printf 'Restored records do not match the backup evidence. Writers remain stopped.\n' >&2
  exit 1
fi
"${compose[@]}" run --rm --no-deps "$BACKEND_SERVICE" alembic upgrade head
services_to_start=("$BACKEND_SERVICE")
if [[ -n "$FRONTEND_SERVICE" ]]; then
  services_to_start+=("$FRONTEND_SERVICE")
fi
if [[ ${#workers_to_resume[@]} -gt 0 ]]; then
  services_to_start+=("${workers_to_resume[@]}")
fi
"${compose[@]}" up -d "${services_to_start[@]}"
printf 'Restore verified against checksums and format %s recovery evidence; migration upgrade passed.\n' "$format_version"
